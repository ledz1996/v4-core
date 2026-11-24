"""Coverage of sets 1 and 2 in the reference interpreter, dumped with branch outcomes (cycle 12)."""
import sys, json, random, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
import pmdiff as P, pmdiff2 as Q
from bytecode import worlds
code = P.fetch_code(); pm, drv = int(P.PM, 16), int(P.DRV, 16); w1, w2 = worlds(code)
cover = set(); branches = {}
rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(250)]
rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(300)]
for scripts, mk in ((s1, w1), (s2, w2)):
    for data, _, _ in scripts:
        w = mk(); w.max_steps = 400_000
        try: w.call(0, drv, 0, data, False, 0)
        except TimeoutError: pass
        cover |= w.cover.get(pm, set())
        for (a, pc), o in w.branches.items():
            if a == pm: branches.setdefault(pc, set()).update(o)
json.dump({'cover': sorted(cover), 'branches': {str(k): sorted(v) for k, v in branches.items()}}, open(sys.argv[1], 'w'))
print(len(cover), len(branches))
