# Price what the hooks hold and rank hooks per network. Prices: DexScreener token endpoint (pair with the most liquidity where the
# token is the base token). A token position is capped at half the liquidity of that pair. Read-only.
# usage: python3 value.py <chainId>
import sys, collections, time, requests
from common import *
SLUG = {1:'ethereum',10:'optimism',8453:'base',130:'unichain',7777777:'zora',480:'worldchain',57073:'ink',1868:'soneium',42220:'celo',196:'xlayer',42161:'arbitrum',4663:'robinhood',99901:'elysium',137:'polygon',56:'bsc',43114:'avalanche',143:'monad',4326:'megaeth',4217:'tempo',5042:'arc',999:'hyperevm'}
WN = {1:'0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',10:'0x4200000000000000000000000000000000000006',8453:'0x4200000000000000000000000000000000000006',130:'0x4200000000000000000000000000000000000006',7777777:'0x4200000000000000000000000000000000000006',480:'0x4200000000000000000000000000000000000006',57073:'0x4200000000000000000000000000000000000006',1868:'0x4200000000000000000000000000000000000006',42220:'0x471ece3750da237f93b8e339c536989b8978a438',196:'0xe538905cf8410324e03a5a23c1c177a474d59b2b',42161:'0x82af49447d8a07e3bd95bd0d56f35241523fbab1',137:'0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270',56:'0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',43114:'0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7',143:'0x3bd359c1119da7da1d913d1c4d2b7c461115433a',4326:'0x4200000000000000000000000000000000000006',999:'0x5555555555555555555555555555555555555555'}
Z = '0x' + '0' * 40
def ds(slug, addrs):
    out = {}
    for i in range(0, len(addrs), 30):
        for t in range(4):
            try:
                r = requests.get('https://api.dexscreener.com/tokens/v1/%s/%s' % (slug, ','.join(addrs[i:i + 30])), timeout=30, headers={'user-agent': 'curl/8'})
                if r.status_code == 429: time.sleep(5); continue
                j = r.json() if r.status_code == 200 else []
                break
            except Exception as e: j = []; time.sleep(1)
        for p in j if isinstance(j, list) else []:
            try:
                a = p['baseToken']['address'].lower(); liq = float((p.get('liquidity') or {}).get('usd') or 0); px = float(p.get('priceUsd') or 0)
            except Exception: continue
            if a not in out or liq > out[a][1]: out[a] = (px, liq, p['baseToken'].get('symbol'))
        time.sleep(0.25)
    return out
def main(cid, nativePx):
    j = json.load(gzip.open(os.path.join(RAW, 'rank_%d.json.gz' % cid)))
    rows = [(k, h, c, int(v)) for k, h, c, v in j['rows']]
    curs = sorted(set(c for _, _, c, _ in rows if c != Z))
    u = urls(cid)[0]; meta = {}
    for i in range(0, len(curs), 400):
        ch = curs[i:i + 400]
        for uu in urls(cid):
            try:
                r = mc3(uu, [(c, '313ce567') for c in ch] + [(c, '95d89b41') for c in ch]); break
            except Exception as e: r = None
        if r is None: continue
        for k, c in enumerate(ch):
            ok, b = r[k]; dec = int(b[:64], 16) if ok and len(b) >= 64 and int(b[:64], 16) < 78 else None
            ok2, b2 = r[len(ch) + k]; sym = ''
            try:
                if ok2 and len(b2) >= 128: l = int(b2[64:128], 16); sym = bytes.fromhex(b2[128:128 + 2 * l]).decode('utf8', 'replace')
                elif ok2 and len(b2) == 64: sym = bytes.fromhex(b2).rstrip(b'\0').decode('utf8', 'replace')
            except Exception: pass
            meta[c] = (dec, sym[:16])
    px = ds(SLUG[cid], curs) if SLUG.get(cid) else {}
    n = net(cid)
    def val(c, v):
        if c == Z: return v / 10 ** n['nativeDecimals'] * nativePx, 'native'
        dec = (meta.get(c) or (None, ''))[0]
        if c in px and dec is not None:
            p, liq, _ = px[c]; x = v / 10 ** dec * p
            return min(x, liq / 2), 'ds'
        return 0.0, 'unpriced'
    per = collections.defaultdict(lambda: dict(usd=0.0, claimsUsd=0.0, items=[]))
    for k, h, c, v in rows:
        x, how = val(c, v); d = per[h]; d['usd'] += x
        if k == 'claim': d['claimsUsd'] += x
        d['items'].append((x, k, c, (meta.get(c) or (None, ''))[1] if c != Z else n['nativeSymbol'], (meta.get(c) or (18,))[0] if c != Z else n['nativeDecimals'], str(v), how))
    rank = sorted(per.items(), key=lambda kv: -kv[1]['usd'])
    out = dict(chainId=cid, block=j['block'], nativePx=nativePx, priced=len(px), currencies=len(curs), hooksWithHoldings=len(per),
               rank=[dict(hook=h, usd=round(d['usd'], 2), claimsUsd=round(d['claimsUsd'], 2), n=len(d['items']), items=sorted(d['items'], key=lambda t: -t[0])[:12]) for h, d in rank])
    json.dump(out, open(os.path.join(RAW, 'value_%d.json' % cid), 'w'))
    print(cid, n['name'], 'block', j['block'], 'hooks with holdings', len(per), 'currencies', len(curs), 'priced', len(px), 'nativePx', nativePx)
    for r in out['rank'][:25]:
        print('  %s usd %10.2f claims %10.2f  %s' % (r['hook'], r['usd'], r['claimsUsd'], '; '.join('%s %s %.4g%s' % (k, s or c[:8], int(v) / 10 ** (dec if dec is not None else 18), '' if how != 'unpriced' else '?') for x, k, c, s, dec, v, how in r['items'][:5])))
if __name__ == '__main__':
    main(int(sys.argv[1]), float(sys.argv[2]))
