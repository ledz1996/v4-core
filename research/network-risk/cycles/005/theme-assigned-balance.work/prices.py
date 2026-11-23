# USD prices from coins.llama.fi for every pooled currency with a balance (public price API, no keys).
import sys, json, gzip, os, time, requests
from concurrent.futures import ThreadPoolExecutor
from common import universe, RAW
LL = {1: 'ethereum', 10: 'optimism', 8453: 'base', 130: 'unichain', 7777777: 'zora', 480: 'wc', 57073: 'ink', 1868: 'soneium', 42220: 'celo', 196: 'xlayer',
      42161: 'arbitrum', 137: 'polygon', 56: 'bsc', 43114: 'avax', 143: 'monad', 4326: 'megaeth', 999: 'hyperliquid', 4217: 'tempo', 5042: 'arc', 4663: 'robinhood', 99901: 'elysium'}
S = requests.Session()
def run(cid, only=None):
    d, rows = universe(cid)
    toks = [r['token'] for r in rows if int(r.get('bal2') or 0) > 0]
    if only is not None: toks = [t for t in toks if t in only]
    out = {}
    def job(i):
        ch = toks[i:i + 60]
        for k in range(5):
            try:
                r = S.get('https://coins.llama.fi/prices/current/' + ','.join(LL[cid] + ':' + t for t in ch), timeout=40)
                j = r.json()['coins']
                return {k.split(':')[1].lower(): v for k, v in j.items()}
            except Exception as e:
                time.sleep(1 + k)
        return {}
    with ThreadPoolExecutor(6) as ex:
        for res in ex.map(job, range(0, len(toks), 60)): out.update(res)
    json.dump(out, gzip.open(os.path.join(RAW, 'prices_%d.json.gz' % cid), 'wt'))
    print(cid, 'tokens', len(toks), 'priced', len(out), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
