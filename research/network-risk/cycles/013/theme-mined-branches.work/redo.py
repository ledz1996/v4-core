"""Replay again, with the current pmreplay.py, every row of a jsonl that did not match or failed; rewrite the file."""
import sys, json
ARGV = list(sys.argv)
from pmreplay import pmreplay
from report import ok
cid, f = int(ARGV[1]), ARGV[2]
rows = [json.loads(l) for l in open(f)]; lst = {x[0]: x[1] for x in json.load(open(ARGV[3]))}
n = 0
for i, r in enumerate(rows):
    if 'error' in r or 'setAside' in r or 'frames' not in r or not ok(r):
        try: rows[i] = pmreplay(cid, r['tx'], bool(lst.get(r['tx'], 0)))
        except Exception as e: rows[i] = {'tx': r['tx'], 'error': str(e)[:200]}
        n += 1
open(f, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print('redone', n)
