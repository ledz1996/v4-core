"""Cycle 16, theme-revert-rollback-mined, task 1. Read-only.
For one chain: collect transactions that emitted PoolManager logs in recent blocks, read each with
debug_traceTransaction (callTracer, withLog), and find those in which a frame into the PoolManager
was undone (it, or a frame above it, failed) and a later frame into the PoolManager in the same
transaction was not undone. Records the selector sequence and whether an undone unlock was followed
by a completed unlock. Compares receipt status and logs with the trace.
Usage: python3 scan.py <chainId> <traceUrl> <logsUrl> <maxTx> <out.json> [threads]"""
import sys, json, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak

SIGS = ['unlock(bytes)', 'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)',
        'modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)',
        'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'sync(address)', 'mint(address,uint256,uint256)',
        'burn(address,uint256,uint256)', 'donate((address,address,uint24,int24,address),uint256,uint256,bytes)',
        'initialize((address,address,uint24,int24,address),uint160)', 'clear(address,uint256)', 'extsload(bytes32)',
        'exttload(bytes32)', 'extsload(bytes32[])', 'exttload(bytes32[])', 'extsload(bytes32,uint256)',
        'transfer(address,uint256,uint256)', 'transferFrom(address,address,uint256,uint256)', 'balanceOf(address,uint256)',
        'allowance(address,address,uint256)', 'isOperator(address,address)', 'protocolFeesAccrued(address)']
SEL = {keccak(x.encode())[:4].hex(): x.split('(')[0] for x in SIGS}


def R(url, m, p, timeout=int(__import__("os").environ.get("SCAN_TIMEOUT", "90")), tries=int(__import__("os").environ.get("SCAN_TRIES", "7"))):
    last = None
    for k in range(tries):
        try: return rpc(url, m, p, timeout=timeout)
        except Exception as e:
            last = e
            if 'not found' in str(e).lower() and k >= 1: break
            time.sleep(2.0 * (k + 1))
    raise last


def walk(node, pm, undone_above, acc, logs, depth=0):
    err = 'error' in node; und = undone_above or err
    if (node.get('to') or '').lower() == pm:
        acc.append({'sel': SEL.get(node.get('input', '')[2:10], node.get('input', '')[2:10]), 'err': node.get('error'),
                    'undone': und, 'depth': depth, 'type': node.get('type')})
    for l in node.get('logs', []) or []:
        if not und: logs.append(((l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower(), l.get('position')))
    for c in node.get('calls', []) or []:
        walk(c, pm, und, acc, logs, depth + 1)


def ordered_logs(node, und_above, out):
    """Surviving logs in execution order: a log's position is the number of child calls before it."""
    und = und_above or 'error' in node
    calls = node.get('calls', []) or []; lg = node.get('logs', []) or []
    bypos = {}
    for l in lg: bypos.setdefault(int(l.get('position', len(calls)) if not isinstance(l.get('position'), str) else int(l['position'], 16)), []).append(l)
    for i in range(len(calls) + 1):
        for l in bypos.get(i, []):
            if not und: out.append(((l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower()))
        if i < len(calls): ordered_logs(calls[i], und, out)


def logs_window(url, pm, want, head, step):
    hs = []; b = head; spans = 0
    while len(hs) < want and spans < 400:
        a = b - step + 1
        try: lg = R(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(a), 'toBlock': hex(b)}], tries=4)
        except Exception as e:
            if step > 20: step //= 4; continue
            raise
        for l in sorted(lg, key=lambda x: (int(x['blockNumber'], 16), int(x['transactionIndex'], 16))):
            if l['transactionHash'] not in hs: hs.append(l['transactionHash'])
        b = a - 1; spans += 1
    return hs[:want], b


def main():
    cid = int(sys.argv[1]); turl, lurl = sys.argv[2], sys.argv[3]; want = int(sys.argv[4]); out = sys.argv[5]
    th = int(sys.argv[6]) if len(sys.argv) > 6 else 4; step = int(sys.argv[7]) if len(sys.argv) > 7 else 500
    nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
    pm = nets[cid]['poolManager'].lower()
    head = int(R(lurl, 'eth_blockNumber', []), 16)
    hs, low = logs_window(lurl, pm, want, head, step)
    print(cid, 'txs', len(hs), 'blocks', low, head, flush=True)

    def one(h):
        t = R(turl, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
        acc, lg = [], []; walk(t, pm, False, acc, lg)
        ol = []; ordered_logs(t, False, ol)
        rec = R(lurl, 'eth_getTransactionReceipt', [h])
        rl = [((l['address']).lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
        unl = [i for i, a in enumerate(acc) if a['sel'] == 'unlock']
        later_ok = any(a['undone'] and any(not b['undone'] for b in acc[i + 1:]) for i, a in enumerate(acc))
        rtc = any(acc[i]['undone'] and any(not acc[j]['undone'] for j in unl if j > i) for i in unl)
        return {'tx': h, 'block': int(rec['blockNumber'], 16), 'index': int(rec['transactionIndex'], 16), 'status': int(rec['status'], 16),
                'traceStatus': 0 if 'error' in t else 1, 'logsEqual': rl == ol, 'logsEqualSet': sorted(rl) == sorted(ol),
                'nLogs': len(rl), 'pm': [[a['sel'], int(a['undone']), a['err'], a['depth']] for a in acc],
                'undoneThenOk': later_ok, 'revertedThenCompletedUnlock': rtc, 'from': t.get('from'), 'to': t.get('to')}

    def w(h):
        try: return one(h)
        except Exception as e: return {'tx': h, 'error': str(e)[:200]}
    with cf.ThreadPoolExecutor(th) as ex: res = list(ex.map(w, hs))
    ok = [r for r in res if 'error' not in r]
    hit = [r for r in ok if r['undoneThenOk']]
    summ = {'chain': cid, 'traceUrl': turl, 'blocks': [low + 1, head], 'txs': len(hs), 'traced': len(ok), 'errors': len(res) - len(ok),
            'statusMismatch': sum(r['status'] != r['traceStatus'] for r in ok), 'logsMismatch': sum(not r['logsEqual'] for r in ok),
            'logsMismatchSet': sum(not r['logsEqualSet'] for r in ok), 'undonePmFrameTx': sum(any(p[1] for p in r['pm']) for r in ok),
            'undoneThenOkTx': len(hit), 'revertedThenCompletedUnlockTx': sum(r['revertedThenCompletedUnlock'] for r in ok)}
    us = {}
    for r in hit:
        for p in r['pm']:
            if p[1]: us[p[0]] = us.get(p[0], 0) + 1
    summ['undoneSelectorsInHits'] = us
    json.dump({'summary': summ, 'hits': hit, 'mismatch': [r for r in ok if not r['logsEqual'] or r['status'] != r['traceStatus']][:50],
               'errors': [r for r in res if 'error' in r][:30]}, open(out, 'w'), indent=1)
    print(json.dumps(summ), flush=True)


if __name__ == '__main__':
    main()
