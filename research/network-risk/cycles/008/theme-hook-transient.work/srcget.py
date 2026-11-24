# Fetch verified source for a hook: cycle 5/6 cache, then Sourcify v2, then Blockscout, then Routescan. Saved under raw/src/.
from common import *
import requests, re
SCOUT = {1: 'https://eth.blockscout.com', 8453: 'https://base.blockscout.com', 42161: 'https://arbitrum.blockscout.com', 137: 'https://polygon.blockscout.com', 7777777: 'https://explorer.zora.energy', 4663: 'https://explorer.mainnet.chain.robinhood.com', 143: 'https://monadscan.blockscout.com', 999: 'https://www.hyperscan.com', 5042: 'https://explorer.arc.io', 196: 'https://www.oklink.com'}
def cached(cid, a):
    for d in (RAW, os.path.join(C6, 'raw'), os.path.join(C5, 'raw')):
        fn = os.path.join(d, 'src', '%d_%s.json' % (cid, a.lower()))
        if os.path.exists(fn):
            j = json.load(open(fn))
            if 'sources' in j: return j
    return None
def fetch(cid, a, force=False):
    a = a.lower()
    j = None if force else cached(cid, a)
    if j: return j
    d = os.path.join(RAW, 'src'); os.makedirs(d, exist_ok=True); fn = os.path.join(d, '%d_%s.json' % (cid, a))
    if os.path.exists(fn) and not force: return json.load(open(fn))
    j = None
    try:
        r = requests.get('https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,compilation,abi' % (cid, a), timeout=60)
        if r.status_code == 200: j = r.json(); j['_from'] = 'https://sourcify.dev/server/v2/contract/%d/%s' % (cid, a)
    except Exception: pass
    if not j or 'sources' not in j:
        j = None
        sc = CFG.get(cid, {}).get('scout') or SCOUT.get(cid)
        if sc:
            try:
                r = requests.get('%s/api/v2/smart-contracts/%s' % (sc, a), timeout=60, headers={'user-agent': 'curl/8'})
                if r.status_code == 200:
                    b = r.json()
                    if b.get('source_code'):
                        srcs = {b.get('file_path') or 'main.sol': {'content': b['source_code']}}
                        for x in b.get('additional_sources') or []: srcs[x['file_path']] = {'content': x['source_code']}
                        j = {'sources': srcs, 'compilation': {'name': b.get('name'), 'compilerVersion': b.get('compiler_version')}, 'abi': b.get('abi'), '_from': '%s/api/v2/smart-contracts/%s' % (sc, a)}
            except Exception: pass
    if not j:
        try:
            u = 'https://api.routescan.io/v2/network/mainnet/evm/%d/etherscan/api?module=contract&action=getsourcecode&address=%s' % (cid, a)
            r = requests.get(u, timeout=60, headers={'user-agent': 'curl/8'})
            if r.status_code == 200:
                b = r.json().get('result')
                if isinstance(b, list) and b and b[0].get('SourceCode'):
                    sc_ = b[0]['SourceCode']; srcs = None
                    if sc_.startswith('{{'):
                        try: srcs = json.loads(sc_[1:-1])['sources']
                        except Exception: pass
                    if srcs is None: srcs = {b[0].get('ContractName', 'main') + '.sol': {'content': sc_}}
                    j = {'sources': srcs, 'compilation': {'name': b[0].get('ContractName'), 'compilerVersion': b[0].get('CompilerVersion')}, 'abi': b[0].get('ABI'), '_from': u}
        except Exception: pass
    if not j: j = {'status': 'not found'}
    json.dump(j, open(fn, 'w'))
    return j
SKIPDIR = re.compile(r'(^|/)(node_modules|@openzeppelin|forge-std|openzeppelin-contracts|permit2)/')
def grep(j, pat, skip=True):
    out = []
    for name, s in j['sources'].items():
        lines = s['content'].split('\n')
        for i, l in enumerate(lines):
            if re.search(pat, l): out.append('%s:%d: %s' % (name, i + 1, l.rstrip()[:240]))
    return out
if __name__ == '__main__':
    if sys.argv[1] == 'all':
        import concurrent.futures as cf
        res = json.load(open(os.path.join(RAW, 'tscan.json')))
        def one(r):
            a = r.get('impl') or r['hook']
            j = fetch(r['chainId'], a)
            return r, j
        with cf.ThreadPoolExecutor(6) as ex: out = list(ex.map(one, res))
        tab = []
        for r, j in out:
            s = r.get('implScan') or r
            nm = (j.get('compilation') or {}).get('name') if 'sources' in j else None
            tg = grep(j, r'\btstore\s*\(|\btransient\b|TransientSlot|ReentrancyGuardTransient|\.tstore\(|asUint256\(\)\.tstore|\.asBoolean\(\)|StorageSlot\b.*Transient') if 'sources' in j else []
            tab.append(dict(chainId=r['chainId'], hook=r['hook'], impl=r.get('impl'), pools=r['pools'], name=nm, verified='sources' in j, src=j.get('_from'), tstore=s.get('tstore'), tload=s.get('tload'), dc=s.get('delegatecall'), srcTransientHits=len(tg)))
            print(r['chainId'], r['hook'], nm, 'TS', s.get('tstore'), 'TL', s.get('tload'), 'srcHits', len(tg), j.get('_from', '-'))
        json.dump(tab, open(os.path.join(RAW, 'srctab.json'), 'w'), indent=0)
    else:
        j = fetch(int(sys.argv[1]), sys.argv[2])
        if 'sources' not in j: print(j); sys.exit()
        print((j.get('compilation') or {}).get('name'), (j.get('compilation') or {}).get('compilerVersion'), j.get('_from'))
        print([k for k in j['sources'].keys()][:80])
        if len(sys.argv) > 3:
            for l in grep(j, sys.argv[3]): print(l)
