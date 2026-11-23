# Pair addresses of priced currencies from the public DexScreener token endpoint (no key). Only 20 byte pair addresses are kept
# (v2 and v3 style pools); v4 pool ids are 32 bytes and are not recipients.
import sys, json, os, time, requests, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
SLUG = {1: 'ethereum', 10: 'optimism', 8453: 'base', 130: 'unichain', 7777777: 'zora', 480: 'worldchain', 57073: 'ink', 1868: 'soneium', 42220: 'celo', 196: 'xlayer', 42161: 'arbitrum', 137: 'polygon', 56: 'bsc',
        43114: 'avalanche', 143: 'monad', 4326: 'megaeth', 999: 'hyperevm', 4217: 'tempo', 5042: 'arc', 4663: 'robinhood', 99901: 'elysium'}
S = requests.Session(); S.headers['user-agent'] = 'curl/8'
def run(cid, minusd=50.0):
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    toks = [t for t, L in live.items() if L['usd'] > minusd]
    out = {}; seen = collections.Counter(); fail = [0]
    def job(t):
        for k in range(5):
            try:
                r = S.get('https://api.dexscreener.com/latest/dex/tokens/' + t, timeout=30)
                if r.status_code == 429: time.sleep(5 + 5 * k); continue
                ps = r.json().get('pairs') or []
                rows = []
                for p in ps:
                    seen[p['chainId']] += 1
                    if p['chainId'] == SLUG[cid] and len(p['pairAddress']) == 42: rows.append([p['pairAddress'].lower(), p['dexId'], ','.join(p.get('labels') or []), (p.get('liquidity') or {}).get('usd')])
                return t, rows
            except Exception as e: time.sleep(1 + k)
        fail[0] += 1
        return t, None
    with ThreadPoolExecutor(3) as ex:
        for t, rows in ex.map(job, toks):
            if rows: out[t] = rows
    wz(os.path.join(RAW7, 'dexs_%d.json.gz' % cid), out)
    print(cid, net(cid)['name'], 'asked', len(toks), 'failed', fail[0], 'tokens with a 20 byte pair', len(out), 'pairs', sum(len(v) for v in out.values()), 'chains seen', seen.most_common(4), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
