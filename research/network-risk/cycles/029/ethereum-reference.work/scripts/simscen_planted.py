"""Planted-fault check of simscen.py: reruns two scenarios against one endpoint with the reference altered (one bit of
one return word, then one bit of one final storage word) and expects the comparison to report each. Read-only."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/ethereum-reference.work/scripts')
import simscen as M
S = M.S; orig = S.ref; mode = {'m': 0}
def bad(sc):
    outs, st = orig(sc)
    if mode['m'] == 0:
        i = max(i for i, (ok, r) in enumerate(outs) if ok and r)
        r = outs[i][1]; outs[i] = (True, r[:-1] + ('0' if r[-1] != '0' else '1'))
    else:
        k = sorted(st)[0]; st[k] = hex(int(st[k], 16) ^ 1)
    return outs, st
S.ref = bad
names = [k for k in S.SCEN if k.startswith('A4') or k.startswith('C1')]
S.SCEN = {k: S.SCEN[k] for k in names}
for m in (0, 1):
    mode['m'] = m; sys.argv = ['x', f'/home/user/v4-core/research/network-risk/cycles/029/ethereum-reference.work/out/simscen-planted-{m}.json', 'https://ethereum.public.blockpi.network/v1/rpc/public']
    M.main()
