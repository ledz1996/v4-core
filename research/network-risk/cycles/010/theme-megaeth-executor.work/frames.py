"""MegaETH (4326): mined transactions in which a frame that entered the PoolManager reverted.
Read-only. For each transaction that emitted a PoolManager Swap or ModifyLiquidity log, the
endpoint's debug_traceTransaction (callTracer, withLog) is read and the call tree walked.

Records
  - transactions with a reverted frame at or above a PoolManager frame (the PoolManager's
    effects were undone), and whether a later PoolManager.unlock in the same transaction
    completed (needs the unlock flag and deltas of the reverted frame rolled back)
  - transactions where a swap, settle or take ran inside a reverted frame (quoters)
  - for every traced transaction: the receipt status and logs, which the block producer
    wrote, against the status and the surviving logs of the trace, which the RPC node
    computed by re-executing. A producer that kept transient or persistent state of a reverted
    frame would emit different later logs or fail where the re-execution succeeds.

Usage: python3 frames.py <out.json>
"""
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, keccak
import swaps as S

URL = 'https://mainnet.megaeth.com/rpc'
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
SEL = {'0x' + keccak(x.encode())[:4].hex(): x.split('(')[0] for x in [
    'unlock(bytes)', 'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)',
    'modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)',
    'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'sync(address)', 'mint(address,uint256,uint256)',
    'burn(address,uint256,uint256)', 'donate((address,address,uint24,int24,address),uint256,uint256,bytes)',
    'initialize((address,address,uint24,int24,address),uint160)', 'clear(address,uint256)',
    'extsload(bytes32)', 'exttload(bytes32)', 'extsload(bytes32[])', 'exttload(bytes32[])', 'extsload(bytes32,uint256)',
    'transfer(address,address,uint256,uint256)', 'transferFrom(address,address,uint256,uint256)']}


def walk(node, path, reverted_above, acc, depth=0):
    err = 'error' in node
    rev = reverted_above or err
    to = (node.get('to') or '').lower()
    if to == PM:
        sel = SEL.get(node.get('input', '')[:10], node.get('input', '')[:10])
        acc.append({'path': path, 'sel': sel, 'err': node.get('error'), 'undone': rev, 'depth': depth})
    for i, c in enumerate(node.get('calls', []) or []):
        walk(c, path + [i], rev, acc, depth + 1)


def surviving_logs(node, reverted_above, out):
    rev = reverted_above or ('error' in node)
    # callTracer orders a frame's logs and its calls by position; merge by index
    items = [(int(lg.get('position', 0), 16) if isinstance(lg.get('position', 0), str) else lg.get('position', 0), 0, lg) for lg in node.get('logs', []) or []]
    items += [(i, 1, c) for i, c in enumerate(node.get('calls', []) or [])]
    # position of a log is the number of calls made before it in this frame
    for pos, kind, x in sorted(items, key=lambda t: (t[0], t[1])):
        if kind == 0:
            if not rev: out.append((x['address'].lower(), tuple(t.lower() for t in x['topics']), x['data'].lower()))
        else:
            surviving_logs(x, rev, out)


def one(h):
    t = rpc(URL, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], timeout=90)
    acc = []; walk(t, [], False, acc)
    rec = rpc(URL, 'eth_getTransactionReceipt', [h], timeout=60)
    rlogs = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    tl = []; surviving_logs(t, False, tl)
    status_trace = 0 if 'error' in t else 1
    res = {'tx': h, 'block': int(rec['blockNumber'], 16), 'statusReceipt': int(rec['status'], 16), 'statusTrace': status_trace,
           'logsReceipt': len(rlogs), 'logsTrace': len(tl), 'logsEqual': rlogs == tl, 'logsEqualAsMultiset': sorted(rlogs) == sorted(tl),
           'pmFrames': len(acc)}
    undone = [a for a in acc if a['undone']]
    res['pmUndone'] = undone[:12]
    if undone:
        # was there an unlock that completed after a reverted one?
        unl = [a for a in acc if a['sel'] == 'unlock']
        later_ok = False
        for i, a in enumerate(unl):
            if a['undone']:
                for b in unl[i + 1:]:
                    if not b['undone']: later_ok = True
        res['revertedThenCompletedUnlock'] = later_ok
        res['undoneSels'] = sorted({a['sel'] for a in undone})
    return res


def main():
    out = sys.argv[1]
    want = int(os.environ.get('WANT', 6000))
    logs, lo, head = S.collect(URL, PM, want=want, max_calls=200)
    hs = list(dict.fromkeys(lg['transactionHash'] for lg in sorted(logs, key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16)))))
    print('txs', len(hs), 'blocks', lo, head, flush=True)

    def w(h):
        try: return one(h)
        except Exception as e: return {'tx': h, 'error': str(e)[:120]}  # noqa
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(w, hs))
    ok = [r for r in res if 'error' not in r]
    summ = {'traced': len(ok), 'errors': len(res) - len(ok), 'blocks': [lo, head],
            'statusMismatch': sum(r['statusReceipt'] != r['statusTrace'] for r in ok),
            'logsMismatch': sum(not r['logsEqual'] for r in ok), 'logsMismatchMultiset': sum(not r['logsEqualAsMultiset'] for r in ok),
            'withUndonePmFrame': sum(bool(r['pmUndone']) for r in ok),
            'revertedThenCompletedUnlock': sum(bool(r.get('revertedThenCompletedUnlock')) for r in ok)}
    sels = {}
    for r in ok:
        for x in r.get('undoneSels', []): sels[x] = sels.get(x, 0) + 1
    summ['undoneSelectors'] = sels
    json.dump({'summary': summ, 'interesting': [r for r in ok if r['pmUndone'] or not r['logsEqual'] or r['statusReceipt'] != r['statusTrace']][:400],
               'errors': [r for r in res if 'error' in r][:30]}, open(out, 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
