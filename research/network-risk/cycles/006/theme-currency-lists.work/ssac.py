# L-391: every transaction that holds an sSAC rebase log, classified with rule.classify. A payout is a row of class surplus:
# settle credited a rise of balanceOf(PoolManager) since sync that no Transfer log carries, and take or mint paid it out.
import json, gzip, collections, sys
from concurrent.futures import ThreadPoolExecutor
import rule
SSAC = '0x0ae7cd10f94fd16a6f9a29a372708718144c46f8'
d = json.load(gzip.open('raw/logs_56_ssac_rebase.json.gz')); txs = sorted({(r[0], r[1]) for r in d['rows']})
ep = {r[1]: int(r[2][1], 16) for r in d['rows']}
print('rebase logs', len(d['rows']), 'transactions', len(txs), 'blocks', txs[0][0], txs[-1][0], 'fail', len(d['fail']), flush=True)
def one(x):
    for k in range(3):
        try:
            r = rule.classify(56, x[1], SSAC)
            if r['cls'] not in ('unread', 'error') and r.get('trace') is not None: break
        except Exception as e: r = dict(tx=x[1], token=SSAC, cls='error', why=repr(e)[:150])
    r['epoch'] = ep.get(x[1]); r['block'] = x[0]; return r
with ThreadPoolExecutor(3) as ex: res = list(ex.map(one, txs))
json.dump(dict(rows=res, lo=d['lo'], hi=d['hi']), gzip.open('raw/ssac_payouts.json.gz', 'wt'))
c = collections.Counter(r['cls'] for r in res); print(dict(c))
pay = [r for r in res if r['cls'].startswith('surplus')]
print('payouts', len(pay), 'sum', sum(sum(r['trace']['paid']) - int(r['in']) for r in pay), 'first', pay[0]['block'] if pay else None, 'last', pay[-1]['block'] if pay else None)
print(collections.Counter((r['sender'], r['txTo']) for r in pay).most_common(8))
