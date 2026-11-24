"""Runs cycles/013/theme-swap-residuals.work/replay2.py (full Pool.swap loop from parent-block state) on
Monad with the mulDiv call sites tagged by bigcheck.py, and counts the large-number branches taken by
the swaps that only the full loop reproduces. Usage: python3 run_replay2.py <rawdir> <out.json> [FAULT env]"""
import sys, os, json, threading, collections
HERE = os.path.dirname(os.path.abspath(__file__))
R2 = '/home/user/v4-core/research/network-risk/cycles/013/theme-swap-residuals.work'
sys.path.insert(0, HERE); sys.path.insert(0, R2); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import bigcheck as B
import replay2 as R
lock = threading.Lock(); AGG = {'fullLoopOk': 0, 'swapsWithBig': 0, 'sitesBig': collections.Counter(), 'bigTx': collections.defaultdict(list)}
_sl = R.swap_loop
def swap_loop(*a, **k):
    del B.T()[:]
    return _sl(*a, **k)
R.swap_loop = swap_loop
_fr = R.full_replay
def full_replay(view, ev, pre, pf):
    r = _fr(view, ev, pre, pf)
    if r.get('ok') and r.get('mode') != 'zeroAmount':
        tr = list(B.T()); big = [s for s, f in tr if f]
        with lock:
            AGG['fullLoopOk'] += 1; AGG['swapsWithBig'] += bool(big)
            for s in set(big):
                AGG['sitesBig'][s] += 1
                if len(AGG['bigTx'][s]) < 5: AGG['bigTx'][s].append(ev['tx'])
    return r
R.full_replay = full_replay
raw, out = sys.argv[1], sys.argv[2]
sys.argv = ['replay2.py', '143', out, '--raw', raw, '--threads', '6']
R.main()
res = json.load(open(out)); res['bigBranches'] = {'fault': B.FAULT, 'fullLoopOk': AGG['fullLoopOk'], 'swapsWithBig': AGG['swapsWithBig'], 'sitesBig': dict(AGG['sitesBig']), 'bigTx': dict(AGG['bigTx'])}
json.dump(res, open(out, 'w'), indent=1)
print('bigBranches', res['bigBranches'])
