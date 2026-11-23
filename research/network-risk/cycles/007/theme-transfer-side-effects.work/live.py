# Live balanceOf(PoolManager) for every priced currency, and its USD value. Batches of eth_call on two endpoints.
import sys, json, os
from concurrent.futures import ThreadPoolExecutor
from base import *
def run(cid):
    pm = net(cid)['poolManager'].lower(); pr = prices(cid); toks = sorted(pr)
    us = urls2(cid)
    out = {}
    def job(i):
        ch = toks[i:i + 80]
        calls = [('eth_call', [{'to': t, 'data': sel('balanceOf(address)') + adr(pm)}, 'latest']) for t in ch]
        for k in range(6):
            try:
                res = batch(us[(i // 80 + k) % len(us)], calls, timeout=60, tries=1)
                if sum(1 for r in res if r is None or (isinstance(r, dict) and 'limit' in json.dumps(r).lower())) > 0: raise Exception('partial')
                return {t: (int(r[2:66], 16) if isinstance(r, str) and len(r) >= 66 else None) for t, r in zip(ch, res)}
            except Exception as e: time.sleep(0.5 * (k + 1))
        o = {}
        for t in ch:
            r = ecall(cid, t, sel('balanceOf(address)') + adr(pm))
            o[t] = int(r[2:66], 16) if isinstance(r, str) and len(r) >= 66 else None
        return o
    with ThreadPoolExecutor(5) as ex:
        for o in ex.map(job, range(0, len(toks), 80)): out.update(o)
    bn = int(rpc(us[0], 'eth_blockNumber', []), 16)
    rows = {t: dict(sym=pr[t].get('symbol'), dec=int(pr[t]['decimals']), price=float(pr[t]['price']), bal=str(out[t]) if out[t] is not None else None, usd=usdv(out[t] or 0, pr[t])) for t in toks}
    wz(os.path.join(RAW7, 'live_%d.json.gz' % cid), dict(chainId=cid, block=bn, rows=rows))
    v = [r['usd'] for r in rows.values()]
    print(cid, net(cid)['name'], 'block', bn, 'priced', len(rows), 'nobal', sum(1 for r in rows.values() if r['bal'] is None), 'bal>0', sum(1 for r in rows.values() if int(r['bal'] or 0) > 0),
          '>1000', sum(1 for x in v if x > 1000), '>100', sum(1 for x in v if x > 100), '>10', sum(1 for x in v if x > 10), '>1', sum(1 for x in v if x > 1), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
