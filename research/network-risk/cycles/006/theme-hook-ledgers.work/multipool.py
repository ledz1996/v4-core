# For every candidate hook with more than one pool: which currencies appear in two or more pools of the hook, and how many of them are
# not a common quote currency (present in under 10 percent of the hook's pools)? Such a token has pools against two currencies or two fee tiers.
import sys, collections
from common import *
os.chdir(C5)
from summ import census, load
cand = json.load(open(os.path.join(RAW, 'cand.json')))
for cid in sorted(set(c['chainId'] for c in cand)): census(cid)
os.chdir(HERE)
byc = collections.defaultdict(list)
for c in cand: byc[c['chainId']].append(c)
out = {}
for cid, cs in byc.items():
    hs = set(c['hook'] for c in cs); rows = collections.defaultdict(list)
    for r in load(cid):
        if r[6] in hs: rows[r[6]].append(r)
    for c in cs:
        R = rows.get(c['hook'], [])
        if len(R) < 2: continue
        cur = collections.Counter()
        for r in R: cur[r[2]] += 1; cur[r[3]] += 1
        quotes = [x for x, n in cur.items() if n >= max(2, 0.1 * len(R))]
        multi = [x for x, n in cur.items() if n >= 2 and x not in quotes]
        ex = []
        for x in multi[:3]:
            ex.append((x, [(r[2] if r[3] == x else r[3], r[4], r[5]) for r in R if x in (r[2], r[3])][:4]))
        out['%d_%s' % (cid, c['hook'])] = dict(rows=len(R), quotes=quotes[:8], nQuotes=len(quotes), multi=len(multi), ex=ex)
        print(cid, c['hook'], 'rows', len(R), 'quotes', len(quotes), [q[:8] for q in quotes[:6]], 'multiTokens', len(multi), ex[:2] if multi else '')
json.dump(out, open(os.path.join(RAW, 'multipool.json'), 'w'))
