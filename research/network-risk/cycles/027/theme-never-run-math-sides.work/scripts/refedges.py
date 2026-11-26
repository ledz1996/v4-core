"""Cycle 27 Task 4 support: which operand edges the cycle 25 and cycle 26 cases reach in the reference EVM.
Those cases ran through eth_call on all 21 networks (cycles 25 and 26 compare.json), so an edge they reach has been
answered by every network's eth_call path, including the MegaETH and HyperEVM replicas.
usage: refedges.py 25|26|27 <out.json> [cases.json]   (offline, reference EVM only)"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
NR = '/home/user/v4-core/research/network-risk'
which = sys.argv[1]
if which == '25' or which == '27':
    sys.path.insert(0, NR + '/cycles/025/theme-unexecuted-sides.work/scripts')
    from common import enc_run, dec_run, codes_for, D, EOA
    import pyevm_cov as P
    cases = json.load(open(sys.argv[3] if len(sys.argv) > 3 else NR + '/cycles/025/theme-unexecuted-sides.work/out/allcases.json'))['cases']
else:
    sys.path.insert(0, NR + '/cycles/026/theme-hook-and-native-sides.work/scripts')
    from common26 import enc_run, dec_run, codes_for, balances_for, D, EOA
    import pyevm26 as P
    cases = json.load(open(NR + '/cycles/026/theme-hook-and-native-sides.work/out/cases.json'))['cases']
sys.path.insert(0, HERE)
from edges import edges, OPS
sys.path.insert(0, NR + '/cycles/024/theme-producer-branch-coverage.work/scripts')
from sites import sites
watch = {p: n for p, n, f, l, sn in sites() if n in OPS}
PM = 0x000000000004444c5dc75cB358380D2e3dE08A90
CNT = {}; FIRST = {}; cur = {}


def cb(pc, op, st):
    for ed in edges(watch[pc], st):
        k = '%d|%s' % (pc, ed); CNT[k] = CNT.get(k, 0) + 1; FIRST.setdefault(k, cur['id'])


res = {}; t = time.time()
for c in cases:
    cur['id'] = c['id']
    if which == '26':
        w = P.World(codes_for(PM, [c]), balances_for(PM)); data = enc_run([c], PM)
    else:
        w = P.World(codes_for(PM, [c])); data = enc_run([c])
        for k, v in c.get('storage', {}).items(): w.storage[(PM, int(k, 16))] = int(v, 16)
    w.watch = set(watch); w.watch_addr = PM; w.watch_cb = cb
    try:
        ok, ret = w.call(EOA, D, 0, data, False, 0)
        if ok:
            (uok, words, rv), = dec_run(ret)
            res[str(c['id'])] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
        else:
            res[str(c['id'])] = {'topFail': ret.hex()}
    except Exception as e:  # noqa
        res[str(c['id'])] = {'error': str(e)[:200]}
json.dump({'which': which, 'cases': len(cases), 'secs': round(time.time() - t), 'edges': CNT, 'firstCase': FIRST, 'results': res},
          open(sys.argv[2], 'w'))
print(which, len(cases), round(time.time() - t), len(CNT))
