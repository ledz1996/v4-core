"""For each mined ModifyLiquidity with liquidityDelta <= 0, compute what the source says the PoolManager owed
(principal by SqrtPriceMath at slot0, fees by Position.update at the parent block) and compare it with what
left the PoolManager in the same transaction. Usage: analyze.py <chainId> <mod.json> <out.json> [max]"""
import sys, json, concurrent.futures as cf
from lib import *
import v4math as m
from evm import u
cid, src, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]
MAX = int(sys.argv[4]) if len(sys.argv) > 4 else 100000
net = NETS[cid]; PM = net['poolManager'].lower(); POSM = net['contracts']['PositionManager'].lower()
SU = STATE_URLS[cid]
SEL_EXT2 = keccak(b'extsload(bytes32,uint256)')[:4].hex()
SEL_PK = keccak(b'poolKeys(bytes25)')[:4].hex()
Q128 = 1 << 128

def ext(slot, n, block):
    r = rpc(cid, 'eth_call', [{'to': PM, 'data': '0x' + SEL_EXT2 + (slot % (1 << 256)).to_bytes(32, 'big').hex() + n.to_bytes(32, 'big').hex()}, hex(block)], urls=SU)
    d = bytes.fromhex(r[2:]); assert len(d) == 64 + 32 * n, (len(d), n)
    return [int.from_bytes(d[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]

def H(*words): return int.from_bytes(keccak(b''.join(w.to_bytes(32, 'big') for w in words)), 'big')

keycache = {}
def poolkey(pid):
    if pid in keycache: return keycache[pid]
    r = rpc(cid, 'eth_call', [{'to': POSM, 'data': '0x' + SEL_PK + pid[2:52] + '00' * 7}, 'latest'], urls=SU)
    w = [int(r[2 + 64 * i:66 + 64 * i], 16) for i in range(5)]
    ok = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex() == pid
    keycache[pid] = {'c0': '0x%040x' % w[0], 'c1': '0x%040x' % w[1], 'fee': w[2], 'spacing': s256(w[3]), 'hooks': '0x%040x' % w[4]} if ok else None
    return keycache[pid]

blockcache = {}
def block_pm_logs(b):
    if b not in blockcache:
        blockcache[b] = rpc(cid, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}])
    return blockcache[b]

def native_flows(tx):
    t = rpc(cid, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], urls=TRACE_URLS.get(cid, SU), timeout=120)
    outv = inv = 0
    def walk(c):
        nonlocal outv, inv
        if c.get('error'): return  # value of a reverted frame does not move
        v = int(c.get('value', '0x0') or '0x0', 16)
        if c.get('type') in ('CALL', 'CALLCODE', 'CREATE', 'CREATE2', 'SELFDESTRUCT'):
            if c.get('from', '').lower() == PM: outv += v
            if (c.get('to') or '').lower() == PM: inv += v
        for k in c.get('calls', []) or []: walk(k)
    walk(t)
    return outv, inv
TRACE_URLS = {999: ['https://hyperliquid.drpc.org']}

def amounts(sp, tick, tl, tu, liq):
    # Pool.modifyLiquidity lines 206-235 with liquidityDelta = -liq (round down, owed to the caller)
    pl, pu = m.get_sqrt_price_at_tick(tl), m.get_sqrt_price_at_tick(tu)
    if tick < tl: return m.amount0_delta(pl, pu, liq, False), 0
    if tick < tu: return m.amount0_delta(sp, pu, liq, False), m.amount1_delta(pl, sp, liq, False)
    return 0, m.amount1_delta(pl, pu, liq, False)

def one(lg):
    r = {'tx': lg['transactionHash'], 'block': int(lg['blockNumber'], 16)}
    pid = lg['topics'][1]; owner = '0x' + lg['topics'][2][26:]
    d = lg['data']; w = [int(d[2 + 64 * i:66 + 64 * i], 16) for i in range(4)]
    tl, tu, delta, salt = s256(w[0]), s256(w[1]), s256(w[2]), w[3]
    r.update(pool=pid, owner=owner, tl=tl, tu=tu, delta=delta, kind='collect' if delta == 0 else 'remove')
    N = r['block']
    bl = block_pm_logs(N)
    same_pool = [x for x in bl if len(x['topics']) > 1 and x['topics'][1] == pid]
    if len(same_pool) != 1: r['aside'] = 'pool touched by another PoolManager event in the block'; return r
    in_tx = [x for x in bl if x['transactionHash'] == lg['transactionHash']]
    key = poolkey(pid)
    if key is None: r['aside'] = 'pool key not found'; return r
    r['key'] = key
    hk = int(key['hooks'], 16)
    if hk & ((1 << 9) | (1 << 8) | 1): r['aside'] = 'hook with remove-liquidity permissions'; return r
    base = H(int(pid, 16), 6)
    s0, fg0, fg1, pliq = ext(base, 4, N - 1)
    lo = ext(H(u(tl), base + 4), 3, N - 1); up = ext(H(u(tu), base + 4), 3, N - 1)
    pk = int.from_bytes(keccak(bytes.fromhex(owner[2:]) + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt.to_bytes(32, 'big')), 'big')
    pos0 = ext(H(pk, base + 6), 3, N - 1); pos1 = ext(H(pk, base + 6), 3, N)
    s0b = ext(base, 1, N)[0]
    sp = s0 & ((1 << 160) - 1); tick = s256(m.ref_signextend(2, (s0 >> 160) & 0xffffff))
    if s0b != s0: r['aside'] = 'slot0 changed in the block'; return r
    M = (1 << 256) - 1
    if tick < tl: fi = [(lo[1] - up[1]) & M, (lo[2] - up[2]) & M]
    elif tick >= tu: fi = [(up[1] - lo[1]) & M, (up[2] - lo[2]) & M]
    else: fi = [(fg0 - lo[1] - up[1]) & M, (fg1 - lo[2] - up[2]) & M]
    liq = pos0[0]
    r['posLiq'] = str(liq)
    r['insideMatchesStored'] = fi == pos1[1:3]
    r['liqAfterOk'] = pos1[0] == liq + delta
    fees = [m.mul_div((fi[i] - pos0[1 + i]) & M, liq, Q128) for i in range(2)]
    prin = amounts(sp, tick, tl, tu, -delta) if delta else (0, 0)
    owed = [prin[0] + fees[0], prin[1] + fees[1]]
    r.update(tick=tick, principal=[str(x) for x in prin], fees=[str(x) for x in fees], owed=[str(x) for x in owed])
    # what left the PoolManager in the transaction
    if len(in_tx) != 1: r['aside'] = 'other PoolManager events in the transaction'; return r
    rc = rpc(cid, 'eth_getTransactionReceipt', [lg['transactionHash']], urls=SU)
    if rc['status'] != '0x1': r['aside'] = 'receipt status not 1'; return r
    paid = []
    for i, c in enumerate((key['c0'], key['c1'])):
        if int(c, 16) == 0:
            o, n_in = native_flows(lg['transactionHash'])
            paid.append({'out': str(o), 'in': str(n_in), 'via': 'trace'})
        else:
            o = n_in = 0
            for x in rc['logs']:
                if x['address'].lower() == c and x['topics'][0] == TRANSFER and len(x['topics']) == 3:
                    v = int(x['data'][:66], 16)
                    if '0x' + x['topics'][1][26:] == PM: o += v
                    if '0x' + x['topics'][2][26:] == PM: n_in += v
            paid.append({'out': str(o), 'in': str(n_in), 'via': 'Transfer'})
    r['paid'] = paid
    res = []
    for i in range(2):
        o, n_in = int(paid[i]['out']), int(paid[i]['in'])
        if n_in: res.append('inflow'); continue
        diff = o - owed[i]
        res.append('exact' if diff == 0 else ('over %d' % diff if diff > 0 else 'under %d' % -diff))
    r['result'] = res
    return r

if __name__ == '__main__':
    logs = json.load(open(src))['logs']
    logs = [l for l in logs if s256(int(l['data'][2 + 128:2 + 192], 16)) <= 0]
    logs.sort(key=lambda l: (-int(l['blockNumber'], 16), -int(l['logIndex'], 16)))
    logs = logs[:MAX]
    def safe(l):
        try: return one(l)
        except Exception as e: return {'tx': l['transactionHash'], 'block': int(l['blockNumber'], 16), 'error': str(e)[:200]}
    with cf.ThreadPoolExecutor(int(sys.argv[5]) if len(sys.argv) > 5 else 4) as ex:
        res = list(ex.map(safe, logs))
    json.dump({'chainId': cid, 'results': res}, open(out, 'w'), indent=1)
    from collections import Counter
    print(cid, 'n', len(res), Counter(r.get('aside') or ('error' if 'error' in r else 'checked') for r in res))
    print(cid, Counter((r['kind'], tuple(r['result'])) for r in res if 'result' in r).most_common(20))
    print(cid, 'insideMatchesStored', Counter(r.get('insideMatchesStored') for r in res if 'insideMatchesStored' in r), 'liqAfterOk', Counter(r.get('liqAfterOk') for r in res if 'liqAfterOk' in r))
