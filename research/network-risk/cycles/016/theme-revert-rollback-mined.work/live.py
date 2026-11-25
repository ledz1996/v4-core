"""Read-only. For an endpoint that keeps only recent state (Arbitrum One on arbitrum.drpc.org), follow the chain head
for a fixed time, and trace each new transaction with PoolManager logs within seconds of its block, with the same
analysis as scan.py. Usage: python3 live.py <chainId> <traceUrl> <logsUrl> <seconds> <out.json>"""
import sys, json, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
import scan as S
import importlib.util as _iu
_sp = _iu.spec_from_file_location('rp16', '/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/replay.py'); RP = _iu.module_from_spec(_sp); _sp.loader.exec_module(RP)  # this unit's replay.py, not tools/opdiff/replay.py
cid, turl, lurl, dur, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
pm = nets[cid]['poolManager'].lower()
def one(h):
    t = S.R(turl, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], tries=2)
    acc, lg = [], []; S.walk(t, pm, False, acc, lg); ol = []; S.ordered_logs(t, False, ol)
    rec = S.R(lurl, 'eth_getTransactionReceipt', [h])
    rl = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    unl = [i for i, a in enumerate(acc) if a['sel'] == 'unlock']
    r = {'tx': h, 'block': int(rec['blockNumber'], 16), 'status': int(rec['status'], 16), 'traceStatus': 0 if 'error' in t else 1,
            'logsEqual': rl == ol, 'pm': [[a['sel'], int(a['undone']), a['err'], a['depth']] for a in acc],
            'undoneThenOk': any(a['undone'] and any(not b['undone'] for b in acc[i + 1:]) for i, a in enumerate(acc)),
            'revertedThenCompletedUnlock': any(acc[i]['undone'] and any(not acc[j]['undone'] for j in unl if j > i) for i in unl)}
    if r['undoneThenOk']:  # rerun at once, while the endpoint still has the parent state
        try: r['replay'] = RP.one(cid, turl, pm, h, lurl)
        except Exception as e: r['replay'] = {'error': str(e)[:160]}
    return r
seen, res, errs = set(), [], []
end = time.time() + dur; last = int(S.R(lurl, 'eth_blockNumber', []), 16) - 20; b0 = last
ex = cf.ThreadPoolExecutor(6); fut = []
while time.time() < end:
    head = int(S.R(lurl, 'eth_blockNumber', []), 16)
    if head > last:
        try: lg = S.R(lurl, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(last + 1), 'toBlock': hex(head)}], tries=2)
        except Exception: lg = []
        for l in lg:
            h = l['transactionHash']
            if h not in seen: seen.add(h); fut.append((h, ex.submit(one, h)))
        last = head
    time.sleep(1.0)
for h, f in fut:
    try: res.append(f.result())
    except Exception as e: errs.append({'tx': h, 'error': str(e)[:120]})
hit = [r for r in res if r['undoneThenOk']]
summ = {'chain': cid, 'traceUrl': turl, 'blocks': [b0 + 1, last], 'txs': len(seen), 'traced': len(res), 'errors': len(errs),
        'statusMismatch': sum(r['status'] != r['traceStatus'] for r in res), 'logsMismatch': sum(not r['logsEqual'] for r in res),
        'undoneThenOkTx': len(hit), 'revertedThenCompletedUnlockTx': sum(r['revertedThenCompletedUnlock'] for r in res), 'undoneSelectorsInHits': {}}
json.dump({'summary': summ, 'hits': hit, 'mismatch': [r for r in res if not r['logsEqual']][:30], 'errors': errs[:30]}, open(out, 'w'), indent=1)
print(json.dumps(summ))
