"""Which branch sides that cycle 24 lists as never executed by the MegaETH, Monad or HyperEVM producers ran in this
unit's reference runs. Usage: python3 coverage.py <ref.json> <out.json>"""
import sys, json, os
ref = json.load(open(sys.argv[1]))
lib = json.load(open(os.path.join(os.path.dirname(__file__), '..', '..', '..', '024', 'theme-producer-branch-coverage.work', 'out', 'library-sides.json')))
sides = ref['sides']
first = {}
for cid, ks in ref['perCaseSides'].items():
    for k in ks: first.setdefault(k, cid)
cases = {c['id']: c['tag'] for c in json.load(open(os.path.join(os.path.dirname(sys.argv[1]), 'allcases.json')))['cases']}
rows = []
for r in lib:
    miss = set()
    for ch, v in r['neverOnProducer'].items(): miss |= set(v)
    for sd in sorted(miss):
        k = '%d:%d' % (r['pc'], 1 if sd == 'taken' else 0)
        n = sides.get(k, 0)
        rows.append({'pc': r['pc'], 'side': sd, 'leadsTo': r['sideLeadsTo'][sd], 'file': r['file'], 'line': r['line'],
                     'snippet': r['snippet'][:90], 'neverOn': sorted(ch for ch, v in r['neverOnProducer'].items() if sd in v),
                     'countHere': n, 'firstCase': ((cases.get(int(first[k])) if first[k] != 'outside' else 'outside calls') if k in first else None)})
done = sum(1 for x in rows if x['countHere']); print('target sides', len(rows), 'executed', done)
for x in rows:
    if not x['countHere']: print('MISSING', x['pc'], x['side'], x['leadsTo'], x['file'].split('/')[-1], x['line'], x['snippet'][:70], x['neverOn'])
json.dump({'targets': len(rows), 'executed': done, 'rows': rows}, open(sys.argv[2], 'w'), indent=1)
