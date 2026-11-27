# Fetch verified source of the official Universal Router and PositionManager addresses on each network from Sourcify (no key),
# and check that every PoolManager.settle in the source is preceded by poolManager.sync(currency) in DeltaResolver._settle.
import sys, json, os, re, glob, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
A = json.load(open('out/periphery_addrs.json'))
jobs = []
for cid, v in A.items():
    for k, a in v['UR'].items(): jobs.append((int(cid), k, a))
    jobs.append((int(cid), 'PositionManager', v['PosM']))
def one(j):
    cid, k, a = j
    try: r = fetch_src(cid, a)
    except Exception as e: return dict(chainId=cid, name=k, addr=a, err=str(e)[:100])
    if not r: return dict(chainId=cid, name=k, addr=a, verified=False)
    d = r[0]; settles = []; dr = []
    for f in glob.glob(d + '/*.sol'):
        if '__lib__v4-core__' in f or 'interfaces' in f: continue
        for i, line in enumerate(open(f, errors='ignore')):
            s = line.strip()
            if s.startswith('//') or s.startswith('*') or s.startswith('///'): continue
            if re.search(r'poolManager\.(settle|settleFor)\b|\.settle\{|\.settleFor\(', s): settles.append('%s:%d %s' % (os.path.basename(f), i + 1, s[:80]))
        if f.endswith('DeltaResolver.sol'):
            t = open(f).read(); m = re.search(r'function _settle\(.*?\n    \}', t, re.S)
            dr.append(bool(m and re.search(r'poolManager\.sync\(currency\);\s*if \(currency\.isAddressZero\(\)\) \{\s*poolManager\.settle\{value: amount\}\(\);\s*\} else \{\s*_pay\(currency, payer, amount\);\s*poolManager\.settle\(\);', m.group(0))))
    return dict(chainId=cid, name=k, addr=a, verified=True, contract=r[1], nfiles=r[2], settleSites=sorted(set(settles)), deltaResolverSyncFirst=dr)
with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
json.dump(res, open('out/periphery_src.json', 'w'), indent=1)
for x in res: print(x['chainId'], x['name'], x['addr'][:10], x.get('verified'), x.get('contract'), len(x.get('settleSites', [])), set(s.split(' ',1)[0].split(':')[0] for s in x.get('settleSites', [])), x.get('deltaResolverSyncFirst'), x.get('err',''))
