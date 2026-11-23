# Does unlockCallback of an approved contract look at its caller? Read-only comparison: the same calldata is sent once with from = PoolManager
# and once with from = an unrelated account. Equal answers for every payload mean no caller check was reached before the call failed.
import sys, json, os, concurrent.futures as cf
from lib import *
from abi2 import calldata
from state import url
ATT = '0x00000000000000000000000000000000a77ac4e5'
PAY = [b'', bytes(32 * 4), bytes(32 * 20), (32).to_bytes(32, 'big') + bytes(32 * 19), bytes([0] * 31 + [1]) + bytes(32 * 19)]
def one(u, pm, x):
    res = []
    for p in PAY:
        d = calldata('unlockCallback(bytes)', [p]); r = []
        for frm in (pm, ATT):
            try: r.append('ok:' + rpc(u, 'eth_call', [{'from': frm, 'to': x, 'data': d}, 'latest'], tries=3)[:40])
            except Exception as e:
                s = str(e); i = s.find('"data"'); r.append('rev:' + (s[i:i + 60] if i >= 0 else s[:60]))
        res.append(r)
    return res
def run(cid):
    st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid))); u = url(cid); pm = net(cid)['poolManager']
    live = {p[1] for p in st['liveOp'] if p[2]} | {p[1] for p in st['liveAl'] if p[3]}
    xs = [x for x in live if st['info'].get(x, {}).get('len', 0) > 0 and x != pm.lower()]
    out = {}
    def f(x):
        tgt = st['info'][x].get('delegate') or x
        try: code = rpc(u, 'eth_getCode', [tgt, 'latest'])
        except Exception as e: return x, dict(err=str(e)[:80])
        if '91dd7346' not in code: return x, dict(hasCallback=False, len=len(code) // 2 - 1)
        r = one(u, pm, x)
        same = all(a == b for a, b in r)
        return x, dict(hasCallback=True, len=len(code) // 2 - 1, sameForBothCallers=same, sample=r[1])
    with cf.ThreadPoolExecutor(6) as ex:
        for x, v in ex.map(f, xs): out[x] = v
    json.dump(out, open(os.path.join(HERE, 'raw', 'guard_%d.json' % cid), 'w'))
    cb = [x for x, v in out.items() if v.get('hasCallback')]
    return cid, 'live approved contracts', len(xs), 'with unlockCallback', len(cb), 'same answer for both callers', [(x, out[x]['sample']) for x in cb if out[x]['sameForBothCallers']]
if __name__ == '__main__':
    for c in sys.argv[1:]: print(run(int(c)), flush=True)
