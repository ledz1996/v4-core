"""Cycle 25: fetch prestateTracer (plain, diffMode) and callTracer withLog for transactions, record format of cycle 23/24 fetchtx.py.
Threaded. Brackets the run with web3_clientVersion. usage: fetchtx.py <pm> <url> <outdir> <hashfile> [threads]"""
import sys, json, gzip, os, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
PM = sys.argv[1].lower(); u = sys.argv[2]; od = sys.argv[3]; os.makedirs(od, exist_ok=True)
hs = [l.strip() for l in open(sys.argv[4]) if l.strip()]; th = int(sys.argv[5]) if len(sys.argv) > 5 else 6
def keep(x): return {k: v for k, v in (x or {}).items() if k.lower() == PM}
def c(m, p, t):
    for i in range(6):
        r, e = call(u, m, p, t)
        if not e or ('429' not in e and 'rate' not in e.lower() and 'EXC' not in e): return r, e
        time.sleep(3 * (i + 1))
    return r, e
def one(h):
    if os.path.exists('%s/%s.json.gz' % (od, h)): return {'hash': h, 'errors': [], 'cached': True}
    rc, e0 = c('eth_getTransactionReceipt', [h], 60)
    diff, e1 = c('debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True, 'disableCode': True}}], 120)
    pre, e2 = c('debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'disableCode': True}}], 120)
    ct, e3 = c('debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], 120)
    errs = [e for e in (e0, e1, e2, e3) if e]
    if errs: return {'hash': h, 'errors': errs}
    rec = {'hash': h, 'block': int(rc['blockNumber'], 16), 'index': int(rc['transactionIndex'], 16), 'url': u, 'status': rc['status'],
           'diff': {'pre': keep(diff.get('pre')), 'post': keep(diff.get('post'))}, 'pre': keep(pre), 'call': ct, 'receiptLogs': rc['logs']}
    json.dump(rec, gzip.open('%s/%s.json.gz' % (od, h), 'wt')); return {'hash': h, 'errors': []}
a = call(u, 'web3_clientVersion', [], 30); t0 = time.time()
with ThreadPoolExecutor(th) as ex: log = list(ex.map(one, hs))
b = call(u, 'web3_clientVersion', [], 30)
json.dump({'url': u, 'clientBefore': a, 'clientAfter': b, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'secs': time.time() - t0, 'txs': log}, open('%s/../fetch-%d.json' % (od, int(time.time())), 'w'), indent=1)
print(len(log), sum(1 for x in log if x['errors']), a, b)
