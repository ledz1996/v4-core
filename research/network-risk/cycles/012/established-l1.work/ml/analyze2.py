"""Transaction-level check of mined liquidity removals and fee collections.
A transaction is taken when every PoolManager event in it is ModifyLiquidity and no other transaction in the
block emitted a PoolManager event for the same pools. The script then reruns Pool.modifyLiquidity and
Position.update (src/libraries/Pool.sol:146-237, 488-511, 520-557, src/libraries/Position.sol:79-104) in order on
the PoolManager's storage at the parent block, read with extsload, and compares
  (a) the storage it predicts with the storage at the block (positions, ticks, pool liquidity), and
  (b) what the source says the PoolManager owed, per currency, with what left it in the transaction
      (ERC-20 Transfer logs, native value from debug_traceTransaction callTracer).
Usage: analyze2.py <chainId> <mod.json> <out.json> [max_tx] [threads]"""
import sys, json, concurrent.futures as cf
from collections import Counter, defaultdict
from lib import *
import v4math as m
from evm import u
cid, src, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]
MAXTX = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9
THREADS = int(sys.argv[5]) if len(sys.argv) > 5 else 4
import os
ALLOW_SWAP = os.environ.get('ALLOW_SWAP') == '1'
net = NETS[cid]; PM = net['poolManager'].lower(); POSM = net['contracts']['PositionManager'].lower()
SU = STATE_URLS[cid]
TRACE_URLS = {137: ['https://rpc-mainnet.matic.quiknode.pro']}
SEL_EXT2 = keccak(b'extsload(bytes32,uint256)')[:4].hex()
SEL_PK = keccak(b'poolKeys(bytes25)')[:4].hex()
Q128 = 1 << 128; M = (1 << 256) - 1; M128 = (1 << 128) - 1
LIQ_HOOK_BITS = (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | 2 | 1

def ext(slot, n, block):
    r = rpc(cid, 'eth_call', [{'to': PM, 'data': '0x' + SEL_EXT2 + (slot & M).to_bytes(32, 'big').hex() + n.to_bytes(32, 'big').hex()}, hex(block)], urls=SU)
    d = bytes.fromhex(r[2:]); assert len(d) == 64 + 32 * n, (len(d), n)
    return [int.from_bytes(d[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]

def H(*words): return int.from_bytes(keccak(b''.join((w & M).to_bytes(32, 'big') for w in words)), 'big')
def s128(x): return x - (1 << 128) if x >> 127 else x

keycache = {}
try:
    INITKEYS = json.load(open('raw/inits-%d.json' % cid))
except Exception:  # noqa
    INITKEYS = {}
def poolkey(pid):
    if pid not in keycache:
        r = rpc(cid, 'eth_call', [{'to': POSM, 'data': '0x' + SEL_PK + pid[2:52] + '00' * 7}, 'latest'], urls=SU)
        w = [int(r[2 + 64 * i:66 + 64 * i], 16) for i in range(5)]
        ok = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex() == pid
        if not ok and pid in INITKEYS:
            k = INITKEYS[pid]; w = [int(k['c0'], 16), int(k['c1'], 16), k['fee'], k['spacing'] & ((1 << 256) - 1), int(k['hooks'], 16)]
            ok = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex() == pid
        keycache[pid] = {'c0': '0x%040x' % w[0], 'c1': '0x%040x' % w[1], 'fee': w[2], 'spacing': s256(w[3]), 'hooks': '0x%040x' % w[4]} if ok else None
    return keycache[pid]

def native_flows(tx):
    t = rpc(cid, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], urls=TRACE_URLS.get(cid, SU), timeout=120)
    acc = [0, 0]
    def walk(c, ok):
        ok = ok and not c.get('error')  # a reverted frame moves no value
        v = int(c.get('value') or '0x0', 16)
        if ok and c.get('type') in ('CALL', 'CREATE', 'CREATE2', 'SELFDESTRUCT') and v:
            if (c.get('from') or '').lower() == PM: acc[0] += v
            if (c.get('to') or '').lower() == PM: acc[1] += v
        for k in c.get('calls') or []: walk(k, ok)
    walk(t, True)
    return acc

def amounts(sp, tick, tl, tu, delta):
    """signed principal, positive = owed to the caller (Pool.sol:206-235, SqrtPriceMath.sol:261-288)"""
    pl, pu = m.get_sqrt_price_at_tick(tl), m.get_sqrt_price_at_tick(tu)
    up = delta > 0; L = abs(delta); sg = -1 if up else 1
    if tick < tl: return sg * m.amount0_delta(pl, pu, L, up), 0
    if tick < tu: return sg * m.amount0_delta(sp, pu, L, up), sg * m.amount1_delta(pl, sp, L, up)
    return 0, sg * m.amount1_delta(pl, pu, L, up)

class PoolSim:
    def __init__(self, pid, N):
        self.pid, self.N = pid, N; self.base = H(int(pid, 16), 6)
        s0, self.fg0, self.fg1, self.liq = ext(self.base, 4, N - 1)
        self.s0 = s0; self.sp = s0 & ((1 << 160) - 1); self.tick = s256(m.ref_signextend(2, (s0 >> 160) & 0xffffff))
        self.ticks = {}; self.pos = {}; self.swapped = False
    def T(self, t):
        if t not in self.ticks:
            w = ext(H(u(t), self.base + 4), 3, self.N - 1)
            self.ticks[t] = [w[0] & M128, s128(w[0] >> 128), w[1], w[2]]
        return self.ticks[t]
    def P(self, k):
        if k not in self.pos: self.pos[k] = ext(H(k, self.base + 6), 3, self.N - 1)
        return self.pos[k]
    def update_tick(self, t, delta, upper):
        info = self.T(t); g0 = info[0]; g1 = g0 + delta
        if g1 < 0 or g1 >> 128: raise ValueError('gross out of range')
        flipped = (g1 == 0) != (g0 == 0)
        if g0 == 0 and t <= self.tick: info[2], info[3] = self.fg0, self.fg1
        info[0] = g1; info[1] = info[1] - delta if upper else info[1] + delta
        return flipped
    def modify(self, owner, tl, tu, delta, salt):
        fl = fu = False
        if delta != 0:
            fl = self.update_tick(tl, delta, False); fu = self.update_tick(tu, delta, True)
        lo, up = self.T(tl), self.T(tu)
        if self.tick < tl: fi = [(lo[2] - up[2]) & M, (lo[3] - up[3]) & M]
        elif self.tick >= tu: fi = [(up[2] - lo[2]) & M, (up[3] - lo[3]) & M]
        else: fi = [(self.fg0 - lo[2] - up[2]) & M, (self.fg1 - lo[3] - up[3]) & M]
        pk = int.from_bytes(keccak(bytes.fromhex(owner[2:]) + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt.to_bytes(32, 'big')), 'big')
        p = self.P(pk); L = p[0]
        if delta == 0 and L == 0: raise ValueError('poke of empty position')
        if self.swapped and L: raise Aside('fees of a position touched after a swap in the same transaction')
        fees = [m.mul_div((fi[i] - p[1 + i]) & M, L, Q128) for i in range(2)]
        p[0] = L + delta; p[1], p[2] = fi
        if delta < 0:
            if fl: self.ticks[tl] = [0, 0, 0, 0]
            if fu: self.ticks[tu] = [0, 0, 0, 0]
        prin = (0, 0)
        if delta != 0:
            prin = amounts(self.sp, self.tick, tl, tu, delta)
            if tl <= self.tick < tu: self.liq += delta
        return prin, fees, L
    def swap(self, sp, tick, liq):
        self.swapped = True; self.sp, self.tick, self.liq = sp, tick, liq
    def verify(self):
        bad = []
        s0 = ext(self.base, 1, self.N)[0]
        if self.swapped:
            if (s0 & ((1 << 160) - 1), s256(m.ref_signextend(2, (s0 >> 160) & 0xffffff))) != (self.sp, self.tick): bad.append('slot0')
            if ext(self.base + 3, 1, self.N)[0] != self.liq: bad.append('liquidity')
            return bad  # fee growth and crossed ticks after a swap are not modelled
        if s0 != self.s0: bad.append('slot0')
        if ext(self.base + 3, 1, self.N)[0] != self.liq: bad.append('liquidity')
        for t, v in self.ticks.items():
            w = ext(H(u(t), self.base + 4), 3, self.N)
            if [w[0] & M128, s128(w[0] >> 128), w[1], w[2]] != v: bad.append('tick %d' % t)
        for k, v in self.pos.items():
            if ext(H(k, self.base + 6), 3, self.N) != v: bad.append('position %x' % k)
        return bad

class Aside(Exception): pass
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
blockcache = {}
def block_pm_logs(b):
    if b not in blockcache: blockcache[b] = rpc(cid, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}])
    return blockcache[b]

def one(tx, N):
    r = {'tx': tx, 'block': N}
    bl = block_pm_logs(N)
    mine = sorted([x for x in bl if x['transactionHash'] == tx], key=lambda x: int(x['logIndex'], 16))
    r['events'] = len(mine)
    if any(x['topics'][0] not in (MOD, SWAP) for x in mine): r['aside'] = 'other PoolManager events in the transaction'; return r
    nsw = sum(1 for x in mine if x['topics'][0] == SWAP); r['swaps'] = nsw
    if nsw and not ALLOW_SWAP: r['aside'] = 'swap in the transaction'; return r
    pools = {x['topics'][1] for x in mine}
    if any(x['transactionHash'] != tx and len(x['topics']) > 1 and x['topics'][1] in pools for x in bl):
        r['aside'] = 'pool touched by another transaction in the block'; return r
    keys = {}
    for p in pools:
        k = poolkey(p)
        if k is None: r['aside'] = 'pool key not found'; return r
        if int(k['hooks'], 16) & LIQ_HOOK_BITS: r['aside'] = 'hook with liquidity permissions'; return r
        keys[p] = k
    sims = {p: PoolSim(p, N) for p in pools}
    owed = defaultdict(int); evs = []
    for x in mine:
        if x['topics'][0] == SWAP:
            d = x['data']; w = [int(d[2 + 64 * i:66 + 64 * i], 16) for i in range(6)]
            k = keys[x['topics'][1]]; a0, a1 = s256(w[0]), s256(w[1])
            owed[k['c0']] += a0; owed[k['c1']] += a1
            sims[x['topics'][1]].swap(w[2], s256(m.ref_signextend(2, w[4] & 0xffffff)), w[3])
            evs.append({'pool': x['topics'][1], 'swap': [str(a0), str(a1)]}); continue
        d = x['data']; w = [int(d[2 + 64 * i:66 + 64 * i], 16) for i in range(4)]
        tl, tu, delta, salt = s256(w[0]), s256(w[1]), s256(w[2]), w[3]
        owner = '0x' + x['topics'][2][26:]
        try:
            prin, fees, L = sims[x['topics'][1]].modify(owner, tl, tu, delta, salt)
        except Aside as e:
            r['aside'] = str(e); return r
        k = keys[x['topics'][1]]
        for i, c in enumerate((k['c0'], k['c1'])): owed[c] += prin[i] + fees[i]
        evs.append({'pool': x['topics'][1], 'tl': tl, 'tu': tu, 'delta': str(delta), 'liqBefore': str(L), 'principal': [str(prin[0]), str(prin[1])], 'fees': [str(fees[0]), str(fees[1])]})
    r['detail'] = evs
    r['kind'] = ('collect' if evs[0]['delta'] == '0' else ('remove' if int(evs[0]['delta']) < 0 else 'add')) if len(evs) == 1 else ('multi+swap' if nsw else 'multi')
    r['removals'] = sum(1 for e in evs if 'delta' in e and int(e['delta']) < 0); r['collects'] = sum(1 for e in evs if e.get('delta') == '0')
    bad = []
    for s_ in sims.values(): bad += s_.verify()
    r['storageMismatch'] = bad
    rc = rpc(cid, 'eth_getTransactionReceipt', [tx], urls=SU)
    if rc['status'] != '0x1': r['aside'] = 'receipt status not 1'; return r
    flows = {}
    for c in owed:
        if int(c, 16) == 0:
            # producer-written evidence: the PoolManager's native balance at the block and its parent
            bd = int(rpc(cid, 'eth_getBalance', [PM, hex(N)], urls=SU), 16) - int(rpc(cid, 'eth_getBalance', [PM, hex(N - 1)], urls=SU), 16)
            other = any(x['transactionHash'] != tx for x in bl)
            r['native'] = {'balanceDiff': str(bd), 'otherPmTxInBlock': other}
            try:
                flows[c] = native_flows(tx); r['native']['via'] = 'trace'
            except Exception as e:  # noqa  no tracer on this endpoint: fall back to the balance difference
                if 'not supported' not in str(e) and 'not found' not in str(e).lower(): raise
                flows[c] = [max(0, -bd), max(0, bd)]; r['native']['via'] = 'balance'
        else:
            o = i_ = 0
            for x in rc['logs']:
                if x['address'].lower() == c and x['topics'] and x['topics'][0] == TRANSFER and len(x['topics']) == 3:
                    v = int(x['data'][2:66], 16)
                    if '0x' + x['topics'][1][26:] == PM: o += v
                    if '0x' + x['topics'][2][26:] == PM: i_ += v
            flows[c] = [o, i_]
    res = {}
    for c, ow in owed.items():
        o, i_ = flows[c]; diff = (o - i_) - ow
        res[c] = {'owed': str(ow), 'out': str(o), 'in': str(i_), 'diff': str(diff)}
    r['currencies'] = res
    r['result'] = 'exact' if all(v['diff'] == '0' for v in res.values()) else ('over' if any(int(v['diff']) > 0 for v in res.values()) else 'under')
    return r

if __name__ == '__main__':
    logs = json.load(open(src))['logs']
    txs = {}
    for l in logs:
        if s256(int(l['data'][2 + 128:2 + 192], 16)) <= 0: txs[l['transactionHash']] = int(l['blockNumber'], 16)
    jobs = sorted(txs.items(), key=lambda kv: -kv[1])[:MAXTX]
    done = [0]
    def safe(j):
        done[0] += 1
        if done[0] % 50 == 0: print('progress', done[0], flush=True)
        try: return one(*j)
        except Exception as e: return {'tx': j[0], 'block': j[1], 'error': str(e)[:200]}
    with cf.ThreadPoolExecutor(THREADS) as ex: res = list(ex.map(safe, jobs))
    json.dump({'chainId': cid, 'results': res}, open(out, 'w'), indent=1)
    print(cid, 'tx', len(res), dict(Counter(r.get('aside') or ('error' if 'error' in r else 'checked') for r in res)))
    print(cid, 'results', dict(Counter((r['kind'], r['result']) for r in res if 'result' in r)))
    print(cid, 'storage mismatches', sum(1 for r in res if r.get('storageMismatch')), 'errors', Counter(r['error'][:60] for r in res if 'error' in r).most_common(5))
