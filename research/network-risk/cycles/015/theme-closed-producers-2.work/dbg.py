"""Debug: rerun one (pool, block) group of v3check.py with alternative fees to see what explains a mismatch. Read only."""
import sys, json
sys.argv = ['v3check.py', 'raw/_dbg.json', '--limit', '1']
src = open('v3check.py').read().split('t0 = time.time(); n = 0')[0]
exec(src)
R = json.load(open(sys.argv_in if False else 'raw/stageB-300.json'))
import collections
P = pools
out = []
for mm in R['mismatches']:
    pool, block = mm['pool'], mm['block']
    base = P[pool]['fee']; found = None
    for fee in [base] + [f for f in range(0, 30001, 50) if f != base] + list(range(base - 60, base + 61)):
        P[pool]['fee'] = fee
        try: res = run_group((pool, block))
        except Exception as e: continue
        st = [k for k, r, ok in res if r and r[2] == mm['logIndex']]
        if st and st[0] == 'ok': found = fee; break
    P[pool]['fee'] = base
    out.append((mm['tx'], P[pool]['factory'], P[pool].get('getPool', 'u24'), base, found))
    print(out[-1], flush=True)
json.dump(out, open('raw/dbg-fees.json', 'w'))
