"""Sums out/runs/*.json per target and per op into out/summary.json, with jd, faults, avaxkey, memo and chain results."""
import glob, json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = {'targets': {}, 'jd': {}, 'faults': {}, 'memo': {}, 'avaxkey': {}}
for f in sorted(glob.glob(W + '/out/runs/*.json')):
    d = json.load(open(f)); t = S['targets'].setdefault(d['target'], {'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0, 'files': 0, 'bySet': {}, 'byOp': {}})
    for k in ('cases', 'mismatches', 'errors', 'steps'):
        t[k] += d[k]
    t['files'] += 1; t['bySet'][d['set']] = t['bySet'].get(d['set'], 0) + d['cases']
    for op, v in d['byOp'].items():
        o = t['byOp'].setdefault(op, [0, 0, 0])
        for i in range(3): o[i] += v[i]
for f in sorted(glob.glob(W + '/out/jd/*.json')):
    d = json.load(open(f)); S['jd'][os.path.basename(f)[:-5]] = {k: d.get(k) for k in ('programs', 'bitmapMismatchPrograms', 'validMismatchPrograms', 'dests', 'flippedBit', 'patch')} | {'pm': d['poolmanager']}
for f in sorted(glob.glob(W + '/out/faults/*.json')):
    d = json.load(open(f)); S['faults'][os.path.basename(f)[:-5]] = {'set': d['set'], 'cases': d['cases'], 'mismatches': d['mismatches'], 'where': d['faultWhere']}
for f in sorted(glob.glob(W + '/out/memo/*.json')):
    d = json.load(open(f)); S['memo'][os.path.basename(f)[:-5]] = {k: d.get(k) for k in ('steps', 'mismatches', 'errors', 'memoHits', 'memoMisses', 'byKind')}
for f in sorted(glob.glob(W + '/out/avaxkey-*.json')):
    d = json.load(open(f)); S['avaxkey'][os.path.basename(f)[:-5]] = {k: d.get(k) for k in ('cases', 'mismatches', 'changed', 'byTag', 'callers', 'transientFunctions')}
S['total'] = {k: sum(t[k] for t in S['targets'].values()) for k in ('cases', 'mismatches', 'errors', 'steps')}
json.dump(S, open(W + '/out/summary.json', 'w'), indent=1)
for k, t in S['targets'].items():
    print(k, t['files'], t['cases'], t['mismatches'], t['errors'], t['bySet'])
print('total', S['total'])
