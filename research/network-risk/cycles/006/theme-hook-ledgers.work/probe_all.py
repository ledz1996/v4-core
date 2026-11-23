# Run the cycle 5 probe (initialize from an ordinary account with seven PoolKey variants; each flagged callback called from the
# PoolManager address with a foreign PoolKey) and the verified source lookup on every candidate hook. Read-only eth_call.
import sys, concurrent.futures as cf, traceback
from common import *
os.chdir(C5)
import summ, probe as P, src as SRC
cand = json.load(open(os.path.join(RAW, 'cand.json')))
for cid in sorted(set(c['chainId'] for c in cand)): summ.census(cid)
os.chdir(HERE)
only = set(int(x) for x in sys.argv[1:])
def one(c):
    cid, h = c['chainId'], c['hook']
    fn = os.path.join(RAW, 'probe', '%d_%s.json' % (cid, h))
    try:
        if not os.path.exists(fn): P.probe(cid, h, verbose=False)
        s = SRC.fetch(cid, h)
        return cid, h, (s.get('compilation') or {}).get('name') if 'sources' in s else None
    except Exception as e:
        return cid, h, 'ERR ' + repr(e)[:100]
by = {}
for c in cand:
    if only and c['chainId'] not in only: continue
    by.setdefault(c['chainId'], []).append(c)
def chain(cs): return [one(c) for c in cs]
with cf.ThreadPoolExecutor(21) as ex:
    for res in ex.map(chain, by.values()):
        for r in res: print(*r, flush=True)
