"""PoolManager-only replay (pmreplay.py) of a list of transactions. Usage: runmany.py <chainId> <list.json> <out.jsonl> <threads>
list: [[txhash, lastInBlock(0/1)], ...]; already finished hashes in out.jsonl are skipped."""
import sys, json, os, concurrent.futures as cf, traceback
from pmreplay import pmreplay as rerun
cid, lst, out, th = int(sys.argv[1]), json.load(open(sys.argv[2])), sys.argv[3], int(sys.argv[4])
done = set()
if os.path.exists(out):
    for line in open(out):
        try: done.add(json.loads(line)['tx'])
        except Exception: pass
todo = [x for x in lst if x[0] not in done]
print('todo', len(todo), 'done', len(done), flush=True)
f = open(out, 'a')
def one(x):
    try: return rerun(cid, x[0], bool(x[1]))
    except Exception as e: return {'tx': x[0], 'error': str(e)[:200]}
with cf.ThreadPoolExecutor(th) as ex:
    for i, r in enumerate(ex.map(one, todo)):
        f.write(json.dumps(r) + '\n'); f.flush()
        if i % 100 == 0: print(i, len(todo), flush=True)
print('finished', flush=True)
