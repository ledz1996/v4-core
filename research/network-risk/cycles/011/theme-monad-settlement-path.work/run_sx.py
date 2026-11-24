"""SIGNEXTEND with a non literal index (settlejit.py) against the specification.
Usage: python3 -I run_sx.py <out.json> [randomCases]"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settlejit as J
U = 1 << 256
rng = random.Random(7); n = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
ixs = list(range(0, 40)) + [255, 256, 1 << 32, (1 << 32) + 3, 1 << 64, (1 << 64) + 5, U - 1, 1 << 255, (1 << 128) + 1]
fails = []; cases = 0
def vals():
    out = [0, 1, U - 1, 1 << 255]
    for b in range(32):
        out += [1 << (8 * b + 7), (1 << (8 * b + 7)) - 1, rng.getrandbits(256)]
    return out
def run(ix, x):
    global cases
    exp = J.spec_signextend(ix, x)
    for loc in ('gpr', 'avx', 'stack'):
        for live in (True, False):
            for free in (True, False):
                eax = J.bounded_rax(J.CPU(rng), loc, ix, live, free)
                for name, f in (('avx', J.signextend_avx), ('gpr', J.signextend_gpr), ('mem', J.signextend_mem)):
                    got = f(eax, x); cases += 1
                    if got != exp and len(fails) < 20: fails.append({'ix': hex(ix), 'x': hex(x), 'ixLoc': loc, 'srcLoc': name, 'got': hex(got), 'exp': hex(exp)})
for ix in ixs:
    for x in vals(): run(ix, x)
for _ in range(n):
    k = rng.randrange(4)
    ix = rng.randrange(40) if k < 2 else ((rng.getrandbits(224) << 32) | rng.randrange(40) if k == 2 else rng.getrandbits(256))
    run(ix, rng.getrandbits(256))
res = {'cases': cases, 'failures': len(fails), 'firstFailures': fails, 'coverage': {k: v for k, v in J.COV.items() if k.startswith(('sx', 'br'))}}
json.dump(res, open(sys.argv[1], 'w'), indent=1); print(json.dumps(res)[:1500])
