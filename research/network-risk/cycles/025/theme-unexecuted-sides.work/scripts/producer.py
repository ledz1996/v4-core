"""For MegaETH, HyperEVM and Monad: which branch sides each case executes (reference run) and whether mined
transactions of that network's producer have executed each of them (cycle 24 counts,
cycles/024/theme-producer-branch-coverage.work/out/<chainId>/branches.json). Usage: python3 producer.py <ref.json> <allcases.json> <out.json>"""
import sys, os, json
ref = json.load(open(sys.argv[1])); cases = {str(c['id']): c['tag'] for c in json.load(open(sys.argv[2]))['cases']}
C24 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '024', 'theme-producer-branch-coverage.work', 'out')
out = {}
for cid in ('4326', '999', '143'):
    rows = json.load(open(os.path.join(C24, cid, 'branches.json')))['rows']
    cnt = {}
    for r in rows: cnt['%d:1' % r['pc']] = r['taken']; cnt['%d:0' % r['pc']] = r['fallthrough']
    per = {}; full = 0
    for k, sides in ref['perCaseSides'].items():
        miss = [s for s in sides if not cnt.get(s)]
        per[k] = {'tag': cases.get(k, k), 'sides': len(sides), 'unminedSides': miss}
        if not miss: full += 1
    allsides = set(ref['sides'])
    out[cid] = {'cases': len(per), 'casesAllSidesMined': full, 'sidesRunHere': len(allsides),
                'sidesRunHereNeverMined': sorted(s for s in allsides if not cnt.get(s)), 'perCase': per}
    print(cid, 'cases', len(per), 'with every side mined', full, 'sides run here', len(allsides), 'of which never mined', len(out[cid]['sidesRunHereNeverMined']))
json.dump(out, open(sys.argv[3], 'w'))
