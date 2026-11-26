"""Cycle 24 theme-replay-eleven, Task 2 and Task 3: replay of mined PoolManager transactions from parent-block storage on
networks whose public endpoints serve no traces (Zora, World Chain, Soneium, Arc) and on BNB Smart Chain.
Generalises cycles/021/theme-arc-running-code.work/drive.py: the transaction is run whole in the reference interpreter
(pyevm_tx24 through lazyreplay24) with every account, code, balance, nonce and storage word read lazily from the parent block
with eth_getCode, eth_getBalance, eth_getTransactionCount and eth_getStorageAt, then compared with the chain:
  status; every receipt log in order; every PoolManager storage word the run read or wrote against eth_getStorageAt at the
  block (only when no later transaction of the block emits a PoolManager log); the PoolManager native balance change against
  eth_getBalance at the block and its parent (only when the transaction is the only one of the block that emits a PoolManager log).
A transaction that differs in status, a PoolManager log, a PoolManager word or the native balance and is not first in its block is run again after every earlier transaction of the block on the
same state (replay_prefix), up to PREFIX_MAX earlier transactions.
usage: gdrive.py <cid> <url> <window.json> <shard> <nshards> <out.jsonl> [arc]
The window file lists [hash, block, index] newest first plus 'pmTx' (block -> list of tx indices with a PoolManager log)."""
import sys, os, json, time
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import lazyreplay24 as L
from rpc import batch, call
from eps import NETS
I = L.I
cid, url, wf, shard, nsh, outp = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
L.ARC = len(sys.argv) > 7 and sys.argv[7] == 'arc'; L.CELO = len(sys.argv) > 7 and sys.argv[7] == 'celo'; L.CID = cid
L.MAX_ROUNDS = int(os.environ.get('MAXR', '60'))
PM = int(NETS[cid]['poolManager'], 16); L.PM = PM
PREFIX_MAX = 120
RCPT = os.environ.get('RCPT_URLS', '').split() 
W = json.load(open(wf)); pmtx = {int(k): set(v) for k, v in W['pmTx'].items()}
done = set()
if os.path.exists(outp):
    for line in open(outp): done.add(json.loads(line)['tx'])
fo = open(outp, 'a'); BLK = {}
def block(bn, full=False):
    k = (bn, full)
    if k not in BLK:
        BLK[k] = call(url, 'eth_getBlockByNumber', [hex(bn), full])
        if len(BLK) > 200: BLK.pop(next(iter(BLK)))
    return BLK[k]
def compare(r, w, ok, rec, tx, bn, idx, first):
    r['statusChain'] = I(rec['status']); r['statusRef'] = int(bool(ok)); r['steps'] = w.steps
    rl = [(l['address'].lower(), [x.lower() for x in l['topics']], l['data'].lower()) for l in rec['logs']]
    ol = [('0x%040x' % ad, ['0x%064x' % t for t in tp], '0x' + d.hex()) for (ad, tp, d) in w.logs]
    r['logsChain'] = len(rl); r['logsRef'] = len(ol); r['logsEqual'] = rl == ol
    pml = [x for x in rl if x[0] == '0x%040x' % PM]; r['pmLogs'] = len(pml); r['pmLogsEqual'] = pml == [x for x in ol if x[0] == '0x%040x' % PM]
    if rl != ol: r['logMismatch'] = {'chain': [x for x in rl if x not in ol][:20], 'ref': [x for x in ol if x not in rl][:20]}
    r['pmFrames'] = [[f[0], f[2], f[3]] for f in w.frames][:80]
    keys = sorted({k for k in set(w.storage.keys()) | w.storage.read if k[0] == PM})
    later = any(j > idx for j in pmtx.get(bn, ())); r['laterPmTxInBlock'] = later; r['earlierPmTxInBlock'] = any(j < idx for j in pmtx.get(bn, ()))
    r['pmSlots'] = len(keys); r['pmSlotsWritten'] = sum(1 for k in w.storage.keys() if k[0] == PM)
    if not later and keys:
        post = []
        for i in range(0, len(keys), 10): post += batch(url, [('eth_getStorageAt', ['0x%040x' % PM, hex(k[1]), hex(bn)]) for k in keys[i:i + 10]])
        r['pmSlotMismatch'] = [[hex(k[1]), v, hex(w.storage.get(k, 0))] for k, v in zip(keys, post) if int(v, 16) != w.storage.get(k, 0)]
        r['pmSlotsCompared'] = len(keys)
    if pmtx.get(bn, set()) <= {idx}:
        b0, b1 = batch(url, [('eth_getBalance', ['0x%040x' % PM, hex(bn - 1)]), ('eth_getBalance', ['0x%040x' % PM, hex(bn)])])
        ref = (dict.__getitem__(w.balances, PM) - int(b0, 16)) if dict.__contains__(w.balances, PM) else 0  # a balance the run never wrote is unchanged
        r['pmNativeDeltaChain'] = str(int(b1, 16) - int(b0, 16)); r['pmNativeDeltaRef'] = str(ref); r['pmNativeEqual'] = int(b1, 16) - int(b0, 16) == ref
    return (r['statusChain'] == r['statusRef'] and r['logsEqual'] and not r.get('pmSlotMismatch') and r.get('pmNativeEqual') is not False)
mine = [t for k, t in enumerate(W['txs']) if k % nsh == shard and t[0] not in done]
for h, bn, idx in mine:
    t0 = time.time(); r = {'tx': h, 'block': bn, 'index': idx}
    try:
        tx = call(url, 'eth_getTransactionByHash', [h]); rec = None
        for u2 in [url, url, url] + RCPT:  # forno.celo.org answers null for some receipts from some of its backends
            rec = call(u2, 'eth_getTransactionReceipt', [h])
            if rec: r['receiptFrom'] = u2; break
            time.sleep(0.5)
        blk = block(bn)
        if rec is None or tx is None: raise RuntimeError('transaction or receipt not served')
        r['to'] = tx.get('to'); r['type'] = tx.get('type'); r['from'] = tx.get('from')
        if not tx.get('to'): r['unsupported'] = 'contract creation transaction'; raise StopIteration
        base, w, ok, ret, err, rounds = L.replay(url, tx, rec, blk)
        r['rounds'] = rounds; r['keysFetched'] = len(base.c); r['converged'] = not base.miss
        if err: r['unsupported'] = err; raise StopIteration
        for a in ('creates', 'mints', 'p256', 'collisions', 'ncaCalls', 'celoTransfers'): r[a] = getattr(w, a, 0)
        good = compare(r, w, ok, rec, tx, bn, idx, True)
        r['match'] = good
        pm_ok = r['statusChain'] == r['statusRef'] and r['pmLogsEqual'] and not r.get('pmSlotMismatch') and r.get('pmNativeEqual') is not False
        if not good and pm_ok: r['prefix'] = 'not run: status, PoolManager logs, words and balance already equal; only logs of other contracts differ'
        if not good and not pm_ok and idx > 0:
            full = block(bn, True); earlier = [t for t in full['transactions'] if I(t['transactionIndex']) < idx]
            if len(earlier) > PREFIX_MAX: r['prefix'] = 'not run: %d earlier transactions' % len(earlier); raise StopIteration
            recs = []
            for j in range(0, len(earlier), 8): recs += batch(url, [('eth_getTransactionReceipt', [t['hash']]) for t in earlier[j:j + 8]])
            for j, x in enumerate(recs):
                if x is None:
                    for u2 in [url, url] + RCPT:
                        x = call(u2, 'eth_getTransactionReceipt', [earlier[j]['hash']])
                        if x: recs[j] = x; break
            if any(x is None for x in recs): raise RuntimeError('receipt of an earlier transaction not served')
            pairs = list(zip(earlier, recs)) + [(tx, rec)]
            base2, w2, ok2, ret2, err2, rounds2, notes = L.replay_prefix(url, pairs, blk)
            p = {'earlier': len(earlier), 'rounds': rounds2, 'notes': notes[:20], 'converged': not base2.miss}
            if err2: p['unsupported'] = err2
            else: p['match'] = compare(p, w2, ok2, rec, tx, bn, idx, False)
            r['prefix'] = p
    except StopIteration: pass
    except Exception as e: r['error'] = repr(e)[:300]
    r['secs'] = round(time.time() - t0, 1)
    fo.write(json.dumps(r) + '\n'); fo.flush()
