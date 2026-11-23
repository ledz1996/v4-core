# Transfer census with one rule and no labels. For a block window on one network: every ERC-20 Transfer log with the PoolManager as
# sender or recipient, wrapper Deposit logs naming it, and every PoolManager log (Swap with amounts, ModifyLiquidity, Donate, claims).
# Per (transaction, token):  net = out + claims minted - in - claims burned,  owed = sum of Swap amounts of the token over pools that
# hold it (positive when the pool pays, src/PoolManager.sol:187-239) minus Donate amounts. The row is flagged when net > owed and the
# transaction holds no ModifyLiquidity log on a pool with that token and no pool event on a pool missing from the Initialize list.
# Transactions with pool events are judged too (cycle 5 skipped them). Every flagged row then goes through rule.classify.
# Read-only: eth_getLogs, eth_blockNumber, eth_getBlockByNumber. usage: python3 census2.py <chainId> <days> [tag]
import sys, json, gzip, threading, collections, os, struct, time
from lib import *
from config import CFG
from fetch import getlogs_range
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
SWAP = '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
MODL = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
DON = '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb'
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
DEPOSIT = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
NATLOG = 'fffffffffffffffffffffffffffffffffffffffe'   # native transfer logs (Arc and any chain with EIP-7708 style logs)
Z = '0x' + '0' * 64; Z40 = '0' * 40; ARCUSDC = '3600000000000000000000000000000000000000'
PMLOGS = {8453: ('https://base-rpc.publicnode.com', 2000), 56: ('https://bsc.api.pocket.network', 1000), 480: ('https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 5000), 1: ('https://mainnet.gateway.tenderly.co', 500), 143: ('https://rpc2.monad.xyz', 2000)}
def s128(h): 
    v = int(h, 16); return v - (1 << 256) if v >> 255 else v
def pool_map(cid, ids):
    """pool id -> (currency0, currency1) for the ids asked, from the Initialize lists."""
    m = {}
    if cid == 8453:
        want = {bytes.fromhex(i[2:]) for i in ids}
        with open('raw/base_init.bin', 'rb') as f:
            while True:
                h = f.read(8)
                if len(h) < 8: break
                a, n = struct.unpack('>II', h); body = f.read(102 * n)
                for k in range(n):
                    r = body[102 * k: 102 * k + 102]
                    if r[4:36] in want: m['0x' + r[4:36].hex()] = (r[36:56].hex(), r[56:76].hex())
        return m
    fns = ['raw/init_%d.json.gz' % cid, '../../005/theme-shared-hooks.work/raw/init_%d.json.gz' % cid]
    for fn in fns:
        if os.path.exists(fn):
            for r in json.load(gzip.open(fn))['rows']: m[r[1]] = (r[2][2:], r[3][2:])
            break
    return m
LOGSRC = {56: ('https://bsc.api.pocket.network', 1000, 4), 480: ('https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 10000, 1), 196: ('https://xlayer-mainnet.rpc.sentio.xyz', 1000, 4)}
SEGDAYS = {1868: 20, 7777777: 400, 4326: 200, 4217: 200, 999: 400, 42220: 200, 480: 30, 1: 2, 10: 4, 130: 4, 8453: 0.5, 56: 1, 4663: 1, 42161: 4, 5042: 2, 99901: 3, 143: 2, 137: 6, 43114: 14, 57073: 7, 196: 4}
def run(cid, days, tag=''):
    n = net(cid); c = CFG[cid]; su = c['state'][0]
    head = int(rpc(su, 'eth_blockNumber', []), 16); B2 = head - 50
    t2 = int(rpc(su, 'eth_getBlockByNumber', [hex(B2), False])['timestamp'], 16)
    tp = int(rpc(su, 'eth_getBlockByNumber', [hex(B2 - 20000), False])['timestamp'], 16)
    bt = (t2 - tp) / 20000; B1 = B2 - int(days * 86400 / bt)
    for fn in ['raw/init_%d.json.gz' % cid, '../../005/theme-shared-hooks.work/raw/init_%d.json.gz' % cid]:
        if os.path.exists(fn): B1 = max(B1, json.load(gzip.open(fn))['lo']); break
    B1 = max(B1, 0)
    seg = int(SEGDAYS.get(cid, 10 ** 6) * 86400 / bt); C = collections.Counter(); flagged = []; agg = dict(txs=0, txsWithPoolEvent=0, poolsUnknown=0, fails=collections.Counter(), req=0, logs=0, nativeLogs=False)
    print(cid, n['name'], 'B1', B1, 'B2', B2, 'blockTime', round(bt, 3), 'segment', seg, flush=True)
    a = B1
    while a <= B2:
        b = min(a + seg - 1, B2); o = segment(cid, a, b)
        C.update(o['counts']); flagged += o['flagged']; agg['txs'] += o['txs']; agg['txsWithPoolEvent'] += o['txsWithPoolEvent']; agg['poolsUnknown'] += o['poolsUnknown']
        agg['nativeLogs'] = agg['nativeLogs'] or o['nativeLogs']
        for k, v in o['stats'].items(): agg['fails'][k] += v['nFail']; agg['req'] += v['req']; agg['logs'] += v['logs']
        print(cid, 'segment', a, b, 'txs', o['txs'], 'flagged so far', len(flagged), time.strftime('%H:%M:%S'), flush=True)
        json.dump(dict(chainId=cid, name=n['name'], poolManager=n['poolManager'].lower(), B1=B1, B2=b, wantB2=B2, days=days, partial=b < B2, counts=dict(C), flagged=flagged, fails=dict(agg['fails']), req=agg['req'], logs=agg['logs'],
                       txs=agg['txs'], txsWithPoolEvent=agg['txsWithPoolEvent'], poolsUnknown=agg['poolsUnknown'], nativeLogs=agg['nativeLogs'], blockTime=bt), gzip.open('raw/census2_%d%s.json.gz' % (cid, tag), 'wt'))
        a = b + 1
    print(cid, n['name'], 'DONE txs', agg['txs'], 'poolTx', agg['txsWithPoolEvent'], 'unknownPools', agg['poolsUnknown'], dict(C), 'fails', dict(agg['fails']), flush=True)
def segment(cid, B1, B2):
    n = net(cid); c = dict(CFG[cid]); pm = n['poolManager'].lower(); u = c['logs']
    if cid in LOGSRC: u, c['chunk'], c['workers'] = LOGSRC[cid]
    tx = {}; lock = threading.Lock(); p = pad_addr(pm); newpools = {}
    def ent(h, b):
        e = tx.get(h)
        if e is None: e = tx[h] = {'b': b, 'tok': {}, 'sw': {}, 'ml': set(), 'dn': {}, 'rc': {}}
        return e
    def tk(e, a): 
        x = e['tok'].get(a)
        if x is None: x = e['tok'][a] = [0, 0, 0, 0]
        return x
    def on_tr(logs):
        with lock:
            for l in logs:
                t = l['topics']
                if l.get('removed'): continue
                a = l['address'].lower()[2:]
                if a == NATLOG: a = Z40
                elif cid == 5042 and a == ARCUSDC: continue   # Arc logs each move of the USDC face a second time at 0xff..fe in 18 decimals
                if len(t) == 3 and t[0] == TRANSFER and len(l['data']) == 66:
                    v = int(l['data'], 16); e = ent(l['transactionHash'], int(l['blockNumber'], 16))
                    if t[1] == p:
                        tk(e, a)[0] += v; k = (a, t[2][-40:]); e['rc'][k] = e['rc'].get(k, 0) + v
                    if t[2] == p: tk(e, a)[1] += v
                elif len(t) == 2 and t[0] == DEPOSIT and t[1] == p and len(l['data']) == 66:
                    tk(ent(l['transactionHash'], int(l['blockNumber'], 16)), a)[1] += int(l['data'], 16)
    def on_pm(logs):
        with lock:
            for l in logs:
                t = l['topics']
                if l.get('removed') or not t: continue
                e = ent(l['transactionHash'], int(l['blockNumber'], 16)); d = l['data'][2:]
                if t[0] == SWAP:
                    s = e['sw'].setdefault(t[1], [0, 0]); s[0] += s128(d[0:64]); s[1] += s128(d[64:128])
                elif t[0] == MODL: e['ml'].add(t[1])
                elif t[0] == DON:
                    s = e['dn'].setdefault(t[1], [0, 0]); s[0] += int(d[0:64], 16); s[1] += int(d[64:128], 16)
                elif t[0] == INIT: newpools[t[1]] = (t[2][-40:], t[3][-40:])
                elif t[0] == T6909 and len(t) == 4:
                    amt = int(d[64:128] or '0', 16)
                    if t[1] == Z: tk(e, t[3][-40:])[2] += amt
                    elif t[2] == Z: tk(e, t[3][-40:])[3] += amt
    w = c.get('workers', 4); st = {}
    st['out'] = getlogs_range(u, {'topics': [TRANSFER, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d out' % cid)
    st['in'] = getlogs_range(u, {'topics': [TRANSFER, None, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d in' % cid)
    st['dep'] = getlogs_range(u, {'topics': [DEPOSIT, p]}, B1, B2, c['chunk'], workers=w, on_logs=on_tr, label='%d dep' % cid)
    pu, pc = PMLOGS.get(cid, (u, c['chunk'])) if cid not in LOGSRC else (u, c['chunk'])
    st['pm'] = getlogs_range(pu, {'address': n['poolManager']}, B1, B2, pc, workers=w, on_logs=on_pm, label='%d pm' % cid)
    for k in st: st[k] = {'req': st[k]['req'], 'logs': st[k]['logs'], 'nFail': len(st[k]['fail']), 'fail': st[k]['fail'][:5]}
    ids = set()
    for e in tx.values(): ids.update(e['sw']); ids.update(e['ml']); ids.update(e['dn'])
    pmap = pool_map(cid, ids); pmap.update(newpools)
    natlogs = any(Z40 in e['tok'] and (e['tok'][Z40][0] or e['tok'][Z40][1]) for e in tx.values())
    alias = {ARCUSDC: Z40} if cid == 5042 else {}; scale = {ARCUSDC: 10 ** 12} if cid == 5042 else {}
    flagged = []; C = collections.Counter(); blocksum = collections.defaultdict(int)
    for h, e in tx.items():
        unk = any(i not in pmap for i in list(e['sw']) + list(e['ml']) + list(e['dn']))
        owed = collections.defaultdict(int); liq = set()
        for i, (a0, a1) in e['sw'].items():
            if i in pmap: c0, c1 = pmap[i]; owed[alias.get(c0, c0)] += a0 * scale.get(c0, 1); owed[alias.get(c1, c1)] += a1 * scale.get(c1, 1)
        for i, (a0, a1) in e['dn'].items():
            if i in pmap: c0, c1 = pmap[i]; owed[alias.get(c0, c0)] -= a0 * scale.get(c0, 1); owed[alias.get(c1, c1)] -= a1 * scale.get(c1, 1)
        for i in e['ml']:
            if i in pmap: liq.update(alias.get(x, x) for x in pmap[i])
        toks = collections.defaultdict(lambda: [0, 0, 0, 0])
        for a, v in e['tok'].items():
            x = toks[alias.get(a, a)]
            for k in range(4): x[k] += v[k] * scale.get(a, 1)
        haspool = bool(e['sw'] or e['ml'] or e['dn'])
        for a, (o, i, m, bn) in toks.items():
            if a == Z40 and not natlogs: C['native-no-logs'] += 1; continue
            C['rows'] += 1; netv = o + m - i - bn
            if netv <= owed.get(a, 0): C['ok'] += 1; continue
            if a in liq: C['skipped-liquidity'] += 1; continue
            if unk: C['skipped-unknown-pool'] += 1; continue
            C['flagged'] += 1; C['flagged-pooltx' if haspool else 'flagged-nopool'] += 1
            rc = sorted(((v, r) for (ta, r), v in e['rc'].items() if alias.get(ta, ta) == a), reverse=True)[:3]
            flagged.append(dict(tx=h, block=e['b'], token='0x' + a, out=str(o), mint=str(m), burn=str(bn), owed=str(owed.get(a, 0)), excess=str(netv - owed.get(a, 0)), poolTx=haspool,
                                recipients=[['0x' + r, str(v)] for v, r in rc], **{'in': str(i)}))
    return dict(stats=st, txs=len(tx), txsWithPoolEvent=sum(1 for e in tx.values() if e['sw'] or e['ml'] or e['dn']), poolsUnknown=len([i for i in ids if i not in pmap]), nativeLogs=natlogs, counts=dict(C), flagged=flagged)
if __name__ == '__main__':
    run(int(sys.argv[1]), float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else '')
