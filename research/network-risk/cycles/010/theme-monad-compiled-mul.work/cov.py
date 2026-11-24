"""Branch coverage of the transcription for a sample of each path. Usage: python3 -I cov.py <workdir>"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import muljit as J, run as R
rng = random.Random(5); random.seed(6); st = {}; fl = []
for i in range(60000):
    R.mul_mod2(rng, 96, R.operand(rng), R.operand(rng), False, st, fl, 'a')
    R.mul_mod2(rng, 128, R.operand(rng), R.operand(rng), False, st, fl, 'b')
    R.mul_optimized(rng, R.SITE_MUL_LITERALS[i % len(R.SITE_MUL_LITERALS)], R.operand(rng), st, fl, 'c')
json.dump({'stats': st, 'failures': fl, 'branches': dict(sorted(J.COV.items()))}, open(os.path.join(sys.argv[1], 'coverage.json'), 'w'), indent=1)
print(st, len(fl)); print(json.dumps(dict(sorted(J.COV.items())), indent=0))
