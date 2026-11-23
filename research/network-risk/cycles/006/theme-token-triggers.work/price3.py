# Prices for Robinhood Chain, Elysium and Arc, which cycle 5 left without a price file. Tokens with any Transfer log
# touching the PoolManager in the cycle 4 window are priced at coins.llama.fi; GeckoTerminal top pools add the rest.
import sys, json, gzip, os, time, requests
from concurrent.futures import ThreadPoolExecutor
from base import *
LL = {4663: 'robinhood', 99901: 'elysium', 5042: 'arc', 999: 'hyperliquid', 7777777: 'zora'}
GT = {4663: 'robinhood', 99901: 'elysium', 5042: 'arc', 999: 'hyperevm', 7777777: 'zora-network'}
S = requests.Session(); S.headers['user-agent'] = 'curl/8'
def llama(cid, toks):
    out = {}
    def job(i):
        ch = toks[i:i + 60]
        for k in range(5):
            try:
                j = S.get('https://coins.llama.fi/prices/current/' + ','.join(LL[cid] + ':' + t for t in ch), timeout=40).json()['coins']
                return {k.split(':')[1].lower(): v for k, v in j.items()}
            except Exception as e: time.sleep(1 + k)
        return {}
    with ThreadPoolExecutor(6) as ex:
        for res in ex.map(job, range(0, len(toks), 60)): out.update(res)
    return out
def gecko(cid, pages=10):
    out = {}
    for dex in ('uniswap-v4-' + GT[cid], 'uniswap_v4_' + GT[cid], None):
        for pg in range(1, pages + 1):
            u = 'https://api.geckoterminal.com/api/v2/networks/%s/%spools?page=%d&include=base_token,quote_token' % (GT[cid], ('dexes/%s/' % dex) if dex else '', pg)
            try:
                r = S.get(u, timeout=30); j = r.json()
            except Exception as e: print('gt err', u, e); break
            if 'data' not in j: print('gt none', u, str(j)[:100]); break
            for x in j.get('included') or []:
                a = x['attributes']
                if a.get('address'): out[a['address'].lower()] = dict(symbol=a.get('symbol'), decimals=a.get('decimals'))
            for p in j['data']:
                a = p['attributes']
                for side in ('base', 'quote'):
                    tid = p['relationships'][side + '_token']['data']['id'].split('_')[-1].lower()
                    pr = a.get(side + '_token_price_usd')
                    if pr and tid in out: out[tid]['price'] = float(pr); out[tid].setdefault('pools', []).append((a.get('name'), a.get('reserve_in_usd'), p['relationships']['dex']['data']['id']))
            if len(j['data']) < 20: break
            time.sleep(2.2)
    return out
for cid in [int(c) for c in sys.argv[1:]]:
    d, rows = universe(cid)
    act = [r['token'] for r in rows if int(r.get('bal2') or 0) > 0 and (r.get('nlogs') or 0) > 0]
    print(cid, 'nonzero', sum(1 for r in rows if int(r.get('bal2') or 0) > 0), 'active', len(act), flush=True)
    pl = llama(cid, act[:30000])
    g = gecko(cid)
    extra = [t for t in g if t not in pl]
    pl2 = llama(cid, extra) if extra else {}
    json.dump(dict(llama={**pl, **pl2}, gecko=g, active=len(act)), gzip.open(os.path.join(RAW6, 'prices3_%d.json.gz' % cid), 'wt'))
    print(cid, 'llama priced', len(pl) + len(pl2), 'gecko tokens', len(g), flush=True)
