"""Pick transactions to rerun from a log dump. Usage: select.py <logs.json|.gz> <perPool> <out.json> [seed]
All transactions with a PoolManager log other than Swap, plus up to perPool swap transactions per pool id."""
import sys, json, gzip, random, collections
from common import EV
p, per, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = json.load(gzip.open(p) if p.endswith('.gz') else open(p))
logs = d['logs']; random.seed(int(sys.argv[4]) if len(sys.argv) > 4 else 13)
blocktx = collections.defaultdict(list); kinds = collections.defaultdict(set); pools = collections.defaultdict(set)
for l in sorted(logs, key=lambda l: (l['b'], l['i'], l['li'])):
    if l['tx'] not in blocktx[l['b']]: blocktx[l['b']].append(l['tx'])
    k = EV.get(l['topics'][0], 'other'); kinds[l['tx']].add(k)
    if k == 'Swap': pools[l['topics'][1]].add(l['tx'])
last = {txs[-1] for txs in blocktx.values()}
pick = {h for h, k in kinds.items() if k - {'Swap'}}
for pid, txs in pools.items():
    txs = sorted(txs); random.shuffle(txs); pick |= set(txs[:per])
lst = sorted([[h, int(h in last)] for h in pick])
json.dump(lst, open(out, 'w'))
print('txs', len(kinds), 'pools', len(pools), 'picked', len(lst), 'nonSwap', sum(1 for h, k in kinds.items() if k - {'Swap'}))
