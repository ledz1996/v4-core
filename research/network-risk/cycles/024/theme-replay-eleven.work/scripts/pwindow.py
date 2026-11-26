"""Parallel version of collect.py's window step (cycle 24), for networks whose log endpoints cap a query at a few thousand
blocks. Same output format as collect.py window.json: newest <target> PoolManager transactions with a log, newest first.
usage: pwindow.py <cid> <span> <target> <threads> <url> [url ...]"""
import sys, json, time, threading
from rpcu import call
from eps import NETS
cid, span, target, nth = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); urls = sys.argv[5:]
PM = NETS[cid]['poolManager'].lower(); D = '../raw/%d' % cid
head = int(call(urls[0], 'eth_blockNumber', [])[0], 16) - 2
res = {}; lock = threading.Lock(); nxt = [head]; stop = [False]; errs = []
def wk(n):
    while not stop[0]:
        with lock:
            hi = nxt[0]; nxt[0] -= span
        if hi < 0: return
        lo = max(0, hi - span + 1)
        for k in range(10):
            r, e = call(urls[(n + k) % len(urls)], 'eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi)}], 90)
            if e is None: break
            with lock: errs.append([lo, hi, e[:150]])
            time.sleep(1 + k)
        with lock: res[hi] = r or []
def count_contig():
    txs = {}; h = head; low = None
    while h in res:
        for l in res[h]: txs.setdefault(l['transactionHash'], [int(l['blockNumber'], 16), int(l['transactionIndex'], 16)])
        low = h - span + 1; h -= span
    return txs, low
th = [threading.Thread(target=wk, args=(n,)) for n in range(nth)]; [t.start() for t in th]
while True:
    time.sleep(10)
    txs, low = count_contig()
    print(len(txs), low, len(errs), flush=True)
    if len(txs) >= target or (low is not None and low <= 0): stop[0] = True; break
[t.join() for t in th]
txs, low = count_contig()
order = sorted(txs.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))[:target]
blocks = [v[0] for _, v in order]
json.dump({'chainId': cid, 'poolManager': PM, 'head': head, 'logEndpoints': urls, 'logsRead': sum(len(v) for v in res.values()), 'scannedDownTo': low,
           'firstBlock': min(blocks), 'lastBlock': max(blocks), 'txs': [[h, v[0], v[1]] for h, v in order], 'complete': low is not None and low <= 0,
           'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'parallelScan': True, 'errors': errs[:50]}, open(D + '/window.json', 'w'))
print('window', len(order), min(blocks), max(blocks))
