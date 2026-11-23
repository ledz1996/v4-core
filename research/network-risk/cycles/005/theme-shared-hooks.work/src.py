# Fetch verified source from Sourcify (v2 API); fall back to a Blockscout instance when one is configured. Saved under raw/src/.
import sys, json, os, requests, re
from config import CFG
SCOUT = {1: 'https://eth.blockscout.com', 8453: 'https://base.blockscout.com', 42161: 'https://arbitrum.blockscout.com', 137: 'https://polygon.blockscout.com', 7777777: 'https://explorer.zora.energy', 4663: 'https://explorer.mainnet.chain.robinhood.com', 143: 'https://monadscan.blockscout.com', 999: 'https://www.hyperscan.com', 5042: 'https://explorer.arc.io'}
def fetch(cid, addr):
    d = os.path.join('raw', 'src'); os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, '%d_%s.json' % (cid, addr.lower()))
    if os.path.exists(fn): return json.load(open(fn))
    j = None
    try:
        r = requests.get('https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,compilation,abi' % (cid, addr), timeout=60)
        if r.status_code == 200: j = r.json(); j['_from'] = 'https://sourcify.dev/server/v2/contract/%d/%s' % (cid, addr)
    except Exception as e: pass
    if not j or 'sources' not in j:
        sc = CFG.get(cid, {}).get('scout') or SCOUT.get(cid)
        if sc:
            try:
                r = requests.get('%s/api/v2/smart-contracts/%s' % (sc, addr), timeout=60, headers={'user-agent': 'curl/8'})
                if r.status_code == 200:
                    b = r.json()
                    if b.get('source_code'):
                        srcs = {b.get('file_path') or 'main.sol': {'content': b['source_code']}}
                        for a in b.get('additional_sources') or []: srcs[a['file_path']] = {'content': a['source_code']}
                        j = {'sources': srcs, 'compilation': {'name': b.get('name'), 'compilerVersion': b.get('compiler_version')}, 'abi': b.get('abi'), '_from': '%s/api/v2/smart-contracts/%s' % (sc, addr)}
            except Exception as e: pass
    if not j: j = {'status': 'not found'}
    json.dump(j, open(fn, 'w'))
    return j
if __name__ == '__main__':
    j = fetch(int(sys.argv[1]), sys.argv[2])
    if 'sources' not in j: print(j); sys.exit()
    print(j.get('compilation', {}).get('name'), j.get('compilation', {}).get('compilerVersion'), j.get('_from'), [k.split('/')[-1] for k in j['sources'].keys()][:60])
    pat = sys.argv[3] if len(sys.argv) > 3 else None
    if pat:
        for name, s in j['sources'].items():
            lines = s['content'].split('\n')
            for i, l in enumerate(lines):
                if re.search(pat, l): print('%s:%d: %s' % (name.split('/')[-1], i + 1, l.rstrip()[:220]))
