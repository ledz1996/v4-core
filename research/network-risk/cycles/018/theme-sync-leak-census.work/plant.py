"""Planted-fault check of census.py's model on real MegaETH traces: (a) drop each transaction's first completed ERC-20
sync frame, which must make the following settle disagree; (b) drop its last completed settle, which must leave an
ERC-20 synced at the end. Read only. Usage: plant.py <census.jsonl> <n> <seed> <url>"""
import sys, json, random, copy
src = open('census.py').read().split('txs = json.load(open(lst))')[0]
fn, n, seed, url = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.argv = ['x', '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e', '/dev/null', '1', '/dev/null', url]; g = {}; exec(src, g)
Z = '0x' + '0' * 40
rows = [json.loads(l) for l in open(fn)]
cand = [r['tx'] for r in rows if r.get('ok') and any(f[0] == 'sync' and f[1] != Z and not f[3] for f in r['frames'])]
pick = random.Random(seed).sample(cand, n); a = b = base = 0
for h in pick:
    t = g['rpc']('debug_traceTransaction', [h, {'tracer': 'callTracer'}]); acc = []; g['walk'](t, acc)
    s0, bad0, _ = g['model'](acc); base += (not bad0 and s0 is None)
    i = next(i for i, f in enumerate(acc) if f['sel'] == 'sync' and f['arg'] != Z and not f['rev'])
    x = acc[:i] + acc[i + 1:]; a += bool(g['model'](x)[1])
    j = max((i for i, f in enumerate(acc) if f['sel'] in ('settle', 'settleFor') and not f['rev']), default=None)
    if j is not None:
        y = acc[:j] + acc[j + 1:]; s, _, _ = g['model'](y); b += bool(s and s != Z) or bool(g['model'](y)[1])
print(json.dumps({'seed': seed, 'n': n, 'cleanBaseline': base, 'droppedSyncDetected': a, 'droppedLastSettleDetected': b}))
