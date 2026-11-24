"""Parallel eth_getLogs over [lo, hi] in fixed spans, PoolManager address, optional topic0 list. Read only.
Usage: pcollect.py <chainId> <lo> <hi> <span> <threads> <out.jsonl> <topicset: rare|swap|all> [url,url]"""
import sys, json, os, concurrent.futures as cf, itertools, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/013/theme-mined-branches.work')
from common import EV, NETS, URLS, _rpc
cid, lo, hi, span, th, out, ts = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6], sys.argv[7]
urls = sys.argv[8].split(',') if len(sys.argv) > 8 else URLS[cid]
pm = NETS[cid]['poolManager']
names = {'rare': ('Donate', 'Approval', 'OperatorSet', 'Initialize', 'Transfer6909', 'ProtocolFeeUpdated'), 'swap': ('Swap',), 'all': None}[ts]
topics = [[k for k, v in EV.items() if v in names]] if names else []
done = set()
if os.path.exists(out):
    for line in open(out):
        try: done.add(json.loads(line)['a'])
        except Exception: pass
ranges = [a for a in range(lo, hi + 1, span) if a not in done]
cnt = itertools.count()
def one(a):
    b = min(hi, a + span - 1)
    for k in range(12):
        u = urls[next(cnt) % len(urls)]
        try:
            r = _rpc(u, 'eth_getLogs', [{'address': pm, 'topics': topics, 'fromBlock': hex(a), 'toBlock': hex(b)}], timeout=60)
            return {'a': a, 'b': b, 'logs': [{'tx': l['transactionHash'], 'b': int(l['blockNumber'], 16), 'i': int(l['transactionIndex'], 16), 'li': int(l['logIndex'], 16), 'topics': l['topics'], 'data': l['data']} for l in r]}
        except Exception as e:
            time.sleep(1 + k)
    return {'a': a, 'b': b, 'error': True}
f = open(out, 'a'); t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(th) as ex:
    for r in ex.map(one, ranges):
        if r.get('error'): print('ERR', r['a'], flush=True); continue
        f.write(json.dumps(r) + '\n'); n += 1
        if n % 500 == 0: print(n, len(ranges), round(time.time() - t0), flush=True)
print('finished', n, len(ranges), flush=True)
