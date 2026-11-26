"""Task 2: for every PoolManager frame with an error in the cycle 23 raw traces (successful outer transactions),
find where the revert started: the innermost frame on the erroring chain whose own output is the same bytes.
Classes: callback (started in the caller's unlockCallback code, bubbled by PoolManager.unlock), pm-own (started in a
PoolManager frame with no erroring child carrying the same output), external (a token or hook frame below the PoolManager),
other (error string other than 'execution reverted'). Writes results/origin-<cid>.json with every frame record."""
import json, gzip, os, sys, collections
sel = json.load(open(os.path.dirname(__file__) + '/../results/selectors.json'))
cid = int(sys.argv[1])
R = '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/%d' % cid
PM = json.load(open(R + '/window.json'))['poolManager'].lower()
recs = []; errs = collections.Counter(); ntx = 0; txs = set()
def origin(f):
    out = f.get('output') or ''
    for c in f.get('calls', []) or []:
        if c.get('error') and (c.get('output') or '') == out:
            return origin(c)
    return f
def walk(f, h, b):
    if f.get('to', '').lower() == PM and f.get('error'):
        o = origin(f)
        out = f.get('output') or ''
        s = out[:10]
        cls = 'other' if f.get('error') != 'execution reverted' else (
              'pm-own' if o is f or o.get('to', '').lower() == PM else
              'callback' if (o.get('to', '').lower() == f.get('from', '').lower()) or (o.get('type') == 'DELEGATECALL') else 'external')
        recs.append({'tx': h, 'block': b, 'pmSelector': f.get('input', '')[:10], 'from': f.get('from'), 'error': f.get('error'), 'output': out,
                     'decoded': sel.get(s, [None])[0], 'origin': {'to': o.get('to'), 'type': o.get('type'), 'input4': (o.get('input') or '')[:10], 'error': o.get('error')},
                     'class': cls, 'gas': f.get('gas'), 'gasUsed': f.get('gasUsed')})
        txs.add(h); errs[f.get('error')] += 1
    for c in f.get('calls', []) or []: walk(c, h, b)
for fn in os.listdir(R + '/tx'):
    r = json.load(gzip.open(R + '/tx/' + fn)); ntx += 1
    walk(r['call'], r['hash'], r['block'])
by = collections.Counter((r['class'], r['pmSelector'], r['output'][:10], r['decoded']) for r in recs)
summ = {'chainId': cid, 'txs': ntx, 'txsWithCaughtPmRevert': len(txs), 'frames': len(recs), 'errorStrings': dict(errs),
        'groups': [{'class': k[0], 'pmSelector': k[1], 'revertSelector': k[2], 'decoded': k[3], 'frames': n} for k, n in by.most_common()]}
json.dump({'summary': summ, 'frames': recs}, open(os.path.dirname(__file__) + '/../results/origin-%d.json' % cid, 'w'))
print(json.dumps(summ))
