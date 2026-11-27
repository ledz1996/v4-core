"""Sums out/runs/*.json into out/summary.json. usage: python3 -I aggregate.py"""
import glob, json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = {}
for f in sorted(glob.glob(W + '/out/runs/*.json')):
    d = json.load(open(f))
    a = S.setdefault(d['arch'], {'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0, 'bySet': {}, 'byOp': {}, 'randomByOp': {}, 'records': [], 'files': 0})
    a['files'] += 1
    for k in ('cases', 'mismatches', 'errors', 'steps'):
        a[k] += d[k]
    s = a['bySet'].setdefault(d['set'], [0, 0, 0]); s[0] += d['cases']; s[1] += d['mismatches']; s[2] += d['errors']
    for op, v in d['byOp'].items():
        o = a['byOp'].setdefault(op, [0, 0, 0])
        for i in range(3): o[i] += v[i]
        if d['set'] == 'random':
            r = a['randomByOp'].setdefault(op, [0, 0, 0])
            for i in range(3): r[i] += v[i]
    a['records'] += d['records']
json.dump(S, open(W + '/out/summary.json', 'w'), indent=1)
for arch, a in S.items():
    print(arch, {k: a[k] for k in ('files', 'cases', 'mismatches', 'errors', 'steps')}, a['bySet'])
    print('  random per op', {k: v[0] for k, v in sorted(a['randomByOp'].items())})
