"""Step 2 of tasks 1 and 3 (cycle 24, theme-failed-tx-replay). Read-only JSON-RPC.
usage: trace.py <chainId> <maxFailed> <maxLogFree> <seed>
Candidates come from raw/<cid>/find-*.jsonl: receipts with status 0 (task 1) and successful transactions outside the cycle 23
log window without a PoolManager log (task 3). A random.Random(seed) sample of at most maxFailed / maxLogFree is traced with
callTracer withLog; if a frame enters the PoolManager, prestateTracer (and for successful ones prestateTracer diffMode) is added and
the record is stored in raw/<cid>/tx/<hash>.json.gz in the cycle 23 format, with 'status' and 'kind'. Transactions that never enter
the PoolManager are listed in raw/<cid>/nopm.jsonl. Calls are bracketed with web3_clientVersion every 100 transactions."""
import json, os, sys, time, gzip, random, threading, queue
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS
cid = int(sys.argv[1]); mf = int(sys.argv[2]); ml = int(sys.argv[3]); seed = int(sys.argv[4])
PM = NETS[cid]['poolManager'].lower()
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../raw/%d' % cid); os.makedirs(D + '/tx', exist_ok=True)
TRACE = {1: ['https://eth.api.pocket.network'], 8453: ['https://base.api.pocket.network'], 130: ['https://unichain.api.pocket.network', 'https://unichain.drpc.org'],
         42161: ['https://arb-one.api.pocket.network', 'https://arbitrum.drpc.org'], 56: ['https://bsc.api.pocket.network', 'https://bsc.drpc.org'], 43114: ['https://avax.api.pocket.network'],
         137: ['https://polygon.drpc.org', 'https://poly.api.pocket.network'], 143: ['https://rpc.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://rpc1.monad.xyz'],
         4326: ['https://mainnet.megaeth.com/rpc'], 999: ['https://rpc.purroofgroup.com', 'https://hyperliquid.drpc.org']}
urls = os.environ['TRACE_URLS'].split(',') if os.environ.get('TRACE_URLS') else TRACE[cid]
cands = {}
for fn in os.listdir(D):
    if fn.startswith('find-') and fn.endswith('.jsonl'):
        for l in open(os.path.join(D, fn)):
            x = json.loads(l)
            if x['hash'] not in cands or ('status' in x and 'status' not in cands[x['hash']]): cands[x['hash']] = x
failed = sorted(h for h, x in cands.items() if x.get('status') == '0x0')
logfree = sorted(h for h, x in cands.items() if x.get('status') == '0x1' and not x.get('inWindow') and not x.get('pmLog'))
rng = random.Random(seed)
fs = failed if len(failed) <= mf else sorted(rng.sample(failed, mf)); ls = logfree if len(logfree) <= ml else sorted(rng.sample(logfree, ml))
json.dump({'seed': seed, 'failedCandidates': len(failed), 'logFreeCandidates': len(logfree), 'failedSampled': fs, 'logFreeSampled': ls},
          open(D + '/trace-sample-%d.json' % seed, 'w'))
def elog(r): open(D + '/errors.jsonl', 'a').write(json.dumps(r) + '\n')
lock = threading.Lock(); done = [0]
def br(tag):
    for u in urls:
        v, e = call(u, 'web3_clientVersion', [], 30)
        open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'trace-' + tag, 'url': u, 'client': v, 'err': e, 'done': done[0], 't': time.time()}) + '\n')
def tr(u, h, cfg):
    for k in range(6):
        r, e = call(u, 'debug_traceTransaction', [h, cfg], 120)
        if e is None: return r, None
        elog({'stage': 'trace', 'url': u, 'tx': h, 'cfg': cfg.get('tracer'), 'err': e[:300]})
        if '429' in e or 'rate' in e.lower() or 'EXC' in e or 'HTTP 5' in e: time.sleep(2 + 3 * k); continue
        return None, e
    return None, e
def touches(f):
    if (f.get('to') or '').lower() == PM: return True
    return any(touches(c) for c in f.get('calls', []) or [])
def keep_pm(x): return {k: v for k, v in (x or {}).items() if k.lower() == PM}
def one(u, h, kind):
    p = '%s/tx/%s.json.gz' % (D, h)
    if os.path.exists(p): return True
    x = cands[h]
    ct, e = tr(u, h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}})
    if ct is None: return False
    if not touches(ct):
        with lock: open(D + '/nopm.jsonl', 'a').write(json.dumps({'hash': h, 'kind': kind, 'to': ct.get('to'), 'error': ct.get('error')}) + '\n')
        return True
    rec = {'hash': h, 'block': x['block'], 'index': x.get('index'), 'url': u, 'status': x.get('status'), 'kind': kind, 'call': ct}
    pre, e = tr(u, h, {'tracer': 'prestateTracer', 'tracerConfig': {'disableCode': True}})
    rec['pre'] = keep_pm(pre) if pre is not None else None
    if kind == 'logfree':
        diff, e = tr(u, h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True, 'disableCode': True}})
        rec['diff'] = {'pre': keep_pm((diff or {}).get('pre')), 'post': keep_pm((diff or {}).get('post'))} if diff is not None else None
    for a in (rec['pre'] or {}).values(): a.pop('code', None)
    gzip.open(p + '.tmp', 'wt').write(json.dumps(rec)); os.rename(p + '.tmp', p)
    return True
q = queue.Queue(); [q.put((h, 'failed')) for h in fs]; [q.put((h, 'logfree')) for h in ls]
br('start')
def wk(n):
    while True:
        try: h, kind = q.get_nowait()
        except queue.Empty: return
        for j in range(len(urls)):
            if one(urls[(n + j) % len(urls)], h, kind): break
        with lock:
            done[0] += 1
            if done[0] % 100 == 0: br('every100'); print(cid, done[0], flush=True)
th = [threading.Thread(target=wk, args=(n,)) for n in range(4)]; [t.start() for t in th]; [t.join() for t in th]
br('end'); print(cid, 'traced', done[0], 'failed', len(fs), 'logfree', len(ls))
