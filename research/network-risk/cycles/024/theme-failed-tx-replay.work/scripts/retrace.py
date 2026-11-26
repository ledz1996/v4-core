"""Task 4b, exact form (cycle 24, theme-failed-tx-replay): re-execute each stored failed transaction at its own position with
debug_traceTransaction callTracer on a second endpoint, and compare every PoolManager frame (order, input, output, error) and the root
result with the stored trace. usage: retrace.py <cid> <url> <N> <seed>. Read-only. Writes results/retrace-<cid>.json and .jsonl."""
import json, os, sys, gzip, glob, random, time, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS
cid = int(sys.argv[1]); url = sys.argv[2]; N = int(sys.argv[3]); seed = int(sys.argv[4]); PM = NETS[cid]['poolManager'].lower()
HERE = os.path.dirname(os.path.abspath(__file__)); D = HERE + '/../raw/%d' % cid
recs = [r for r in (json.load(gzip.open(f)) for f in sorted(glob.glob(D + '/tx/*.json.gz'))) if r.get('kind') == 'failed']
rng = random.Random(seed); recs = recs if len(recs) <= N else rng.sample(recs, N)
def pmf(f, acc):
    if (f.get('to') or '').lower() == PM: acc.append(((f.get('input') or '')[:10], (f.get('input') or '')[10:], f.get('output') or '', f.get('error'), f.get('type')))
    for c in f.get('calls', []) or []: pmf(c, acc)
    return acc
v0, e0 = call(url, 'web3_clientVersion', [], 30)
out = open(HERE + '/../results/retrace-%d.jsonl' % cid, 'w'); cnt = collections.Counter()
for r in recs:
    for k in range(5):
        ct, e = call(url, 'debug_traceTransaction', [r['hash'], {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], 120)
        if ct is not None or not ('429' in (e or '') or 'EXC' in (e or '') or 'HTTP 5' in (e or '')): break
        time.sleep(3 + 3 * k)
    if ct is None: cnt['endpoint-error'] += 1; out.write(json.dumps({'hash': r['hash'], 'err': (e or '')[:300]}) + '\n'); continue
    a = pmf(r['call'], []); b = pmf(ct, [])
    same_root = (r['call'].get('error') == ct.get('error') or bool(r['call'].get('error')) == bool(ct.get('error'))) and (r['call'].get('output') or '') == (ct.get('output') or '')
    cls = 'identical' if a == b and same_root else 'different'
    cnt[cls] += 1; cnt['pmFrames'] += len(a)
    rec = {'hash': r['hash'], 'class': cls, 'pmFrames': len(a), 'rootError': [r['call'].get('error'), ct.get('error')]}
    if cls == 'different': rec['first'] = next(([x, y] for x, y in zip(a, b) if x != y), [a[len(b):][:1], b[len(a):][:1]]); rec['roots'] = [(r['call'].get('output') or '')[:300], (ct.get('output') or '')[:300]]
    out.write(json.dumps(rec) + '\n')
v1, e1 = call(url, 'web3_clientVersion', [], 30)
summ = {'chainId': cid, 'url': url, 'clientBefore': v0, 'clientAfter': v1, 'firstEndpoints': sorted(set(r.get('url') for r in recs)), 'n': len(recs), 'seed': seed, 'classes': dict(cnt)}
json.dump(summ, open(HERE + '/../results/retrace-%d.json' % cid, 'w'), indent=1); print(json.dumps(summ))
