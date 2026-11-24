import json, gzip, glob, os
from fractions import Fraction
tot = dict(named=0, nonzero=0, pairs=0, priced=0, answered=0, failed=0, pairsFailed=0)
allhits = []
for fn in sorted(glob.glob('raw/all_faces_*.json.gz'), key=lambda f: int(f.split('_')[-1].split('.')[0])):
    d = json.load(gzip.open(fn, 'rt')); cid = d['chainId']
    tot['named'] += d['namedAddresses']; tot['nonzero'] += d['nonzero']; tot['pairs'] += d['pairsTested']; tot['priced'] += d['pricedTokens']
    tot['answered'] += d['answered']; tot['failed'] += d['failed']; tot['pairsFailed'] += d['pairsFailed']
    for r in d['rows']:
        a = r.get('sendT'); b = r.get('sendX')
        if not a or not b: continue
        a = [int(x) for x in a]; b = [int(x) for x in b]
        tmoved = a[2] != a[3]; xchg = a[0] != a[1]; xmoved = b[0] != b[1]; tchg = b[2] != b[3]
        if not ((tmoved and xchg) or (xmoved and tchg)): continue
        kind = []
        if tmoved and xchg:
            dT = a[3] - a[2]; dX = a[1] - a[0]
            if dX == dT: kind.append('X mirrors T one to one')
            elif dX * dT > 0: kind.append('X follows T at ratio %s' % (Fraction(dX, dT).limit_denominator(10**13)))
            else: kind.append('X rises by %d when T leaves' % dX)
        kind.append('X pays out when called directly' if xmoved else 'X does not pay out')
        if xmoved and tchg: kind.append('T reading follows X')
        allhits.append((cid, r['T'], r.get('Tsym'), r['X'], r.get('XisPriced'), r.get('Tusd'), kind))
print(tot)
for h in allhits: print(h)
json.dump(dict(totals=tot, hits=[list(h) for h in allhits]), open('raw/all_faces_summary.json', 'w'), indent=1)
