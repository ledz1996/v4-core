"""Task 1 summary per network: JUMPIs both / one / never, and for one-sided ones whether the missing side reverts (static walk, sides.py)."""
import json, os
from sides import sides
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for c in (143, 4326, 999, 8453):
    D = json.load(open('%s/../out/%d/branches.json' % (HERE, c)))
    s = {'txs': D['totals']['txs'], 'frames': D['totals']['frames'], 'steps': D['totals']['steps'], 'jumpi': D['jumpi'], 'both': D['both'], 'oneSide': D['oneSide'], 'never': D['never'],
         'oneSideMissingSideReverts': 0, 'oneSideMissingSideComputes': 0, 'oneSideComputingList': [], 'neverByFile': {}}
    for r in D['rows']:
        if r['status'] == 'one':
            miss = 'taken' if r['taken'] == 0 else 'fallthrough'
            if sides(r['pc'])[miss] == 'revert': s['oneSideMissingSideReverts'] += 1
            else:
                s['oneSideMissingSideComputes'] += 1; s['oneSideComputingList'].append('%d %s:%s %s' % (r['pc'], r['file'], r['line'], miss))
        if r['status'] == 'never':
            k = '%s:%s' % (r['file'], r['line']); s['neverByFile'][k] = s['neverByFile'].get(k, 0) + 1
    out[c] = s
    print(c, {k: v for k, v in s.items() if not isinstance(v, (list, dict))})
json.dump(out, open(HERE + '/../out/task1-summary.json', 'w'), indent=1)
