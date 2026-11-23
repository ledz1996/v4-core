# Re-read of every flagged row of a census file with rule.classify. usage: python3 reread.py <chainId> <census file> <out tag> [workers]
import sys, json, gzip, collections
from concurrent.futures import ThreadPoolExecutor
import rule
cid = int(sys.argv[1]); d = json.load(gzip.open(sys.argv[2])); rows = d.get('unexplained') or d.get('flagged') or []
pairs = sorted({(u['tx'], u['token'], int(u.get('owed') or 0)) for u in rows})
import os
OUT = 'raw/reread_%d%s.json.gz' % (cid, sys.argv[3]); keep = {}
if os.path.exists(OUT) and os.environ.get('RETRY'):
    for r in json.load(gzip.open(OUT))['rows']:
        if r['cls'] not in ('unread', 'error') and (r.get('b0') is not None or r.get('native')): keep[(r['tx'], r['token'])] = r
    print('kept', len(keep), 'of', len(pairs), flush=True)
def one(x):
    if (x[0], x[1]) in keep: return keep[(x[0], x[1])]
    try: return rule.classify(cid, x[0], x[1], owed=x[2])
    except Exception as e: return dict(tx=x[0], token=x[1], cls='error', why=repr(e)[:200])
with ThreadPoolExecutor(int(sys.argv[4]) if len(sys.argv) > 4 else 4) as ex: res = list(ex.map(one, pairs))
json.dump(dict(chainId=cid, source=sys.argv[2], rows=res), gzip.open('raw/reread_%d%s.json.gz' % (cid, sys.argv[3]), 'wt'))
print(cid, 'rows', len(res), dict(collections.Counter(r['cls'] for r in res)), 'tokens', len({r['token'] for r in res}), flush=True)
by = collections.defaultdict(collections.Counter)
for r in res: by[r['token']][r['cls']] += 1
for t, c in sorted(by.items(), key=lambda x: -sum(x[1].values()))[:40]: print('  ', t, dict(c))
