"""Totals per network for the research file. Arc native legs are taken from raw/arc-native.json (system emitter logs)."""
import json
from collections import Counter
FILES = {143: ['raw/an2-143.json', 'raw/an2-143b.json'], 4326: ['raw/an3-4326.json'], 4217: ['raw/an-4217.json', 'raw/an2-4217c.json'],
         5042: ['raw/an2-5042.json'], 999: ['raw/an2-999.json']}
arc = {r['tx']: r for r in json.load(open('raw/arc-native.json'))}
tot = {}
for cid, fs in FILES.items():
    R = [r for f in fs for r in json.load(open(f))['results']]
    C = [r for r in R if 'result' in r]
    res = Counter()
    for r in C:
        ok = True
        for c, v in r['currencies'].items():
            d = int(v['diff'])
            if cid == 5042 and int(c, 16) == 0: d = int(arc[r['tx']]['diff'])
            if d != 0: ok = False; res['diff %+d' % d] += 1
        res['exact' if ok else 'differs'] += 1
    t = {'txRead': len(R), 'txChecked': len(C), 'result': dict(res),
         'kinds': dict(Counter(r['kind'] for r in C)),
         'removalEvents': sum(r['removals'] for r in C), 'collectEvents': sum(r['collects'] for r in C),
         'singleRemoval': sum(1 for r in C if r['kind'] == 'remove'), 'singleCollect': sum(1 for r in C if r['kind'] == 'collect'),
         'eventsWithFees': sum(1 for r in C for e in r['detail'] if 'fees' in e and any(int(x) for x in e['fees'])),
         'legsPaid': sum(1 for r in C for v in r['currencies'].values() if int(v['out']) > 0),
         'nativeLegs': sum(1 for r in C if 'native' in r), 'storageMismatch': sum(1 for r in C if r['storageMismatch']),
         'aside': dict(Counter(r['aside'] for r in R if r.get('aside'))), 'errors': sum(1 for r in R if 'error' in r),
         'blocks': [min(r['block'] for r in R), max(r['block'] for r in R)]}
    if cid in (143, 4326, 999):
        nat = [r for r in C if 'native' in r]
        t['nativeBalanceAgrees'] = sum(1 for r in nat for c, v in r['currencies'].items() if int(c, 16) == 0 and int(r['native']['balanceDiff']) == -(int(v['out']) - int(v['in'])))
        t['nativeAloneInBlock'] = sum(1 for r in nat if not r['native']['otherPmTxInBlock'])
    tot[cid] = t; print(cid, json.dumps(t))
json.dump(tot, open('totals.json', 'w'), indent=1)
