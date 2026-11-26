"""Fetch prestateTracer (plain and diffMode) and callTracer withLog for given transactions, in the record format of cycle 23
collect.py (PoolManager account only from the prestate results). Brackets each batch with web3_clientVersion.
usage: fetchtx.py <cid> <url> <outdir> <hash>...   writes <outdir>/<hash>.json.gz"""
import sys, json, gzip, os, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from replaycov import NETS
cid = int(sys.argv[1]); u = sys.argv[2]; od = sys.argv[3]; os.makedirs(od, exist_ok=True)
PM = NETS[cid]['poolManager'].lower()
def keep(x): return {k: v for k, v in (x or {}).items() if k.lower() == PM}
a = call(u, 'web3_clientVersion', [], 30); log = []
for h in sys.argv[4:]:
    rc, e0 = call(u, 'eth_getTransactionReceipt', [h], 60)
    diff, e1 = call(u, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True, 'disableCode': True}}], 120)
    pre, e2 = call(u, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'disableCode': True}}], 120)
    ct, e3 = call(u, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], 120)
    errs = [e for e in (e0, e1, e2, e3) if e]
    log.append({'hash': h, 'errors': errs})
    if errs: print(h, errs); continue
    rec = {'hash': h, 'block': int(rc['blockNumber'], 16), 'index': int(rc['transactionIndex'], 16), 'url': u, 'status': rc['status'],
           'diff': {'pre': keep(diff.get('pre')), 'post': keep(diff.get('post'))}, 'pre': keep(pre), 'call': ct, 'receiptLogs': rc['logs']}
    json.dump(rec, gzip.open('%s/%s.json.gz' % (od, h), 'wt')); print(h, 'ok', rec['block'])
b = call(u, 'web3_clientVersion', [], 30)
json.dump({'url': u, 'clientBefore': a, 'clientAfter': b, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'txs': log}, open('%s/fetch-%d.json' % (od, int(time.time())), 'w'), indent=1)
