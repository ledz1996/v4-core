"""Step 1 of tasks 1 and 3 (cycle 24, theme-failed-tx-replay). Read-only JSON-RPC.
usage: find.py <chainId> tf <url> <fromBlock> <toBlock> <span>      trace_filter(toAddress=PoolManager) over a range
       find.py <chainId> scan <url> <fromBlock> <toBlock> <nblocks> <seed>   eth_getBlockReceipts on nblocks blocks drawn with random.Random(seed)
Output raw/<cid>/find-<mode>.jsonl: one record per transaction that has a trace into the PoolManager (tf) or a receipt whose
'to' is in the entry set or the PoolManager (scan), with status where known. Every request batch is bracketed with web3_clientVersion
(raw/<cid>/brackets.jsonl); errors go to raw/<cid>/errors.jsonl."""
import json, os, sys, time, random, threading, queue
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS
cid = int(sys.argv[1]); mode = sys.argv[2]; url = sys.argv[3]; lo = int(sys.argv[4]); hi = int(sys.argv[5])
PM = NETS[cid]['poolManager'].lower()
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../raw/%d' % cid); os.makedirs(D, exist_ok=True)
W = json.load(open('/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/%d/window.json' % cid))
INWIN = set(t[0] for t in W['txs'])
ENTRY = set(json.load(open(os.path.join(D, '../entry-%d.json' % cid)))) | {PM}
def br(tag, extra=None):
    v, e = call(url, 'web3_clientVersion', [], 30)
    open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': tag, 'mode': mode, 'url': url, 'client': v, 'err': e, 't': time.time(), 'extra': extra}) + '\n')
def elog(r): open(D + '/errors.jsonl', 'a').write(json.dumps(r) + '\n')
out = open(D + '/find-%s.jsonl' % mode, 'a'); lock = threading.Lock()
br('start', {'range': [lo, hi], 'argv': sys.argv[1:]})
if mode == 'tf':
    span = int(sys.argv[6]); txs = {}; b = hi; ncalls = 0
    while b >= lo:
        a = max(lo, b - span + 1)
        r, e = call(url, 'trace_filter', [{'fromBlock': hex(a), 'toBlock': hex(b), 'toAddress': [PM]}], 180)
        ncalls += 1
        if e:
            elog({'stage': 'trace_filter', 'url': url, 'range': [a, b], 'err': e[:300]})
            if span > 5 and ('429' not in e): span //= 2
            time.sleep(3); continue
        for t in r:
            h = t['transactionHash']; act = t.get('action', {})
            x = txs.setdefault(h, {'hash': h, 'block': t['blockNumber'], 'index': t.get('transactionPosition'), 'inWindow': h in INWIN, 'pmTraces': []})
            x['pmTraces'].append({'sel': (act.get('input') or '')[:10], 'from': act.get('from'), 'value': act.get('value'), 'callType': act.get('callType'),
                                  'addr': t.get('traceAddress'), 'error': t.get('error'), 'out': ((t.get('result') or {}).get('output') or '')[:138]})
        b = a - 1
        if ncalls % 25 == 0: br('every25', {'at': b}); print(cid, 'at', b, len(txs), flush=True)
    for x in txs.values(): out.write(json.dumps(x) + '\n')
    print(cid, 'tf txs', len(txs), 'notInWindow', sum(1 for x in txs.values() if not x['inWindow']))
else:
    n = int(sys.argv[6]); seed = int(sys.argv[7]); rng = random.Random(seed)
    src = sys.argv[8] if len(sys.argv) > 8 else 'range'
    # 'window': draw from the blocks that hold a cycle 23 window transaction (blocks with PoolManager activity), inside [lo, hi]
    pool = sorted(set(t[1] for t in W['txs'] if lo <= t[1] <= hi)) if src == 'window' else range(lo, hi + 1)
    blocks = list(pool) if len(pool) <= n else sorted(rng.sample(list(pool), n))
    json.dump({'seed': seed, 'source': src, 'n': n, 'range': [lo, hi], 'blocks': blocks}, open(D + '/scan-blocks-%d.json' % seed, 'w'))
    q = queue.Queue(); [q.put(b) for b in blocks]; cnt = [0, 0, 0]
    def wk():
        while True:
            try: b = q.get_nowait()
            except queue.Empty: return
            for k in range(6):
                r, e = call(url, 'eth_getBlockReceipts', [hex(b)], 90)
                if e is None: break
                elog({'stage': 'blockReceipts', 'url': url, 'block': b, 'err': e[:200]}); time.sleep(2 + 2 * k)
            if r is None: continue
            with lock:
                cnt[0] += 1
                for x in r:
                    to = (x.get('to') or '').lower()
                    if to in ENTRY:
                        h = x['transactionHash']
                        pmlog = any((l.get('address') or '').lower() == PM for l in x.get('logs', []))
                        out.write(json.dumps({'hash': h, 'block': int(x['blockNumber'], 16), 'index': int(x['transactionIndex'], 16), 'to': to,
                                              'status': x.get('status'), 'pmLog': pmlog, 'inWindow': h in INWIN, 'gasUsed': x.get('gasUsed')}) + '\n')
                        cnt[1] += 1
                        if x.get('status') == '0x0': cnt[2] += 1
                if cnt[0] % 200 == 0: print(cid, cnt, flush=True)
    th = [threading.Thread(target=wk) for _ in range(4)]; [t.start() for t in th]; [t.join() for t in th]
    print(cid, 'scan blocks', cnt[0], 'entry txs', cnt[1], 'failed', cnt[2])
br('end')
