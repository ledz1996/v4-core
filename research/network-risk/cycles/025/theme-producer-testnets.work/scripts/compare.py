"""Sides a testnet replay executed that the mainnet producer never executed (cycle 24 out/<cid>/branches.json plus extra-shard*.json).
usage: compare.py <testnet cid> <mainnet cid> [more mainnet cids]  writes ../out/sides-added-<testnet>.json"""
import sys, json, glob, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap as S
HERE = os.path.dirname(os.path.abspath(__file__))
C24 = '/home/user/v4-core/research/network-risk/cycles/024/theme-producer-branch-coverage.work/out'
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/024/theme-producer-branch-coverage.work/scripts')
from sides import sides
t = int(sys.argv[1]); mains = list(map(int, sys.argv[2:]))
T = json.load(open('%s/../out/%d/branches.json' % (HERE, t)))
mb = {}
for m in mains:
    for r in json.load(open('%s/%d/branches.json' % (C24, m)))['rows']:
        mb.setdefault(r['pc'], [0, 0]); mb[r['pc']][0] += r['taken']; mb[r['pc']][1] += r['fallthrough']
    for f in glob.glob('%s/%d/extra-shard*.json' % (C24, m)):
        for k, v in json.load(open(f))['branches'].items():
            pc, s = map(int, k.split(':')); mb.setdefault(pc, [0, 0]); mb[pc][0 if s else 1] += v
added = []; testnet_missing_side = 0
for r in T['rows']:
    m = mb.get(r['pc'], [0, 0])
    for side, idx in (('taken', 0), ('fallthrough', 1)):
        if r[side] and not m[idx]:
            added.append({'pc': r['pc'], 'side': side, 'testnetCount': r[side], 'file': r['file'], 'line': r['line'], 'snippet': r['snippet'][:100], 'leadsTo': sides(r['pc'])[side]})
out = {'testnet': t, 'mainnet': mains, 'testnetBoth': T['both'], 'testnetOne': T['oneSide'], 'testnetNever': T['never'], 'added': added}
json.dump(out, open('%s/../out/sides-added-%d.json' % (HERE, t), 'w'), indent=1)
print(t, 'both', T['both'], 'one', T['oneSide'], 'never', T['never'], 'added sides', len(added))
for a in added: print(a)
