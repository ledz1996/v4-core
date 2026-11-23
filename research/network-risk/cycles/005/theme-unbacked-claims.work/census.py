# Window census of everything that moves through the PoolManager, per transaction and token.
#  out   = ERC-20 Transfer logs with from = PoolManager (takes, fee collection)
#  in    = ERC-20 Transfer logs with to = PoolManager, plus wrapper Deposit logs that name the PoolManager
#  pool  = Swap, ModifyLiquidity, Donate logs of the PoolManager in the transaction
#  mint/burn = ERC-6909 Transfer logs from / to the zero address, per id
# Classes per (transaction, token):
#  U  "unexplained outflow": no pool event in the transaction and out + mint > in + burn.
#      With ordinary tokens core cannot produce this: a debit from take or mint needs a credit from settle (a balance
#      rise since sync), from burn or from a pool operation (src/PoolManager.sol:112, 291-297, 322-336, 349-365).
#  F  "round trip": out > 0 and in > 0 for the same token (flash use of take). F0 = no pool event, Fx = in == out exactly.
# Read-only: eth_getLogs, eth_blockNumber, eth_getBlockByNumber.
# usage: python3 census.py <chainId> <days>
import sys, json, gzip, threading, collections
from lib import *
from config import CFG
from fetch import getlogs_range
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
SWAP = '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
MODL = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
DON = '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb'
DEPOSIT = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
Z = '0x' + '0' * 64
PMLOGS = {8453: ('https://base-rpc.publicnode.com', 2000), 56: ('https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 2000), 480: ('https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 5000), 1: ('https://mainnet.gateway.tenderly.co', 500), 143: ('https://rpc2.monad.xyz', 2000)}
def run(cid, days):
    n = net(cid); c = CFG[cid]; pm = n['poolManager'].lower(); u = c['logs']; su = c['state'][0]
    head = int(rpc(su, 'eth_blockNumber', []), 16); B2 = head - 50
    t2 = int(rpc(su, 'eth_getBlockByNumber', [hex(B2), False])['timestamp'], 16)
    tp = int(rpc(su, 'eth_getBlockByNumber', [hex(B2 - 20000), False])['timestamp'], 16)
    bt = (t2 - tp) / 20000; B1 = B2 - int(days * 86400 / bt)
    print(cid, n['name'], 'B1', B1, 'B2', B2, 'blockTime', round(bt, 3), flush=True)
    tx = {}; lock = threading.Lock(); p = pad_addr(pm)
    def ent(h): return tx.setdefault(h, {'pool': 0, 'tok': {}, 'b': 0})
    def tk(e, a): return e['tok'].setdefault(a, [0, 0, 0, 0, 0])  # out, in, mint, burn, wrapIn
    def on_tr(logs):
        with lock:
            for l in logs:
                t = l['topics']
                if l.get('removed'): continue
                if len(t) == 3 and t[0] == TRANSFER and len(l['data']) == 66:
                    v = int(l['data'], 16); e = ent(l['transactionHash']); e['b'] = int(l['blockNumber'], 16); a = l['address'].lower()[2:]
                    if t[1] == p: tk(e, a)[0] += v
                    if t[2] == p: tk(e, a)[1] += v
                elif len(t) == 2 and t[0] == DEPOSIT and t[1] == p and len(l['data']) == 66:
                    v = int(l['data'], 16); e = ent(l['transactionHash']); e['b'] = int(l['blockNumber'], 16); x = tk(e, l['address'].lower()[2:]); x[1] += v; x[4] += v
    def on_pm(logs):
        with lock:
            for l in logs:
                t = l['topics']
                if l.get('removed') or not t: continue
                e = ent(l['transactionHash']); e['b'] = int(l['blockNumber'], 16)
                if t[0] in (SWAP, MODL, DON): e['pool'] += 1
                elif t[0] == T6909 and len(t) == 4:
                    amt = int(l['data'][2:][64:128] or '0', 16)
                    if t[1] == Z: tk(e, t[3][-40:])[2] += amt
                    elif t[2] == Z: tk(e, t[3][-40:])[3] += amt
    w = c.get('workers', 4); st = {}
    st['out'] = getlogs_range(u, {'topics': [TRANSFER, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d out' % cid)
    st['in'] = getlogs_range(u, {'topics': [TRANSFER, None, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d in' % cid)
    st['dep'] = getlogs_range(u, {'topics': [DEPOSIT, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d dep' % cid)
    pu, pc = PMLOGS.get(cid, (u, c['chunk']))
    st['pm'] = getlogs_range(pu, {'address': n['poolManager']}, B1, B2, pc, workers=w, on_logs=on_pm, label='%d pm' % cid)
    for k in st: st[k] = {'req': st[k]['req'], 'logs': st[k]['logs'], 'nFail': len(st[k]['fail']), 'fail': st[k]['fail'][:5]}
    U = []; F = collections.defaultdict(lambda: {'n': 0, 'n0': 0, 'nx': 0, 'nx0': 0, 'eg0': None, 'egx0': None, 'sumOut0': 0}); nat = 0
    for h, e in tx.items():
        for a, (o, i, m, bn, wi) in e['tok'].items():
            if int(a, 16) == 0: continue
            if e['pool'] == 0 and o + m > i + bn: U.append(dict(tx=h, block=e['b'], token='0x' + a, out=str(o), **{'in': str(i)}, mint=str(m), burn=str(bn), wrapIn=str(wi)))
            if o > 0 and i > 0:
                f = F['0x' + a]; f['n'] += 1
                if e['pool'] == 0: f['n0'] += 1; f['eg0'] = f['eg0'] or h; f['sumOut0'] += o
                if o == i:
                    f['nx'] += 1
                    if e['pool'] == 0: f['nx0'] += 1; f['egx0'] = f['egx0'] or h
    for f in F.values(): f['sumOut0'] = str(f['sumOut0'])
    res = dict(chainId=cid, name=n['name'], poolManager=pm, logsUrl=u, pmLogsUrl=pu, B1=B1, B2=B2, days=days, stats=st, txs=len(tx), txsNoPool=sum(1 for e in tx.values() if e['pool'] == 0),
               unexplained=U, roundTrips=dict(sorted(F.items(), key=lambda kv: -kv[1]['n'])))
    json.dump(res, gzip.open('raw/census_%d.json.gz' % cid, 'wt'))
    print(cid, 'txs', len(tx), 'noPool', res['txsNoPool'], 'U', len(U), 'tokens with round trips', len(F), 'stats', json.dumps(st)[:400], flush=True)
if __name__ == '__main__': run(int(sys.argv[1]), float(sys.argv[2]))
