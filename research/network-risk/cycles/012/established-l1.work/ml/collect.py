"""Collect mined ModifyLiquidity events of the PoolManager, newest first.
Usage: collect.py <chainId> <span> <max_calls> <want_nonpositive> <out.json>"""
import sys, json, concurrent.futures as cf
from lib import *
cid, span, max_calls, want, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
pm = NETS[cid]['poolManager']
import os
head = int(os.environ["HI"]) if os.environ.get("HI") else int(rpc(cid, "eth_blockNumber", []), 16) - 3
logs = []; hi = head; calls = 0; par = int(sys.argv[6]) if len(sys.argv) > 6 else 1
def fetch(r):
    lo, hi = r
    return rpc(cid, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [MOD]}])
with cf.ThreadPoolExecutor(par) as ex:
    while calls < max_calls and hi > 0:
        ranges = []
        for _ in range(par):
            lo = max(0, hi - span + 1); ranges.append((lo, hi)); hi = lo - 1
            if hi <= 0: break
        calls += len(ranges)
        for part in ex.map(fetch, ranges): logs += part
        nonpos = sum(1 for l in logs if s256(int(l['data'][2+64*2:2+64*3], 16)) <= 0)
        if calls % (par * 10) == 0: print(cid, 'calls', calls, 'lo', hi + 1, 'logs', len(logs), 'nonpos', nonpos, flush=True)
        if nonpos >= want: break
json.dump({'chainId': cid, 'head': head, 'lo': hi + 1, 'calls': calls, 'logs': logs}, open(out, 'w'))
print(cid, 'done calls', calls, 'range', hi + 1, head, 'logs', len(logs), 'nonpos', nonpos)
