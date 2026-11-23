# Verified source for a contract: Sourcify first, then the network's Blockscout instance. Saved under raw/src/<chain>_<address>.json
import sys, json, os, time, requests
from base import *
SCOUT = {1: 'https://eth.blockscout.com', 8453: 'https://base.blockscout.com', 42161: 'https://arbitrum.blockscout.com', 137: 'https://polygon.blockscout.com', 10: 'https://optimism.blockscout.com',
         130: 'https://unichain.blockscout.com', 42220: 'https://celo.blockscout.com', 1868: 'https://soneium.blockscout.com', 57073: 'https://explorer.inkonchain.com', 480: 'https://worldchain-mainnet.explorer.alchemy.com',
         4326: 'https://megaeth.blockscout.com', 4663: 'https://explorer.mainnet.chain.robinhood.com', 5042: 'https://explorer.arc.io', 143: 'https://monad.blockscout.com', 99901: 'https://explorer.elysium.kinetiq.xyz'}
S = requests.Session(); S.headers['user-agent'] = 'curl/8'
SRC = os.path.join(RAW6, 'src')
def fetch(cid, a, force=False):
    a = a.lower(); fn = os.path.join(SRC, '%d_%s.json' % (cid, a))
    if os.path.exists(fn) and not force: return json.load(open(fn))
    out = dict(chainId=cid, address=a, sources={}, name=None, via=None, url=None, impls=[])
    u = 'https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,compilation,proxyResolution' % (cid, a)
    for k in range(3):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 200:
                j = r.json()
                if j.get('sources'):
                    out.update(sources={p: v.get('content', '') for p, v in j['sources'].items()}, name=(j.get('compilation') or {}).get('name'), via='sourcify', url=u)
                    pr = j.get('proxyResolution') or {}
                    out['impls'] = [x.get('address', '').lower() for x in (pr.get('implementations') or []) if x.get('address')]
                break
            if r.status_code == 404: break
        except Exception as e: time.sleep(1 + k)
    if not out['sources'] and cid in SCOUT:
        u = SCOUT[cid] + '/api/v2/smart-contracts/' + a
        for k in range(3):
            try:
                r = S.get(u, timeout=40)
                if r.status_code == 200:
                    j = r.json()
                    if j.get('source_code'):
                        src = {j.get('file_path') or 'main.sol': j['source_code']}
                        for x in j.get('additional_sources') or []: src[x['file_path']] = x['source_code']
                        out.update(sources=src, name=j.get('name'), via='blockscout', url=u)
                    out['impls'] = [x['address'].lower() if 'address' in x else x.get('address_hash', '').lower() for x in (j.get('implementations') or [])]
                    break
                if r.status_code == 404: break
                time.sleep(1 + k)
            except Exception as e: time.sleep(1 + k)
    json.dump(out, open(fn, 'w'))
    return out
if __name__ == '__main__':
    o = fetch(int(sys.argv[1]), sys.argv[2])
    print(o['name'], o['via'], o['url'], len(o['sources']), o['impls'], sum(len(v) for v in o['sources'].values()))
