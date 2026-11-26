"""Summary of theme-replay-eleven raw results (cycle 24). Writes raw/summary.json.
Traced networks: run.py result.json and every mismatch record classified as in cycle 23 (wrapped native deposits,
interest-bearing rounding, rebasing token, token without Transfer log), anything else unexplained.
Parent-storage networks: lazy_*.jsonl records classified as match, match after block prefix, PoolManager part equal and only
logs of other contracts differ (named by emitting contract), not modelled (reason), error, or differing in a PoolManager log,
status, storage word or native balance."""
import json, glob, collections, os, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'raw')
def J(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
out = {'traced': {}, 'lazy': {}}
for d in sorted(glob.glob(R + '/*/result.json')):
    c = d.split('/')[-2]; r = J(d); cls = collections.Counter(); unexp = []
    for l in open(os.path.dirname(d) + '/mismatches.jsonl'):
        x = json.loads(l)
        for m in x['mismatches']:
            k = m['kind']
            if k == 'erc20-flow':
                if m['logsOut'] == m['take'] + m['collect'] and 0 < m['paid'] - (m['logsIn'] - m['logsOut'] + m['take'] + m['collect']) <= 2:
                    cls['interest-bearing token: balanceOf rose 1 or 2 units more than the Transfer amount'] += 1; continue
            unexp.append({'hash': x['hash'], 'block': x['block'], 'mismatch': m, 'actions': x.get('actions', [])[:10]})
    out['traced'][c] = {'result': r, 'explained': dict(cls), 'unexplained': unexp}
def lazycls(r):
    if r.get('error'): return 'error: ' + r['error'][:60]
    if r.get('unsupported'): return 'not modelled: ' + r['unsupported'][:50]
    if r.get('match'): return 'match'
    p = r.get('prefix')
    if isinstance(p, dict):
        if p.get('unsupported'): q = p
        elif p.get('match'): return 'match after block prefix'
        else: q = p
    else: q = r
    if q.get('unsupported'): return 'prefix not modelled: ' + q['unsupported'][:50]
    pmok = q.get('statusChain') == q.get('statusRef') and q.get('pmLogsEqual') and not q.get('pmSlotMismatch') and q.get('pmNativeEqual') is not False
    if pmok:
        em = sorted({x[0][:10] for x in (q.get('logMismatch') or {}).get('chain', []) + (q.get('logMismatch') or {}).get('ref', [])})
        return 'PoolManager status, logs, words and balance equal; other logs differ: ' + ','.join(em)
    return 'DIFFERS in PoolManager part' + (' (' + p + ')' if isinstance(p, str) else '')
for c in sorted({f.split('/')[-2] for f in glob.glob(R + '/*/lazy_*.jsonl')}):
    rs = {}
    for f in sorted(glob.glob(R + '/%s/lazy_*.jsonl' % c), key=lambda f: ('rerun' in f, 'differs' in f, f)):  # reruns of differing or unfinished records override the first run
        for l in open(f):
            x = json.loads(l); rs[x['tx']] = x
    cls = collections.Counter(lazycls(x) for x in rs.values())
    ran = [x for x in rs.values() if not x.get('error') and not x.get('unsupported')]
    agg = {'records': len(rs), 'classes': dict(cls), 'ran': len(ran),
           'pmSlotsCompared': sum(x.get('pmSlotsCompared', 0) for x in ran), 'txWithSlotsCompared': sum(1 for x in ran if 'pmSlotsCompared' in x),
           'logsCompared': sum(x.get('logsChain', 0) for x in ran), 'pmLogs': sum(x.get('pmLogs', 0) for x in ran),
           'nativeCompared': sum(1 for x in ran if 'pmNativeEqual' in x), 'nativeMoved': sum(1 for x in ran if x.get('pmNativeDeltaChain') not in (None, '0')),
           'creates': sum(x.get('creates', 0) for x in ran), 'p256': sum(x.get('p256', 0) for x in ran), 'mints': sum(x.get('mints', 0) for x in ran),
           'blocks': [min((x['block'] for x in rs.values()), default=None), max((x['block'] for x in rs.values()), default=None)],
           'differs': [x for x in rs.values() if lazycls(x).startswith('DIFFERS')]}
    out['lazy'][c] = agg
json.dump(out, open(R + '/summary.json', 'w'), indent=1)
for c, v in out['traced'].items(): print('traced', c, v['result']['txs'], v['result']['wordsCompared'], v['explained'], len(v['unexplained']))
for c, v in out['lazy'].items(): print('lazy', c, v['records'], v['classes'], 'differs', len(v['differs']))
