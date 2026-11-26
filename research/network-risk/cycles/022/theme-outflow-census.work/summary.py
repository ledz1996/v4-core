"""Join census3 and reclass outputs into raw/summary.json: per chain, the covered block ranges (complete or partial),
transaction and row counts, flagged rows and their classes, and every row that no class explains. No RPC."""
import json, gzip, glob, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for fn in sorted(glob.glob(os.path.join(HERE, 'raw', 'census3_*.json.gz'))):
    d = json.load(gzip.open(fn)); c = str(d['chainId']); e = out.setdefault(c, {'ranges': [], 'txs': 0, 'counts': collections.Counter(), 'fails': collections.Counter(), 'endpoint': set(), 'clientVersion': set()})
    e['ranges'].append([d['B1'], d['B2'], d['wantB2'], os.path.basename(fn), 'partial' if d['B2'] < d['wantB2'] else 'complete'])
    e['txs'] += d['txs']; e['counts'].update(d['counts']); e['fails'].update(d['fails']); e['endpoint'].add(d['url'])
    e['clientVersion'].add(d['clientVersionStart'][1]);
    if d.get('clientVersionEnd'): e['clientVersion'].add(d['clientVersionEnd'][1])
cls = collections.defaultdict(collections.Counter); open_rows = collections.defaultdict(list); classified = collections.Counter(); byTok = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for fn in sorted(glob.glob(os.path.join(HERE, 'raw', 'reclass_*.json.gz'))):
    d = json.load(gzip.open(fn)); c = str(d['chainId'])
    for r in d['rows']:
        k = r.get('refined', r.get('cls')); cls[c][k] += 1; classified[c] += 1; byTok[c][k][r['token']] += 1
        if k not in ('fees', 'accrual', 'surplus'):
            open_rows[c].append({x: r.get(x) for x in ('tx', 'block', 'token', 'out', 'in', 'mint', 'burn', 'owed', 'excess', 'poolEvents', 'sender', 'txTo', 'recipient', 'b0', 'b1', 'resid', 'cls', 'refined', 'why')} | {'trace': r.get('trace')})
for c, e in out.items():
    e['ranges'].sort(); e['counts'] = dict(e['counts']); e['fails'] = dict(e['fails']); e['endpoint'] = sorted(e['endpoint']); e['clientVersion'] = sorted(e['clientVersion'])
    e['classes'] = dict(cls.get(c, {})); e['classified'] = classified.get(c, 0); e['notFeesOrAccrual'] = open_rows.get(c, [])
    e['tokensByClass'] = {k: dict(v) for k, v in byTok.get(c, {}).items() if k != 'fees'}
json.dump(out, open(os.path.join(HERE, 'raw', 'summary.json'), 'w'), indent=1)
for c, e in out.items():
    print(c, 'txs', e['txs'], 'flagged', e['counts'].get('flagged', 0), 'classified', e['classified'], e['classes'], 'fails', e['fails'], 'open', len(e['notFeesOrAccrual']))
    for r in e['ranges']: print('   ', r)
