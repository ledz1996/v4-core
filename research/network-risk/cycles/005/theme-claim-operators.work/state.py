# For every operator and spender seen in the logs: code at the address, and whether the approval is still set (isOperator / allowance at latest).
import sys, json, os, time, hashlib, concurrent.futures as cf
from lib import *
from summarize import load
from config import CFG
ALT = {1: 'https://ethereum-rpc.publicnode.com', 8453: 'https://base-rpc.publicnode.com', 56: 'https://bsc-rpc.publicnode.com', 137: 'https://polygon-bor-rpc.publicnode.com', 999: 'https://rpc.hyperliquid.xyz/evm'}
def url(cid): return ALT.get(cid) or net(cid)['rpc']
def chunks(l, n):
    for i in range(0, len(l), n): yield l[i:i + n]
def bcall(u, calls, n=20):
    out = []
    for c in chunks(calls, n):
        try: r = batch(u, c)
        except Exception:
            r = []
            for m, p in c:
                try: r.append(rpc(u, m, p))
                except Exception as e: r.append({'error': str(e)[:100]})
        for k, v in enumerate(r):
            if isinstance(v, dict) or v is None:
                for a in range(4):
                    try: r[k] = rpc(u, c[k][0], c[k][1]); break
                    except Exception as e: r[k] = {'error': str(e)[:100]}; time.sleep(1 + a)
        out.extend(r)
    return out
def run(cid):
    o, ops, sp = load(cid); u = url(cid); pm = net(cid)['poolManager']
    xs = sorted(set(ops) | set(sp))
    codes = bcall(u, [('eth_getCode', [x, 'latest']) for x in xs])
    info = {}
    for x, c in zip(xs, codes):
        if isinstance(c, dict): info[x] = dict(err=str(c)[:80]); continue
        b = bytes.fromhex(c[2:])
        d = dict(len=len(b), h=hashlib.sha256(b).hexdigest()[:16])
        if len(b) == 23 and b[:3] == bytes.fromhex('ef0100'): d['delegate'] = '0x' + b[3:].hex()
        info[x] = d
    dels = sorted({d['delegate'] for d in info.values() if d.get('delegate')})
    dc = bcall(u, [('eth_getCode', [x, 'latest']) for x in dels])
    dinfo = {x: dict(len=len(bytes.fromhex(c[2:])), h=hashlib.sha256(bytes.fromhex(c[2:])).hexdigest()[:16]) for x, c in zip(dels, dc) if not isinstance(c, dict)}
    pairs = [(ow, x) for x, m in ops.items() for ow in m]
    r = bcall(u, [('eth_call', [{'to': pm, 'data': '0xb6363cf2' + adr(ow) + adr(x)}, 'latest']) for ow, x in pairs])
    live_op = [[ow, x, (int(v, 16) if isinstance(v, str) and len(v) > 2 else None)] for (ow, x), v in zip(pairs, r)]
    trip = [(ow, x, i) for x, m in sp.items() for ow, mm in m.items() for i in mm]
    r = bcall(u, [('eth_call', [{'to': pm, 'data': '0x598af9e7' + adr(ow) + adr(x) + u256(i)}, 'latest']) for ow, x, i in trip])
    live_al = [[ow, x, hex(i), (int(v, 16) if isinstance(v, str) and len(v) > 2 else None)] for (ow, x, i), v in zip(trip, r)]
    # owner code too (contract owners are vaults or hooks; accounts are users)
    owners = sorted({p[0] for p in pairs} | {t[0] for t in trip})
    oc = bcall(u, [('eth_getCode', [x, 'latest']) for x in owners])
    oinfo = {x: (len(c) // 2 - 1 if isinstance(c, str) else None) for x, c in zip(owners, oc)}
    json.dump(dict(chainId=cid, url=u, info=info, dinfo=dinfo, liveOp=live_op, liveAl=live_al, ownerCodeLen=oinfo), open(os.path.join(HERE, 'raw', 'state_%d.json' % cid), 'w'))
    return cid, len(xs), 'eoa', sum(1 for d in info.values() if d.get('len') == 0), '7702', len(dels), 'contracts', sum(1 for d in info.values() if d.get('len', 0) > 0 and not d.get('delegate')), 'liveOp', sum(1 for p in live_op if p[2]), '/', len(live_op), 'liveAl', sum(1 for p in live_al if p[3]), '/', len(live_al), 'errs', sum(1 for p in live_op if p[2] is None)
if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]]
    with cf.ThreadPoolExecutor(len(ids)) as ex:
        for r in ex.map(run, ids): print(r, flush=True)
