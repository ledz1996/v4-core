"""Rerun one transaction (with its block prefix) under several values of the approximate GAS model; if the number of
logs moves with the model, the transaction's control flow depends on remaining gas, which the reference does not meter."""
import sys, json, copy
sys.path.insert(0, '.')
import lazyreplay as L
from rpc import batch
U = 'https://rpc.mainnet.arc.io'; D = json.load(open('raw/txs.json'))
h = sys.argv[1]; tx, rec = D['tx'][h]['tx'], D['tx'][h]['rec']; bn = int(tx['blockNumber'], 16); idx = int(tx['transactionIndex'], 16); blk = D['blocks'][str(bn)]
hs = blk['transactions'][:idx]; pairs = []
for i in range(0, len(hs), 5):
    ch = hs[i:i + 5]; r = batch(U, [('eth_getTransactionByHash', [x]) for x in ch] + [('eth_getTransactionReceipt', [x]) for x in ch]); pairs += [(r[j], r[len(ch) + j]) for j in range(len(ch))]
res = []
for g in [int(sys.argv[2]) if len(sys.argv) > 2 else None, 1_200_000, 1_600_000, 2_198_158, 4_000_000]:
    t2 = dict(tx)
    if g: t2['gas'] = hex(g)
    base, w, ok, ret, err, rounds, notes = L.replay_prefix(U, pairs + [(t2, rec)], blk)
    pm = sum(1 for a, tp, d in w.logs if a == L.PM) if w else None
    res.append([g, len(w.logs) if w else err, pm]); print(res[-1], 'chain', len(rec['logs']), flush=True)
json.dump({'tx': h, 'runs': res, 'chainLogs': len(rec['logs'])}, open('raw/gassens_%s.json' % h[:10], 'w'))
