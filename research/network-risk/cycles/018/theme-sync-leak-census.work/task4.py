"""Zero-value failed PoolManager calls on MegaETH before block 31,861,608 from the Blockscout v2 internal transaction
samples (raw/itx.jsonl, raw/itxseg*/), with the block ranges that were read completely, joined with the census traces.
Usage: task4.py <out.json>"""
import json, glob, sys, collections
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'; LIMIT = 31861608
rows_by_tx = {}
files = ['raw/itx.jsonl'] + sorted(glob.glob('raw/itxseg/itxseg-*.jsonl')) + sorted(glob.glob('raw/itxseg3/itxseg-*.jsonl'))
for f in files:
    per = collections.defaultdict(list)
    for l in open(f):
        r = json.loads(l); r['from'] = (r['from'] or '').lower(); r['to'] = (r['to'] or '').lower(); per[r['tx']].append(r)
    for h, rs in per.items():
        if h not in rows_by_tx: rows_by_tx[h] = rs          # one file per transaction, so a re-read boundary block is not counted twice
ranges = [[31795945, LIMIT]]  # raw/itx.jsonl, the continuation of cycle 17's pager (4,000 items)
for sf in ['raw/itxseg/itxseg-summary.json', 'raw/itxseg/itxseg-summary-pass2.json', 'raw/itxseg3/itxseg-summary-pass2.json']:
    try: S = json.load(open(sf))
    except Exception: continue
    for s in S['segments']: ranges.append([s['floor'] + 1 if s['reachedFloor'] else s['lowestReached'], s['top']])
ranges.sort(); merged = []
for a, b in ranges:
    if merged and a <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
census = {}
for f in glob.glob('raw/census-4326*.jsonl'):
    for l in open(f):
        j = json.loads(l)
        if 'fail' not in j: census[j['tx']] = j
fz = [(h, r) for h, rs in rows_by_tx.items() for r in rs if r['to'] == PM and r['ok'] is False and str(r['v']) == '0' and r['b'] < LIMIT]
txs = sorted({h for h, _ in fz}); blocks = sorted({r['b'] for _, r in fz})
errs = collections.Counter(r['err'] for _, r in fz)
traced = [census[h] for h in txs if h in census]
sel = collections.Counter(f[0] for t in traced for f in t['frames'] if f[3])
top_failed = sum(1 for t in traced if not t['ok'])
leak = [t['tx'] for t in traced if t['ok'] and t['endSynced'] and t['endSynced'] != '0x' + '0' * 40]
mism = [t['tx'] for t in traced if t['bad']]
res = {'coveredRanges': merged, 'coveredBlocks': sum(b - a + 1 for a, b in merged if a < LIMIT), 'framesRead': sum(len(v) for v in rows_by_tx.values()),
       'txsRead': len(rows_by_tx), 'zeroValueFailedCallsIntoPM': len(fz), 'theirTxs': len(txs), 'theirBlocks': len(blocks), 'errors': errs.most_common(),
       'traced': len(traced), 'tracedTopLevelFailed': top_failed, 'revertedPMFramesBySelector': sel.most_common(), 'endsSynced': leak, 'settleMismatch': mism,
       'blocks': blocks, 'txs': txs}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print({k: v for k, v in res.items() if k not in ('blocks', 'txs')})
