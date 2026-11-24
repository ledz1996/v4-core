"""Instruction and branch coverage of the PoolManager bytecode over the three script
sets, measured in the reference interpreter.
Usage: python3 coverage.py <coverage file>[,<coverage file>...] <out.json> [maxSteps]"""
import sys, json, random
sys.path.insert(0,"/home/user/v4-core/research/network-risk/tools/opdiff")
import pmdiff as P, pmdiff2 as Q
from pyevm import NAMES
from bytecode import worlds

extra = [json.load(open(f)) for f in sys.argv[1].split(',')]; out = sys.argv[2]; max_steps = int(sys.argv[3]) if len(sys.argv) > 3 else 400_000
code = P.fetch_code(); pm, drv = int(P.PM, 16), int(P.DRV, 16); w1, w2 = worlds(code)
cover = set(); branches = {}; ops = {}
rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(250)]
rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(300)]
for scripts, mk in ((s1, w1), (s2, w2)):
    for data, _, _ in scripts:
        w = mk(); w.max_steps = max_steps
        try: w.call(0, drv, 0, data, False, 0)
        except TimeoutError: pass
        cover |= w.cover.get(pm, set())
        for (a, pc), o in w.branches.items():
            if a == pm: branches.setdefault(pc, set()).update(o)
        for o, c in w.ops.items(): ops[NAMES.get(o, hex(o))] = ops.get(NAMES.get(o, hex(o)), 0) + c
two = {'instructions': len(cover), 'both': sum(1 for v in branches.values() if len(v) == 2)}
for cov3 in extra:
    cover |= set(cov3['cover'])
    for k, v in cov3['branches'].items(): branches.setdefault(int(k), set()).update(v)
    for k, c in cov3['ops'].items(): ops[k] = ops.get(k, 0) + c
starts = []; i = 0
while i < len(code):
    starts.append(i); op = code[i]; i += op - 0x5e if 0x60 <= op <= 0x7f else 1
jumpis = [p for p in starts if code[p] == 0x57]
present = {NAMES.get(code[p], hex(code[p])) for p in starts}
# uncovered runs of instructions
runs = []; cur = None
for p in starts:
    if p not in cover:
        if cur is None: cur = [p, p, 0]
        cur[1] = p; cur[2] += 1
    elif cur: runs.append(cur); cur = None
if cur: runs.append(cur)
res = {'instructions': len(starts), 'executed': len(cover & set(starts)), 'executedByFirstTwoSets': two['instructions'],
       'jumpi': len(jumpis), 'jumpiBothSides': sum(1 for p in jumpis if len(branches.get(p, ())) == 2), 'jumpiBothSidesFirstTwoSets': two['both'],
       'jumpiOneSide': sum(1 for p in jumpis if len(branches.get(p, ())) == 1), 'jumpiNever': sum(1 for p in jumpis if p not in branches),
       'opcodesPresentNotExecuted': sorted(present - set(ops)),
       'largestUncoveredRuns': sorted(([a, b, n] for a, b, n in runs), key=lambda r: -r[2])[:25], 'uncoveredRuns': len(runs)}
print({k: v for k, v in res.items() if k != 'largestUncoveredRuns'}); print(res['largestUncoveredRuns'][:12])
res['cover']=sorted(cover); res['branches']={str(k):sorted(v) for k,v in branches.items()}
json.dump(res, open(out, 'w'))
