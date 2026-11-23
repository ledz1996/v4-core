# coins.llama.fi price for every currency with a balance on a network (all rows, active or not).
import sys, json, gzip, os, time, requests
from concurrent.futures import ThreadPoolExecutor
from base import *
LL = {4663: 'robinhood', 99901: 'elysium', 5042: 'arc', 999: 'hyperliquid', 7777777: 'zora'}
S = requests.Session(); S.headers['user-agent'] = 'curl/8'
cid = int(sys.argv[1])
d, rows = universe(cid)
toks = [r['token'] for r in rows if int(r.get('bal2') or 0) > 0]
out = {}; fails = 0
def job(i):
    ch = toks[i:i + 80]
    for k in range(6):
        try:
            j = S.get('https://coins.llama.fi/prices/current/' + ','.join(LL[cid] + ':' + t for t in ch), timeout=40).json()['coins']
            return {k.split(':')[1].lower(): v for k, v in j.items()}
        except Exception as e: time.sleep(1 + 2 * k)
    return None
with ThreadPoolExecutor(8) as ex:
    for n, res in enumerate(ex.map(job, range(0, len(toks), 80))):
        if res is None: fails += 1
        else: out.update(res)
        if n % 500 == 0: print(cid, n * 80, len(toks), len(out), 'fails', fails, flush=True)
json.dump(dict(prices=out, asked=len(toks), failedChunks=fails), gzip.open(os.path.join(RAW6, 'pricesall_%d.json.gz' % cid), 'wt'))
print(cid, 'done asked', len(toks), 'priced', len(out), 'failed chunks', fails, flush=True)
