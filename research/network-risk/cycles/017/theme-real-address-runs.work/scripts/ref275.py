"""Run set 6 scripts 275 to 277 (init at extreme prices) in the reference interpreter at the fresh address and compare
with Ethereum's fresh-address answer of this cycle and with the stored reference hash."""
import sys, os, json, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C
TOOLS = C.TOOLS
os.environ['PM_BUILD'] = os.path.join(TOOLS, '..', '..', 'build', 'PoolManager.json')
import pmdiff as P, pmdiff6 as S6
code = P.fetch_code(); SC = S6.scripts()
st = json.load(open(os.path.join(TOOLS, '..', '..', 'opcodes', 'pmdiff6.json')))
F = C.load('6', 'fresh', 1); out = {}
for i in map(int, sys.argv[2:]):
    wd = S6.world(code); wd.max_steps = 40_000_000; t = time.time()
    ok, ret = wd.call(0, S6.DRV, 0, SC[i][1], False, 0)
    h = hashlib.sha256(ret).hexdigest(); f = C.raw(F['results'][i])
    a = C.calls('6', None, ret, False); b = C.calls('6', None, f, False)
    out[i] = {'name': SC[i][0], 'refNowHash': h, 'storedHash': st['referenceHashes'][i], 'equalsStored': h == st['referenceHashes'][i],
              'equalsEthereumFreshToday': ret == f, 'firstDiffVsEthereum': C.first_diff(a, b), 'seconds': round(time.time() - t)}
    print(i, out[i], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
