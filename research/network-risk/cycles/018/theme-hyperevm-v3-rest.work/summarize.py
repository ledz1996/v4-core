"""Sum the per-group lines that v3check18.py writes. Usage: summarize.py <out.json> <groups.jsonl>... [--plant-set groups-rest.json]"""
import sys, json, collections
args = [a for a in sys.argv[2:] if not a.startswith('--')]
plant_only = None
if '--plant-set' in sys.argv:
    g = json.load(open(sys.argv[sys.argv.index('--plant-set') + 1]))
    plant_only = set(tuple(x) for x in g['plant'])
    args = [a for a in args if a != sys.argv[sys.argv.index('--plant-set') + 1]]
C = collections.Counter(); H = collections.Counter(); other = collections.Counter(); seen = set(); dup = 0
swapdiff = []; mbdiff = 0; mis = []
for f in args:
    for l in open(f):
        x = json.loads(l); g = tuple(x['g'])
        if plant_only is not None and g not in plant_only: continue
        if g in seen: dup += 1; continue
        seen.add(g)
        C['groups'] += 1
        for k, v in x['counts'].items(): C[k] += v
        for k, v in x['hits'].items(): H[k] += v
        if x['variant']: C['groupsWithMintVariant'] += 1
        for t, v in x['other'].items(): other[t] += v
        if x['other']: C['groupsWithOtherUnreadTopic'] += 1
        if x['swapsCollector'] is not None and x['swapsCollector'] != x['swapsLive']: swapdiff.append([list(g), x['swapsCollector'], x['swapsLive']])
        if x['mbCollector'] is not None and x['mbCollector'] != x['mbLive']: mbdiff += 1
        mis += x['mismatchTx']
out = {'groups': len(seen), 'duplicateLines': dup, 'counts': C, 'branchCalls': H, 'otherTopics': other,
       'groupsWhereCollectorSwapCountDiffers': len(swapdiff), 'swapDiffExamples': swapdiff[:20],
       'groupsWhereCollectorMintBurnCountDiffers': mbdiff, 'mismatchTx': mis}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'swapDiffExamples'})[:3000])
