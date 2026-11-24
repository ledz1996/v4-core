import sys, json, collections
f = sys.argv[1]; rs = [json.loads(l) for l in open(f)]
c = collections.Counter()
for r in rs:
    if 'error' in r: c['error'] += 1; continue
    if 'setAside' in r: c['setAside:' + r['setAside'][:50]] += 1; continue
    c['rerun'] += 1
    c['statusEq'] += r['status'][0] == r['status'][1]
    c['logsEq'] += r['logs'][2]; c['framesEq'] += r['frames'][2]
    if 'storageVsDiff' in r: c['stDiffChecked'] += 1; c['stDiffEq'] += r['storageVsDiff'][2]
    if 'storageVsBlock' in r: c['stBlockChecked'] += 1; c['stBlockEq'] += r['storageVsBlock'][1]
    if r.get('nMisses'): c['withMisses'] += 1
print(dict(c))
errs = collections.Counter(r['error'][:90] for r in rs if 'error' in r); print(errs.most_common(5))
bad = [r['tx'] for r in rs if 'status' in r and not (r['logs'][2] and r['frames'][2] and r['status'][0] == r['status'][1] and r.get('storageVsDiff', [0, 0, True])[2] and r.get('storageVsBlock', [0, True])[1])]
print('mismatch', len(bad), bad[:5])
