# Task 2 (L-1026): follow mode. The official endpoint answers storage reads at latest only, so poll it.
# Hot set: for the 12 pools with the most recent Swap or ModifyLiquidity logs, the four Pool.State words
# (slot0, feeGrowthGlobal0/1, liquidity) and every tick, position and bitmap word slots2.json lists for them,
# plus protocolFeesAccrued of their currencies. Each batch of reads is bracketed with eth_blockNumber; reads with
# equal bracket ends are compared with the replica at that block. Each loop also asks the official endpoint for
# PoolManager logs in the newest 50 blocks, and any new log block adds its pool's words to the next loop.
# usage: follow.py <official> <replica> <seconds> <out.json>
import json, sys, time
from rpc import rpc, batch
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-hyperevm-twin-state.work/scripts')
from slots import SIG
O, R, DUR, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
S = json.load(open('../raw/slots2.json'))
logs = json.load(open('/home/user/v4-core/research/network-risk/cycles/023/theme-hyperevm-twin-state.work/raw/pm_logs_all_hyperlend.json'))['logs']
recent = []
for l in sorted(logs, key=lambda l: -int(l['blockNumber'], 16)):
    if SIG.get(l['topics'][0]) not in ('Swap', 'ModifyLiquidity'): continue
    p = l['topics'][1] if len(l['topics']) > 1 else None
    if p and p.lower() in S['pools'] or (p and hex(int(p, 16)) in S['pools']):
        q = hex(int(p, 16))
        if q not in recent: recent.append(q)
    if len(recent) >= 12: break
def words_for(pids):
    ws = []
    for k, v in S['slots'].items():
        if v and v.startswith('pool ') and hex(int(v.split()[1], 16)) in pids: ws.append(k)
    return ws
hot = set(words_for(set(recent)))
res = {'official': O, 'replica': R, 'pools': recent, 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
       'cv': {'officialStart': rpc(O, 'web3_clientVersion', []), 'replicaStart': rpc(R, 'web3_clientVersion', [])},
       'loops': 0, 'compared': 0, 'equal': 0, 'unpinned': 0, 'mismatch': [], 'newLogs': [], 'blocksSeen': [], 'errors': []}
t0 = time.time()
seen_logs = set()
while time.time() - t0 < DUR:
    try:
        head = int(rpc(O, 'eth_blockNumber', []), 16)
        lg = rpc(O, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(head - 49), 'toBlock': hex(head)}])
        for l in lg:
            key = (l['transactionHash'], l['logIndex'])
            if key in seen_logs: continue
            seen_logs.add(key); res['newLogs'].append(l)
            if len(l['topics']) > 1: hot |= set(words_for({hex(int(l['topics'][1], 16))}))
    except Exception as e:
        res['errors'].append(['logs', str(e)[:150]]); time.sleep(5); continue
    items = sorted(hot)
    pinned = []
    for i in range(0, len(items), 18):
        ch = items[i:i + 18]
        try:
            r = batch(O, [('eth_blockNumber', [])] + [('eth_getStorageAt', [PM, s, 'latest']) for s in ch] + [('eth_blockNumber', [])])
        except Exception as e:
            res['errors'].append(['official', str(e)[:150]]); time.sleep(8); continue
        b0, b1 = int(r[0], 16), int(r[-1], 16)
        if b0 != b1: res['unpinned'] += len(ch); continue
        pinned.append((b0, ch, r[1:-1]))
        time.sleep(0.6)
    res['blocksSeen'] += sorted({p[0] for p in pinned})
    time.sleep(3)  # let the replica reach the block
    for b0, ch, vals in pinned:
        for k in range(5):
            try:
                rr = batch(R, [('eth_getStorageAt', [PM, s, hex(b0)]) for s in ch], timeout=120); break
            except Exception as e:
                res['errors'].append(['replica', b0, str(e)[:150]]); time.sleep(5 * (k + 1)); rr = None
        if rr is None: continue
        for s, v, x in zip(ch, vals, rr):
            res['compared'] += 1
            if isinstance(x, str) and int(v, 16) == int(x, 16): res['equal'] += 1
            else: res['mismatch'].append({'slot': s, 'label': S['slots'].get(s), 'block': b0, 'official': v, 'replica': x})
    res['loops'] += 1
    json.dump(res, open(out, 'w'))
res['blocksSeen'] = sorted(set(res['blocksSeen']))
res['cv']['officialEnd'] = rpc(O, 'web3_clientVersion', []); res['cv']['replicaEnd'] = rpc(R, 'web3_clientVersion', [])
res['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(res, open(out, 'w'))
print('done loops', res['loops'], 'compared', res['compared'], 'equal', res['equal'], 'mismatch', len(res['mismatch']), 'newLogs', len(res['newLogs']), 'blocks', len(res['blocksSeen']))
