"""BNB Chain live census: the public full nodes keep state for about 128 blocks only, so blocks are read as they
arrive. For each block, eth_getBlockReceipts selects the transactions with a PoolManager log or an ERC-20 Transfer
from or to the PoolManager, then debug_traceTransaction (callTracer) is run on them while state is still held, and
(tracing on the URLs containing "pocket", receipts on the others) the frames go through census.py's model. Read only. Usage: live56.py <out.jsonl> <target_tx> <url> [<url>...]"""
import sys, os, json, time, itertools, threading, queue
sys.argv = [sys.argv[0], '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df', '/dev/null', '1', '/dev/null'] + sys.argv[1:]
OUT, TARGET = sys.argv[5], int(sys.argv[6]); URLS = sys.argv[7:]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'census.py')).read().split('txs = json.load(open(lst))')[0]
g = {'__name__': 'c'}; sys.argv = [sys.argv[0], '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df', OUT, '8', '/dev/null'] + URLS
exec(src, g)
rpc, walk, model = g['rpc'], g['walk'], g['model']
RURLS = [u for u in URLS if 'pocket' not in u]; TURLS = [u for u in URLS if 'pocket' in u] or URLS
g['URLS'][:] = TURLS
g2 = {'__name__': 'c2'}; sys.argv = [sys.argv[0], PM if False else '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df', '/dev/null', '1', '/dev/null'] + RURLS; exec(src, g2); rrpc = g2['rpc']
PM = '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'; T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; top = '0x' + '0' * 24 + PM[2:]
q = queue.Queue(); lock = threading.Lock(); f = open(OUT, 'a'); n = [0]; blocks = open(OUT + '.blocks', 'a')
def worker():
    while True:
        h, bn, ix, frm = q.get()
        try:
            t = rpc('debug_traceTransaction', [h, {'tracer': 'callTracer'}], tries=4)
            acc = []; walk(t, acc)
            s, bad, k = model(acc) if not t.get('error') else (None, [], 0)
            r = {'tx': h, 'block': bn, 'idx': ix, 'ok': not t.get('error'), 'from': frm, 'endSynced': s, 'settleChecks': k, 'bad': bad,
                 'frames': [[x['sel'], x['arg'], x['value'], x['rev'], x['from']] for x in acc]}
        except Exception as e:
            r = {'tx': h, 'block': bn, 'idx': ix, 'fail': str(e)[:200]}
        with lock:
            f.write(json.dumps(r) + '\n'); f.flush(); n[0] += 1
        q.task_done()
for _ in range(10): threading.Thread(target=worker, daemon=True).start()
nxt = int(rrpc('eth_blockNumber', []), 16); t0 = time.time(); found = 0
while found < TARGET:
    head = int(rrpc('eth_blockNumber', []), 16)
    while nxt <= head and found < TARGET:
        try: rc = rrpc('eth_getBlockReceipts', [hex(nxt)], tries=4)
        except Exception as e:
            blocks.write(json.dumps({'block': nxt, 'fail': str(e)[:100]}) + '\n'); nxt += 1; continue
        sel = []
        for r in rc:
            hit = any(l['address'].lower() == PM or (l['topics'] and l['topics'][0] == T and len(l['topics']) >= 3 and top in (l['topics'][1], l['topics'][2])) for l in r['logs'])
            if hit: sel.append(r)
        for r in sel: q.put((r['transactionHash'], nxt, int(r['transactionIndex'], 16), r['from'].lower()))
        blocks.write(json.dumps({'block': nxt, 'ntx': len(rc), 'pm': len(sel)}) + '\n'); blocks.flush()
        found += len(sel); nxt += 1
    if int(time.time() - t0) % 60 == 0: print(round(time.time() - t0), nxt, found, n[0], q.qsize(), flush=True)
    time.sleep(0.3)
q.join(); print('finished', found, n[0], flush=True)
