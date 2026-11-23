import sys, json, gzip, collections
c = int(sys.argv[1]); tag = sys.argv[2] if len(sys.argv) > 2 else '_c2'
d = json.load(gzip.open('raw/reread_%d%s.json.gz' % (c, tag)))
by = collections.defaultdict(list)
for r in d['rows']:
    if r['cls'] not in ('fees', 'balanced'): by[(r['cls'], r['token'])].append(r)
for (cls, tok), v in sorted(by.items(), key=lambda x: (x[0][0], -len(x[1]))):
    r = v[0]; tr = r.get('trace') or {}
    print(c, cls, tok, 'rows', len(v), 'eg out', r.get('out'), 'in', r.get('in'), 'mint', r.get('mint'), 'burn', r.get('burn'), 'owed', r.get('owed'), 'excess', r.get('excess'), 'b0', r.get('b0'), 'b1', r.get('b1'), 'resid', r.get('resid'),
          '| takes', sum(a for _, a in tr.get('takes', [])) if tr else None, 'paid', tr.get('paid'), 'trig', [(x['to'][:12], x['selector']) for x in (tr.get('betweenSyncAndSettle') or [])[:3]], 'top', (tr.get('top') or {}).get('to'), (tr.get('top') or {}).get('selector'), '|', r.get('kind', ''), r.get('why'), '|', r['tx'], 'poolEv', r.get('poolEvents'))
