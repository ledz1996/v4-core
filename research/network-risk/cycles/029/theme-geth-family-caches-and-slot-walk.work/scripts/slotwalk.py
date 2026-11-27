"""Task 3 of theme-geth-family-caches-and-slot-walk (L-1176): the slot operand of every SSTORE, SLOAD,
TSTORE and TLOAD site of research/network-risk/build/PoolManager.json.

Part A, static: every storage and transient storage instruction of the runtime, with its source line from
the solc source map of cycle 12 (cycles/012/theme-bytecode-coverage.work/build-srcmap.json, whose runtime
is checked to equal the build).
Part B, dynamic: the script sets 1, 2, 3, 5 and 6 run in a provenance-tracking copy of the reference
interpreter (taintevm.py). For every site the classes of slot operand seen are recorded: constant,
keccak output, keccak output plus a constant, or anything else.
Seeds are those of the script generators: set 1 7_2026_11_24, set 2 11_2026_11_24, set 3 3_2026_11_24,
set 5 5_2026_11_24 (inside pmdiff5.scripts), set 6 6_2026_11_24 (inside pmdiff6.scripts).
Usage: python3 slotwalk.py <out.json> [n3]
"""
import os, sys, json, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
NR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(1, HERE)
os.environ['PM_BUILD'] = os.path.join(NR, 'build', 'PoolManager.json')
import pmdiff as P, pmdiff2 as Q, pmdiff3 as R, pmdiff5 as F, pmdiff6 as S6
import bytecode as BC
from taintevm import TaintWorld
from pyevm import NAMES

out = sys.argv[1]; n3 = int(sys.argv[2]) if len(sys.argv) > 2 else 300
SETS = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else {'1', '2', '3', '5', '6'}  # which script sets to run
code = P.fetch_code(); PMI, DRV = int(P.PM, 16), int(P.DRV, 16)
build = json.load(open(os.environ['PM_BUILD']))
sm = json.load(open(os.path.join(NR, 'cycles', '012', 'theme-bytecode-coverage.work', 'build-srcmap.json')))
assert sm['runtime'] == build['runtime'], 'source map build differs'
sys.path.insert(2, os.path.join(NR, 'cycles', '012', 'theme-bytecode-coverage.work'))
import srcmap

starts = []; i = 0
while i < len(code):
    starts.append(i); op = code[i]; i += op - 0x5e if 0x60 <= op <= 0x7f else 1
codeinstr = set(starts[:srcmap.NCODE])
static = {}
for p in starts:
    if code[p] in (0x54, 0x55, 0x5c, 0x5d) and p in codeinstr:
        static[p] = {'op': NAMES[code[p]], 'src': srcmap.loc(p)}
print('static sites', {o: sum(1 for v in static.values() if v['op'] == o) for o in ('SLOAD', 'SSTORE', 'TLOAD', 'TSTORE')}, flush=True)

agg = {}; runs = {'scripts': 0, 'heavy': 0, 'steps': 0}


def merge(w):
    for (op, pc), d in w.sites.items():
        a = agg.setdefault(pc, {})
        for k, c in d.items(): a[json.dumps(k)] = a.get(json.dumps(k), 0) + c
    runs['steps'] += w.steps


def go(w, data, ms, drv=None):
    w.watch = PMI; w.max_steps = ms; runs['scripts'] += 1
    try: w.call(0, DRV if drv is None else drv, 0, data, False, 0)
    except TimeoutError: runs['heavy'] += 1
    merge(w)


t0 = time.time()
BC.World = TaintWorld; w1, w2 = BC.worlds(code)
rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(250)]
for d, _, _ in (s1 if '1' in SETS else []): go(w1(), d, 3_000_000)
print('set1', runs, round(time.time() - t0), flush=True)
rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(300)]
for d, _, _ in (s2 if '2' in SETS else []): go(w2(), d, 3_000_000)
print('set2', runs, round(time.time() - t0), flush=True)
rnd = random.Random(3_2026_11_24); s3 = [R.build(rnd, i, code) for i in range(n3)] if '3' in SETS else []  # built with the plain reference
R.World = TaintWorld
for d, _, _ in s3: go(R.world(code), d, 3_000_000)
print('set3', runs, round(time.time() - t0), flush=True)
F.World = TaintWorld
drv5 = F.driver() if hasattr(F, 'driver') else P.driver()
for item in (F.scripts() if '5' in SETS else []):
    d = item[0] if isinstance(item, tuple) else item
    if isinstance(d, tuple): d = d[0]
    go(TaintWorld({PMI: code, DRV: drv5}), d, 8_000_000)
print('set5', runs, round(time.time() - t0), flush=True)
S6.World = TaintWorld
for name, d in (S6.scripts() if '6' in SETS else []): go(S6.world(code), d, 8_000_000, S6.DRV)  # set 6 has its own driver address
print('set6', runs, round(time.time() - t0), flush=True)

res = {'static': {}, 'runs': runs}
for p, v in sorted(static.items()):
    seen = agg.get(p, {})
    classes = sorted({json.loads(k)[0] for k in seen})
    res['static'][str(p)] = dict(v, executed=bool(seen), classes=classes, seen={k: c for k, c in sorted(seen.items(), key=lambda x: -x[1])[:12]}, distinct=len(seen))
json.dump(res, open(out, 'w'), indent=1)
print('done', round(time.time() - t0))
