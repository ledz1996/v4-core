"""Every PoolManager log in [lo, hi], adaptive span. Read only.
Usage: collect.py <chainId> <url> <lo> <hi> <out.json>"""
import sys, json
from common import *
cid, url, lo, hi, out = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
pm = NETS[cid]['poolManager']; logs = []; a = lo; span = 5000; n = 0
while a <= hi:
    b = min(hi, a + span - 1)
    try:
        r = rpc([url], 'eth_getLogs', [{'address': pm, 'fromBlock': hex(a), 'toBlock': hex(b)}], tries=3)
        logs += [{'tx': l['transactionHash'], 'b': int(l['blockNumber'], 16), 'i': int(l['transactionIndex'], 16), 'li': int(l['logIndex'], 16), 'topics': l['topics'], 'data': l['data']} for l in r]
        a = b + 1; n += 1
        if len(r) < 2000 and span < 200000: span *= 2
        if n % 50 == 0: print(cid, a, hi, len(logs), span, flush=True)
    except Exception as e:
        if span <= 5: raise
        span = max(5, span // 4)
json.dump({'chainId': cid, 'lo': lo, 'hi': hi, 'logs': logs}, open(out, 'w'))
print('done', cid, len(logs), len({l['tx'] for l in logs}))
