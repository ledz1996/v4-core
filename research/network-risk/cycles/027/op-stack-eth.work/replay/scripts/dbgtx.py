"""Debug one parent-storage replay that differs in status: print every failing frame (depth, callee, selector, revert data).
usage: dbgtx.py <cid> <url> <hash> [arc|celo]"""
import sys, json
sys.path.insert(0, '.')
import lazyreplay24 as L
from rpc import call
from eps import NETS
cid, url, h = int(sys.argv[1]), sys.argv[2], sys.argv[3]
L.MAX_ROUNDS = 400; L.ARC = len(sys.argv) > 4 and sys.argv[4] == 'arc'; L.CELO = len(sys.argv) > 4 and sys.argv[4] == 'celo'; L.CID = cid; L.PM = int(NETS[cid]['poolManager'], 16)
tx = call(url, 'eth_getTransactionByHash', [h]); rec = call(url, 'eth_getTransactionReceipt', [h]) or call('https://rpc.ankr.com/celo', 'eth_getTransactionReceipt', [h])
bn = int(tx['blockNumber'], 16); blk = call(url, 'eth_getBlockByNumber', [hex(bn), False])
full = call(url, 'eth_getBlockByNumber', [hex(bn), True]); idx = int(tx['transactionIndex'], 16)
earlier = [t for t in full['transactions'] if int(t['transactionIndex'], 16) < idx]
recs = [call(url, 'eth_getTransactionReceipt', [t['hash']]) or call('https://rpc.ankr.com/celo' if cid == 42220 else url, 'eth_getTransactionReceipt', [t['hash']]) for t in earlier]
fails = []
orig = L.P.World.call
def wrapped(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
    ok, ret = orig(self, caller, to, value, data, static, depth, code_addr, storage_addr)
    if not ok and self is LAST[0]: fails.append((depth, '0x%040x' % to, bytes(data[:4]).hex(), ret[:100].hex(), value))
    return ok, ret
L.P.World.call = wrapped
LAST = [None]
oro = L.run_once
def ro(base, tx_, rec_, blk_, cid=None, pre=None):
    del fails[:]
    w, ok, ret = (None, None, None)
    w0 = L.W
    class W2(w0):
        def __init__(s, b): w0.__init__(s, b); LAST[0] = s if tx_['hash'] == h else None
    L.W = W2
    try: return oro(base, tx_, rec_, blk_, cid, pre)
    finally: L.W = w0
L.run_once = ro
base, w, ok, ret, err, rounds, notes = L.replay_prefix(url, list(zip(earlier, recs)) + [(tx, rec)], blk)
print('ok', ok, 'err', err, 'rounds', rounds, 'notes', notes, 'status chain', rec['status'], 'gas', int(tx['gas'], 16), 'gasUsed', int(rec['gasUsed'], 16))
for f in fails[-12:]: print('  fail', f)
print('chain logs', len(rec['logs']), 'ref logs', len(w.logs) if w else None)
