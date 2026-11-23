# Bytecode triage of every address that still holds an operator right or an allowance: code (through EIP-7702, EIP-1167 and EIP-1967 indirections),
# PUSH4 constants that name the PoolManager functions which move claims, and the dispatcher selectors.
import sys, json, os, hashlib, concurrent.futures as cf
from lib import *
from state import url, bcall
from sels import selectors
IMPL = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'; BEACON = '0xa3f0ad74e5423aebfd80e3ef4346578335a9a72aeaee59ff6cb3582b35133d50'
FLAGS = dict(transferFrom='fe99049a', burn='f5298aca', transfer6909='095bcdb6', mint='156e29f6', take='0b0d9c09', unlock='48c89491', unlockCallback='91dd7346', settle='11da60b4', setOperator='558a7297', approve6909='426a8493')
def push4(code):
    b = bytes.fromhex(code[2:]); out = set(); i = 0
    while i < len(b):
        op = b[i]
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f; v = b[i + 1:i + 1 + n]
            if n == 4: out.add(v.hex())
            elif n > 4 and len(v) == n and v[4:] == bytes(n - 4): out.add(v[:4].hex())   # left aligned selector constant
            # the optimizer writes a constant with trailing zero bits as a shorter constant and a shift (0x08c379a0 is PUSH3 461bcd PUSH1 e5 SHL)
            if n <= 4 and i + 1 + n + 2 < len(b) and b[i + 1 + n] == 0x60 and b[i + 1 + n + 2] == 0x1b and 0xe0 <= b[i + 1 + n + 1] <= 0xff:
                out.add(((int.from_bytes(v, 'big') << (b[i + 1 + n + 1] - 0xe0)) & 0xffffffff).to_bytes(4, 'big').hex())
            i += 1 + n
        else: i += 1
    return out
def run(cid):
    st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid))); u = url(cid); pm = net(cid)['poolManager'].lower()
    live = sorted({p[1] for p in st['liveOp'] if p[2]} | {p[1] for p in st['liveAl'] if p[3]})
    xs = [x for x in live if st['info'].get(x, {}).get('len', 0) > 0]
    codes = dict(zip(xs, bcall(u, [('eth_getCode', [x, 'latest']) for x in xs])))
    out = {}
    tgt = {}
    for x in xs:
        c = codes[x]
        if not isinstance(c, str): out[x] = dict(err='code'); continue
        b = bytes.fromhex(c[2:]); via = None; t = None
        if len(b) == 23 and b[:3] == bytes.fromhex('ef0100'): via = '7702'; t = '0x' + b[3:].hex()
        elif len(b) == 45 and b[:10] == bytes.fromhex('363d3d373d3d3d363d73'): via = '1167'; t = '0x' + b[10:30].hex()
        elif len(b) < 400:
            # short code: look for an embedded address used with DELEGATECALL, else the EIP-1967 slots
            try:
                s = rpc(u, 'eth_getStorageAt', [x, IMPL, 'latest'])
                if int(s, 16): via = '1967'; t = '0x' + s[-40:]
                else:
                    s = rpc(u, 'eth_getStorageAt', [x, BEACON, 'latest'])
                    if int(s, 16):
                        r = rpc(u, 'eth_call', [{'to': '0x' + s[-40:], 'data': '0x5c60da1b'}, 'latest']); via = 'beacon'; t = '0x' + r[-40:]
            except Exception as e: pass
            if not t and 0xf4 in b:
                i = 0
                while i < len(b):
                    op = b[i]
                    if op == 0x73: t = '0x' + b[i + 1:i + 21].hex(); via = 'embedded'; break
                    i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
        else:
            try:
                s = rpc(u, 'eth_getStorageAt', [x, IMPL, 'latest'])
                if int(s, 16): via = '1967'; t = '0x' + s[-40:]
            except Exception: pass
        tgt[x] = (via, t)
    ts = sorted({t for v, t in tgt.values() if t})
    tcodes = dict(zip(ts, bcall(u, [('eth_getCode', [t, 'latest']) for t in ts])))
    for x in xs:
        if x in out: continue
        via, t = tgt[x]; c = tcodes.get(t) if t else codes[x]
        if not isinstance(c, str): c = codes[x]
        own = codes[x]
        p = push4(c) | push4(own)
        d = dict(len=len(own) // 2 - 1, via=via, target=t, tlen=(len(c) // 2 - 1), h=hashlib.sha256(bytes.fromhex(c[2:])).hexdigest()[:16],
                 flags=[k for k, v in FLAGS.items() if v in p], pmInCode=pm[2:] in c.lower() or pm[2:] in own.lower(), sels=selectors(c),
                 delegatecall=(0xf4 in bytes.fromhex(c[2:])), isPM=(x == pm))
        out[x] = d
    json.dump(out, open(os.path.join(HERE, 'raw', 'triage_%d.json' % cid), 'w'))
    n = len(out); mv = sum(1 for d in out.values() if 'transferFrom' in d.get('flags', []) or 'burn' in d.get('flags', []))
    return cid, 'live approved contracts', n, 'with transferFrom or burn constant', mv, 'via', {k: sum(1 for d in out.values() if d.get('via') == k) for k in ('7702', '1167', '1967', 'beacon', 'embedded')}
if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]]
    with cf.ThreadPoolExecutor(len(ids)) as ex:
        for r in ex.map(run, ids): print(r, flush=True)
