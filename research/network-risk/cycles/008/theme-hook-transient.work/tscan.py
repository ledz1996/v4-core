# For the top hooks of each network: eth_getCode, linear disassembly, count TSTORE (0x5d) and TLOAD (0x5c) outside PUSH data,
# list the constants pushed shortly before each, note DELEGATECALL and minimal proxy targets. Read-only.
from common import *
import hashlib, concurrent.futures as cf
def dis(code):
    i = 0; ops = []
    n = len(code)
    while i < n:
        op = code[i]
        if 0x60 <= op <= 0x7f:
            k = op - 0x5f; ops.append((i, op, code[i + 1:i + 1 + k])); i += 1 + k
        else: ops.append((i, op, None)); i += 1
    return ops
def strip_meta(code):
    # solc CBOR metadata: last two bytes give its length
    if len(code) > 2:
        l = int.from_bytes(code[-2:], 'big')
        if 0 < l < 200 and l + 2 <= len(code) and code[-2 - l] in (0xa1, 0xa2, 0xa3, 0xa4): return code[:-2 - l]
    return code
def analyse(code):
    body = strip_meta(code); ops = dis(body)
    ts = [k for k, o in enumerate(ops) if o[1] == 0x5d]; tl = [k for k, o in enumerate(ops) if o[1] == 0x5c]
    def consts(k):
        out = []
        for j in range(max(0, k - 6), k):
            if ops[j][2] is not None and len(ops[j][2]) >= 4: out.append(ops[j][2].hex())
        return out
    return dict(size=len(code), tstore=len(ts), tload=len(tl), delegatecall=sum(1 for o in ops if o[1] == 0xf4),
                tstoreConsts=sorted({c for k in ts for c in consts(k)}), tloadConsts=sorted({c for k in tl for c in consts(k)}),
                tstorePcs=[ops[k][0] for k in ts][:40], sha=hashlib.sha256(code).hexdigest()[:16])
def getcode(cid, a):
    last = None
    for u in urls(cid):
        try: return bytes.fromhex(rpc(u, 'eth_getCode', [a, 'latest'])[2:])
        except Exception as e: last = e
    raise last
def proxy_target(cid, a, code):
    h = code.hex()
    if h.startswith('363d3d373d3d3d363d73') and len(code) <= 60: return '0x' + h[20:60]
    if len(code) < 400:
        # ERC-1967 implementation slot
        for u in urls(cid):
            try:
                v = rpc(u, 'eth_getStorageAt', [a, '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', 'latest'])
                if int(v, 16): return '0x' + v[-40:]
                break
            except Exception: pass
        import re
        m = re.findall('73([0-9a-f]{40})', h)
        if m: return '0x' + m[0]
    return None
def one(job):
    cid, a, cnt = job
    try:
        code = getcode(cid, a)
        os.makedirs(os.path.join(RAW, 'code'), exist_ok=True)
        open(os.path.join(RAW, 'code', '%d_%s.hex' % (cid, a)), 'w').write(code.hex())
        r = analyse(code); r.update(chainId=cid, hook=a, pools=cnt)
        t = proxy_target(cid, a, code)
        if t:
            ic = getcode(cid, t); open(os.path.join(RAW, 'code', '%d_%s.hex' % (cid, t)), 'w').write(ic.hex())
            r['impl'] = t; r['implScan'] = analyse(ic)
        return r
    except Exception as e: return dict(chainId=cid, hook=a, pools=cnt, error=repr(e)[:200])
if __name__ == '__main__':
    top = json.load(open(os.path.join(RAW, 'top10.json')))
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    jobs = [(int(c), h, n) for c, v in top.items() for h, n in v['top'][:N]]
    with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    json.dump(res, open(os.path.join(RAW, 'tscan.json'), 'w'), indent=0)
    from summ import flags
    for r in res:
        if 'error' in r: print(r['chainId'], r['hook'], 'ERR', r['error']); continue
        s = r.get('implScan') or r
        print('%-8d %s pools %-8d sz %-6d %s TSTORE %-3d TLOAD %-3d DC %-2d %s %s' % (r['chainId'], r['hook'], r['pools'], r['size'], r['sha'], s['tstore'], s['tload'], s['delegatecall'], ('impl ' + r['impl']) if r.get('impl') else '', ','.join(flags(r['hook']))))
