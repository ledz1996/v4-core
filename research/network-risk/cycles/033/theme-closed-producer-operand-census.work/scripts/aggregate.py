"""Aggregates the census lines of one validator run.
Line format: block op class codeAddress pc count origin a b c.
Only blocks whose result is 'validated' in results.jsonl count. Usage: aggregate.py <run dir> <pm address> <out json>"""
import json, sys, os
d, pm, out = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
st = {}
for l in open(os.path.join(d, 'results.jsonl')):
    r = json.loads(l); st[r['block']] = r['status']
ok = {b for b, s in st.items() if s == 'validated'}
cls = {}; pmk = {}; skipped = 0; blocks_seen = set()
for l in open(os.path.join(d, 'census.txt')):
    p = l.split()
    bn = int(p[0])
    if bn not in ok: skipped += 1; continue
    blocks_seen.add(bn)
    op, c, ad, pc, n = int(p[1]), int(p[2]), p[3], int(p[4]), int(p[5])
    k = '%d:%d' % (op, c)
    v = cls.get(k)
    if v is None:
        v = cls[k] = {'occ': 0, 'blocks': set(), 'contracts': set(), 'first': bn, 'last': bn, 'example': None}
    v['occ'] += n; v['blocks'].add(bn); v['contracts'].add(ad)
    v['first'] = min(v['first'], bn)
    if bn >= v['last'] or v['example'] is None:
        v['last'] = max(v['last'], bn)
        if v['example'] is None or bn >= v['example']['block']:
            v['example'] = {'block': bn, 'contract': ad, 'pc': pc, 'origin': p[6], 'a': p[7], 'b': p[8], 'c': p[9]}
    if ad == pm:
        kk = '%d:%d:%d' % (op, c, pc)
        w = pmk.get(kk)
        if w is None:
            w = pmk[kk] = {'occ': 0, 'blocks': set(), 'first': bn, 'last': bn, 'example': None}
        w['occ'] += n; w['blocks'].add(bn); w['first'] = min(w['first'], bn); w['last'] = max(w['last'], bn)
        if w['example'] is None or bn >= w['example']['block']:
            w['example'] = {'block': bn, 'origin': p[6], 'a': p[7], 'b': p[8], 'c': p[9]}
for v in cls.values():
    v['blocks'] = sorted(v['blocks']); v['nblocks'] = len(v['blocks']); v['ncontracts'] = len(v['contracts']); del v['contracts']
for w in pmk.values():
    w['nblocks'] = len(w['blocks']); w['blocks'] = sorted(w['blocks'])[-50:]
for v in cls.values():
    v['blocksSample'] = v['blocks'][-50:]; del v['blocks']
res = {'run': os.path.basename(d.rstrip('/')), 'listed': len(st), 'validated': len(ok),
       'notValidated': {str(b): s for b, s in st.items() if s != 'validated'},
       'blocksWithCensusLines': len(blocks_seen), 'linesSkipped': skipped,
       'clientBefore': open(os.path.join(d, 'client-before.json')).read() if os.path.exists(os.path.join(d, 'client-before.json')) else None,
       'clientAfter': open(os.path.join(d, 'client-after.json')).read() if os.path.exists(os.path.join(d, 'client-after.json')) else None,
       'classes': cls, 'pm': pmk}
json.dump(res, open(out, 'w'))
print(res['run'], res['listed'], res['validated'], len(cls), len(pmk), skipped)
