"""Task 2: group caught PoolManager frames (error set, outer tx successful) in the cycle 23 replay raw data by revert output, selector of the call, and error string."""
import json, gzip, os, sys, collections
cid = int(sys.argv[1])
D = '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/%d/tx' % cid
w = json.load(open('/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/%d/window.json' % cid))
PM = w['poolManager'].lower()
groups = collections.Counter(); txs = collections.defaultdict(set); ex = {}
ntx = 0; ntxr = 0
def walk(f, h, depth, path):
    global found
    to = f.get('to', '').lower()
    if to == PM and f.get('error'):
        key = (f.get('input', '')[:10], f.get('error'), (f.get('output') or '')[:10+64*0], f.get('type'))
        groups[key] += 1; txs[key].add(h); ex.setdefault(key, (h, f.get('output'), f.get('gas'), f.get('gasUsed'), path))
        found = True
    for i, c in enumerate(f.get('calls', []) or []):
        walk(c, h, depth + 1, path + [i])
for fn in os.listdir(D):
    r = json.load(gzip.open(os.path.join(D, fn)))
    ntx += 1; found = False
    walk(r['call'], r['hash'], 0, [])
    if found: ntxr += 1
out = {'chainId': cid, 'txs': ntx, 'txsWithRevertedPmFrame': ntxr,
       'groups': [{'selector': k[0], 'error': k[1], 'outputHead': k[2], 'type': k[3], 'frames': n, 'txs': len(txs[k]), 'example': ex[k]} for k, n in groups.most_common()]}
json.dump(out, open('/home/user/v4-core/research/network-risk/cycles/024/theme-failed-tx-replay.work/results/caught-%d.json' % cid, 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('txs', 'txsWithRevertedPmFrame')}))
for g in out['groups'][:25]: print(g['selector'], g['error'], g['outputHead'], g['type'], g['frames'], g['txs'], g['example'][0], g['example'][2], g['example'][3])
