"""Block-level rerun of mined liquidity removals and fee collections, including transactions that also swap,
donate, mint or burn ERC-6909 claims, and pools that other transactions of the same block touch.

For a candidate transaction in block N, every pool it touches is loaded from the PoolManager's storage at N-1
(extsload) and every PoolManager event of block N on those pools is applied in log order:
  ModifyLiquidity  Pool.modifyLiquidity, Position.update, updateTick, flipTick, clearTick
                   (src/libraries/Pool.sol:145-237, 520-557, 592-594, Position.sol:79-104, TickBitmap.sol:47-71)
  Swap             the step loop of Pool.swap (src/libraries/Pool.sol:279-460) with crossTick (602-612),
                   protocol fee split (387-401) and fee growth (404-410); the swap parameters are not in the
                   event, so the candidates of tools/opdiff/replay.py are tried and only one that reproduces the
                   event's price, tick, liquidity and both amounts is accepted
  Donate           Pool.donate (src/libraries/Pool.sol:463-477)
The transaction's own events also give what the source says the PoolManager owes, per currency (principal plus
fees, swap deltas, minus donations, minus ERC-6909 mints, plus burns). That is compared with what left the
PoolManager (ERC-20 Transfer logs, native value from the call tracer, on Arc also the native Transfer logs of the
system emitter). After the whole block the predicted slot0, liquidity, fee growth, every tick touched or crossed,
every position touched and every tick bitmap word read or flipped are compared with the storage at N.
Usage: analyze3.py <chainId> <out.json> <max_tx> <threads> <mod.json> [mod.json ...]"""
import sys, json, os, concurrent.futures as cf
from collections import Counter, defaultdict
from lib import *
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from evm import u

cid, out = int(sys.argv[1]), sys.argv[2]
MAXTX, THREADS = int(sys.argv[3]), int(sys.argv[4]); SRCS = sys.argv[5:]
ONLY = set(json.load(open(os.environ['ONLY']))) if os.environ.get('ONLY') else None
net = NETS[cid]; PM = net['poolManager'].lower(); POSM = net['contracts']['PositionManager'].lower()
SU = STATE_URLS[cid]
SEL_EXT2 = keccak(b'extsload(bytes32,uint256)')[:4].hex()
SEL_PK = keccak(b'poolKeys(bytes25)')[:4].hex()
Q128 = 1 << 128; M = (1 << 256) - 1; M128 = (1 << 128) - 1
RETURN_DELTA_BITS = 0xf
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
DONATE = '0x' + keccak(b'Donate(bytes32,address,uint256,uint256)').hex()
PFU = '0x' + keccak(b'ProtocolFeeUpdated(bytes32,uint24)').hex()
INIT = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
ARC_NAT = '0xfffffffffffffffffffffffffffffffffffffffe'
BIG = (1 << 127) - 1
PLANT = os.environ.get('PLANT', '')  # sensitivity runs only: 'fg' adds 2^100 to fee growth per swap step, 'bitmap' flips the bit in the next word


def ext(slot, n, block):
    r = rpc(cid, 'eth_call', [{'to': PM, 'data': '0x' + SEL_EXT2 + (slot & M).to_bytes(32, 'big').hex() + n.to_bytes(32, 'big').hex()}, hex(block)], urls=SU)
    d = bytes.fromhex(r[2:]); assert len(d) == 64 + 32 * n, (len(d), n)
    return [int.from_bytes(d[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]


def H(*words): return int.from_bytes(keccak(b''.join((w & M).to_bytes(32, 'big') for w in words)), 'big')
def s128(x): return x - (1 << 128) if x >> 127 else x
def s24(x): return s256(m.ref_signextend(2, x & 0xffffff))


keycache = {}
INITKEYS = {}
for f in ('raw/inits-%d.json' % cid, '/home/user/v4-core/research/network-risk/cycles/011/theme-mined-liquidity.work/raw/inits-%d.json' % cid):
    try: INITKEYS.update(json.load(open(f)))
    except Exception: pass  # noqa


def poolkey(pid):
    if pid not in keycache:
        r = rpc(cid, 'eth_call', [{'to': POSM, 'data': '0x' + SEL_PK + pid[2:52] + '00' * 7}, 'latest'], urls=SU)
        w = [int(r[2 + 64 * i:66 + 64 * i], 16) for i in range(5)]
        ok = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex() == pid
        if not ok and pid in INITKEYS:
            k = INITKEYS[pid]; w = [int(k['c0'], 16), int(k['c1'], 16), k['fee'], k['spacing'] & M, int(k['hooks'], 16)]
            ok = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex() == pid
        keycache[pid] = {'c0': '0x%040x' % w[0], 'c1': '0x%040x' % w[1], 'fee': w[2], 'spacing': s256(w[3]), 'hooks': '0x%040x' % w[4]} if ok else None
    return keycache[pid]


def harvest_keys(tx):
    """Pool keys from the calldata of the transaction's own PoolManager frames (swap, modifyLiquidity, donate,
    initialize take the PoolKey as their first five words); each is accepted only if it hashes to the id."""
    try: t = rpc(cid, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], urls=TRACE_URLS.get(cid, SU), timeout=120, tries=4)
    except Exception: return False  # noqa
    got = [False]
    def walk(c):
        inp = (c.get('input') or '').lower()
        if (c.get('to') or '').lower() == PM and inp[:10] in ('0xf3cd914c', '0x5a6bcfda', '0x234266d7', '0x6276cbbe') and len(inp) >= 10 + 320:
            w = [int(inp[10 + 64 * i:74 + 64 * i], 16) for i in range(5)]
            pid = '0x' + keccak(b''.join(x.to_bytes(32, 'big') for x in w)).hex()
            if keycache.get(pid) is None:
                keycache[pid] = {'c0': '0x%040x' % w[0], 'c1': '0x%040x' % w[1], 'fee': w[2], 'spacing': s256(w[3]), 'hooks': '0x%040x' % w[4]}; got[0] = True
        for k in c.get('calls') or []: walk(k)
    walk(t)
    return got[0]


def native_flows(tx):
    t = rpc(cid, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], urls=TRACE_URLS.get(cid, SU), timeout=120, tries=4)
    acc = [0, 0]

    def walk(c, ok):
        ok = ok and not c.get('error')
        v = int(c.get('value') or '0x0', 16)
        if ok and c.get('type') in ('CALL', 'CREATE', 'CREATE2', 'SELFDESTRUCT') and v:
            if (c.get('from') or '').lower() == PM: acc[0] += v
            if (c.get('to') or '').lower() == PM: acc[1] += v
        for k in c.get('calls') or []: walk(k, ok)
    walk(t, True)
    return acc


def amounts(sp, tick, tl, tu, delta):
    pl, pu = m.get_sqrt_price_at_tick(tl), m.get_sqrt_price_at_tick(tu)
    up = delta > 0; L = abs(delta); sg = -1 if up else 1
    if tick < tl: return sg * m.amount0_delta(pl, pu, L, up), 0
    if tick < tu: return sg * m.amount0_delta(sp, pu, L, up), sg * m.amount1_delta(pl, sp, L, up)
    return 0, sg * m.amount1_delta(pl, pu, L, up)


def compress(tick, sp):
    q = abs(tick) // sp; q = -q if tick < 0 else q
    return q - (1 if (tick < 0 and tick % sp != 0) else 0)


class Aside(Exception): pass


class PoolSim:
    def __init__(self, pid, N, spacing):
        self.pid, self.N, self.spacing = pid, N, spacing; self.base = H(int(pid, 16), 6)
        s0, self.fg0, self.fg1, self.liq = ext(self.base, 4, N - 1)
        self.fresh = s0 == 0  # initialized inside block N; the Initialize event sets the state (src/libraries/Pool.sol:99-111)
        self.sp = s0 & ((1 << 160) - 1); self.tick = s24(s0 >> 160)
        self.pfee = (s0 >> 184) & 0xffffff; self.lpfee = (s0 >> 208) & 0xffffff; self.s0_hi = s0 >> 208
        self.ticks = {}; self.pos = {}; self.words = {}; self.swaps = 0; self.crossed = 0; self.steps = 0
        self.flips = 0; self.donates = 0

    def T(self, t):
        if t not in self.ticks:
            w = ext(H(u(t), self.base + 4), 3, self.N - 1)
            self.ticks[t] = [w[0] & M128, s128(w[0] >> 128), w[1], w[2]]
        return self.ticks[t]

    def P(self, k):
        if k not in self.pos: self.pos[k] = ext(H(k, self.base + 6), 3, self.N - 1)
        return self.pos[k]

    def W(self, wp):
        if wp not in self.words: self.words[wp] = ext(H(u(wp), self.base + 5), 1, self.N - 1)[0]
        return self.words[wp]

    def flip(self, t):
        if t % self.spacing: raise ValueError('misaligned tick')
        c = int(t / self.spacing)  # exact, t is a multiple
        wp, bit = c >> 8, c & 0xff
        if PLANT == 'bitmap': wp += 1
        self.words[wp] = self.W(wp) ^ (1 << bit); self.flips += 1

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
            if fl: self.flip(tl)
            if fu: self.flip(tu)
        lo, up = self.T(tl), self.T(tu)
        if self.tick < tl: fi = [(lo[2] - up[2]) & M, (lo[3] - up[3]) & M]
        elif self.tick >= tu: fi = [(up[2] - lo[2]) & M, (up[3] - lo[3]) & M]
        else: fi = [(self.fg0 - lo[2] - up[2]) & M, (self.fg1 - lo[3] - up[3]) & M]
        pk = int.from_bytes(keccak(bytes.fromhex(owner[2:]) + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt.to_bytes(32, 'big')), 'big')
        p = self.P(pk); L = p[0]
        if delta == 0 and L == 0: raise ValueError('poke of empty position')
        fees = [m.mul_div((fi[i] - p[1 + i]) & M, L, Q128) for i in range(2)]
        p[0] = L + delta; p[1], p[2] = fi
        if delta < 0:
            if fl: self.ticks[tl] = [0, 0, 0, 0]
            if fu: self.ticks[tu] = [0, 0, 0, 0]
        prin = (0, 0)
        if delta != 0:
            prin = amounts(self.sp, self.tick, tl, tu, delta)
            if tl <= self.tick < tu:
                self.liq += delta
                if self.liq < 0 or self.liq >> 128: raise ValueError('pool liquidity out of range')
        return prin, fees, L

    def next_tick(self, tick, lte):
        sp = self.spacing; c = compress(tick, sp)
        if lte:
            wp, bit = c >> 8, c & 0xff
            masked = self.W(wp) & (M >> (255 - bit))
            return ((c - (bit - m.most_significant_bit(masked))) * sp, True) if masked else ((c - bit) * sp, False)
        c += 1; wp, bit = c >> 8, c & 0xff
        masked = self.W(wp) & (M ^ ((1 << bit) - 1))
        return ((c + (m.least_significant_bit(masked) - bit)) * sp, True) if masked else ((c + (255 - bit)) * sp, False)

    def run_swap(self, zfo, amount, limit, fee):
        """Pool.swap on a scratch copy of the touched state; returns the result and the writes to commit."""
        pf = (self.pfee & 0xfff) if zfo else (self.pfee >> 12)
        if fee >= m.MAX_SWAP_FEE and amount > 0: raise m.Revert('exact out at full fee')
        p, tick, liq = self.sp, self.tick, self.liq
        rem, calc = amount, 0; fg = self.fg0 if zfo else self.fg1; prot = 0
        tw = {}; steps = 0; crossed = 0
        while not (rem == 0 or p == limit):
            steps += 1
            if steps > 5000: raise m.Revert('too many steps')
            start = p
            tn, init = self.next_tick(tick, zfo)
            tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
            pn = m.get_sqrt_price_at_tick(tn)
            target = (pn if pn >= limit else limit) if zfo else (pn if pn < limit else limit)  # SwapMath.getSqrtPriceTarget
            p, a_in, a_out, f = m.compute_swap_step(p, target, liq, rem, fee)
            if amount > 0: rem -= a_out; calc -= a_in + f
            else: rem += a_in + f; calc += a_out
            if pf > 0:
                d = f if fee == pf else ((a_in + f) * pf) // 1000000
                f -= d; prot += d
            if liq > 0: fg = (fg + ((f * Q128) & M) // liq + (1 << 100 if PLANT == 'fg' else 0)) & M
            if p == pn:
                if init:
                    info = list(tw[tn]) if tn in tw else list(self.T(tn))
                    g0, g1 = (fg, self.fg1) if zfo else (self.fg0, fg)
                    info[2] = (g0 - info[2]) & M; info[3] = (g1 - info[3]) & M
                    tw[tn] = info; net_ = info[1]; crossed += 1
                    if zfo: net_ = -net_
                    liq = liq + net_
                    if liq < 0 or liq >> 128: raise m.Revert('liquidity out of range')
                tick = tn - 1 if zfo else tn
            elif p != start:
                tick = m.get_tick_at_sqrt_price(p)
        if zfo != (amount < 0): d0, d1 = calc, amount - rem
        else: d0, d1 = amount - rem, calc
        return {'p': p, 'tick': tick, 'liq': liq, 'fg': fg, 'd0': d0, 'd1': d1, 'tw': tw, 'steps': steps, 'crossed': crossed, 'prot': prot}

    def swap(self, a0, a1, p1, liq1, tick1, fee):
        zfos = [True] if p1 < self.sp else ([False] if p1 > self.sp else [True, False])
        for zfo in zfos:
            inp, outp = (a0, a1) if zfo else (a1, a0)  # event amounts: negative is paid in by the caller
            edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            cands = [(inp, edge), (outp, edge), (inp, p1), (outp, p1), (-BIG, p1), (BIG, p1)]
            for amount, limit in cands:
                if amount == 0: continue
                if zfo and not (limit < self.sp): continue
                if not zfo and not (limit > self.sp): continue
                try: r = self.run_swap(zfo, amount, limit, fee)
                except m.Revert: continue
                if (r['p'], r['tick'], r['liq'], r['d0'], r['d1']) == (p1, tick1, liq1, a0, a1):
                    self.sp, self.tick, self.liq = r['p'], r['tick'], r['liq']
                    if zfo: self.fg0 = r['fg']
                    else: self.fg1 = r['fg']
                    for t, v in r['tw'].items(): self.ticks[t] = v
                    self.swaps += 1; self.crossed += r['crossed']; self.steps += r['steps']
                    return r
        raise Aside('swap not reproduced by any parameter candidate')

    def donate(self, a0, a1):
        if self.liq == 0: raise ValueError('donate with no liquidity')
        if a0: self.fg0 = (self.fg0 + ((a0 * Q128) & M) // self.liq) & M
        if a1: self.fg1 = (self.fg1 + ((a1 * Q128) & M) // self.liq) & M
        self.donates += 1

    def verify(self):
        bad = []
        s0 = ext(self.base, 4, self.N)
        if s0[0] & ((1 << 160) - 1) != self.sp: bad.append('sqrtPrice')
        if s24(s0[0] >> 160) != self.tick: bad.append('tick')
        if (s0[0] >> 184) & 0xffffff != self.pfee: bad.append('protocolFee')
        if (s0[0] >> 208) & 0xffffff != self.lpfee: bad.append('lpFee')
        if s0[1] != self.fg0: bad.append('feeGrowthGlobal0')
        if s0[2] != self.fg1: bad.append('feeGrowthGlobal1')
        if s0[3] != self.liq: bad.append('liquidity')
        for t, v in self.ticks.items():
            w = ext(H(u(t), self.base + 4), 3, self.N)
            if [w[0] & M128, s128(w[0] >> 128), w[1], w[2]] != v: bad.append('tick %d' % t)
        for k, v in self.pos.items():
            if ext(H(k, self.base + 6), 3, self.N) != v: bad.append('position %x' % k)
        for wp, v in self.words.items():
            if ext(H(u(wp), self.base + 5), 1, self.N)[0] != v: bad.append('bitmap word %d' % wp)
        return bad, {'ticks': len(self.ticks), 'positions': len(self.pos), 'words': len(self.words)}


blockcache = {}


def block_pm_logs(b):
    if b not in blockcache: blockcache[b] = rpc(cid, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}])
    return blockcache[b]


def words(d, n): return [int(d[2 + 64 * i:66 + 64 * i], 16) for i in range(n)]


POOL_EVENTS = (MOD, SWAP, DONATE)


def one(tx, N):
    r = {'tx': tx, 'block': N}
    bl = sorted(block_pm_logs(N), key=lambda x: int(x['logIndex'], 16))
    mine = [x for x in bl if x['transactionHash'] == tx]
    r['events'] = len(mine)
    kinds = Counter()
    for x in mine:
        t0 = x['topics'][0]
        if t0 in POOL_EVENTS: kinds[{MOD: 'mod', SWAP: 'swap', DONATE: 'donate'}[t0]] += 1
        elif t0 == T6909: kinds['6909'] += 1
        elif t0 == INIT: kinds['init'] += 1
        else: r['aside'] = 'unmodelled PoolManager event %s' % t0[:10]; return r
    r['eventKinds'] = dict(kinds)
    pools = {x['topics'][1] for x in mine if x['topics'][0] in POOL_EVENTS}
    for x in bl:
        if x['topics'][0] == INIT:  # the event carries the whole key; accept it only if it hashes to the id
            w = words(x['data'], 5); wk = [int(x['topics'][2], 16), int(x['topics'][3], 16), w[0], w[1], w[2]]
            if '0x' + keccak(b''.join(v.to_bytes(32, 'big') for v in wk)).hex() == x['topics'][1]:
                keycache[x['topics'][1]] = {'c0': '0x%040x' % wk[0], 'c1': '0x%040x' % wk[1], 'fee': w[0], 'spacing': s256(w[1]), 'hooks': '0x%040x' % w[2]}
    keys = {}
    for p in pools:
        k = poolkey(p)
        if k is None and harvest_keys(tx): k = poolkey(p)
        if k is None: r['aside'] = 'pool key not found'; return r
        keys[p] = k
    # A hook's return deltas move amounts between the caller's and the hook's accounts only
    # (src/PoolManager.sol:178-183, 221-226); both must reach zero before unlock returns, so the
    # PoolManager's net token flow still equals the pool deltas of the events. Recorded, not set aside.
    r['returnDeltaHooks'] = sum(1 for p in pools if int(keys[p]['hooks'], 16) & RETURN_DELTA_BITS)
    if any(x['topics'][0] == PFU and x['topics'][1] in pools for x in bl): r['aside'] = 'protocol fee changed in the block'; return r
    others = [x for x in bl if x['transactionHash'] != tx and x['topics'][0] in POOL_EVENTS and x['topics'][1] in pools]
    r['otherTxEventsOnPools'] = len(others)
    sims = {p: PoolSim(p, N, keys[p]['spacing']) for p in pools}
    inited = {x['topics'][1] for x in bl if x['topics'][0] == INIT}
    for p, s_ in sims.items():
        if s_.fresh and p not in inited: raise Aside('pool not initialized at the parent block nor in the block')
    r['initializedInBlock'] = sum(1 for p in pools if p in inited)
    owed = defaultdict(int); evs = []; myidx = {x['logIndex'] for x in mine}
    for x in bl:
        t0 = x['topics'][0]; ours = x['logIndex'] in myidx
        if t0 == T6909 and ours:
            fr, to = '0x' + x['topics'][1][26:], '0x' + x['topics'][2][26:]; cur = '0x%040x' % int(x['topics'][3], 16)
            amt = int(x['data'][66:130], 16)
            if int(fr, 16) == 0: owed[cur] -= amt; evs.append({'mint': [cur, str(amt)]})
            if int(to, 16) == 0: owed[cur] += amt; evs.append({'burn': [cur, str(amt)]})
            continue
        if t0 == INIT and x['topics'][1] in pools:
            sim = sims[x['topics'][1]]; w = words(x['data'], 5)
            if not sim.fresh: raise ValueError('Initialize of an initialized pool')
            # Pool.initialize: slot0 = price, tick and lpFee (src/libraries/Pool.sol:100-106); the tick is taken from the event
            sim.sp, sim.tick = w[3], s24(w[4]); sim.lpfee = 0 if w[0] == 0x800000 else w[0]
            if sim.tick != m.get_tick_at_sqrt_price(sim.sp): raise ValueError('Initialize tick is not getTickAtSqrtPrice of its price')
            sim.pfee = 0  # Pool.initialize leaves the protocol fee at 0 (src/libraries/Pool.sol:100-106)
            sim.fresh = False; continue
        if t0 not in POOL_EVENTS or x['topics'][1] not in pools: continue
        pid = x['topics'][1]; sim = sims[pid]; k = keys[pid]
        if t0 == SWAP:
            w = words(x['data'], 6); a0, a1 = s256(w[0]), s256(w[1])
            sr = sim.swap(a0, a1, w[2], w[3], s24(w[4]), w[5] & 0xffffff)
            if ours:
                owed[k['c0']] += a0; owed[k['c1']] += a1
                evs.append({'pool': pid, 'swap': [str(a0), str(a1)], 'steps': sr['steps'], 'crossed': sr['crossed'], 'protocolFee': str(sr['prot'])})
            continue
        if t0 == DONATE:
            w = words(x['data'], 2); sim.donate(w[0], w[1])
            if ours: owed[k['c0']] -= w[0]; owed[k['c1']] -= w[1]; evs.append({'pool': pid, 'donate': [str(w[0]), str(w[1])]})
            continue
        w = words(x['data'], 4)
        tl, tu, delta, salt = s256(w[0]), s256(w[1]), s256(w[2]), w[3]
        owner = '0x' + x['topics'][2][26:]
        prin, fees, L = sim.modify(owner, tl, tu, delta, salt)
        if ours:
            for i, c in enumerate((k['c0'], k['c1'])): owed[c] += prin[i] + fees[i]
            evs.append({'pool': pid, 'tl': tl, 'tu': tu, 'delta': str(delta), 'liqBefore': str(L), 'principal': [str(prin[0]), str(prin[1])], 'fees': [str(fees[0]), str(fees[1])], 'afterSwapInTx': any(s.swaps for s in sims.values())})
    r['detail'] = evs
    r['removals'] = sum(1 for e in evs if 'delta' in e and int(e['delta']) < 0); r['collects'] = sum(1 for e in evs if e.get('delta') == '0')
    r['swaps'] = sum(1 for e in evs if 'swap' in e); r['crossed'] = sum(e.get('crossed', 0) for e in evs)
    r['feesAfterSwap'] = sum(1 for e in evs if e.get('afterSwapInTx') and int(e.get('liqBefore', '0')) > 0)
    bad = []; cov = Counter()
    for s_ in sims.values():
        b_, c_ = s_.verify(); bad += b_; cov.update(c_)
    r['storageMismatch'] = bad; r['storageCompared'] = dict(cov); r['flips'] = sum(s.flips for s in sims.values())
    rc = rpc(cid, 'eth_getTransactionReceipt', [tx], urls=SU)
    if rc['status'] != '0x1': r['aside'] = 'receipt status not 1'; return r
    flows = {}
    for c in owed:
        if int(c, 16) == 0:
            bd = int(rpc(cid, 'eth_getBalance', [PM, hex(N)], urls=SU), 16) - int(rpc(cid, 'eth_getBalance', [PM, hex(N - 1)], urls=SU), 16)
            other = any(x['transactionHash'] != tx for x in bl)
            r['native'] = {'balanceDiff': str(bd), 'otherPmTxInBlock': other}
            if cid == 5042:
                o = i_ = 0
                for x in rc['logs']:
                    if x['address'].lower() == ARC_NAT and x['topics'][0] == TRANSFER:
                        v = int(x['data'][2:66], 16)
                        if '0x' + x['topics'][1][26:] == PM: o += v
                        if '0x' + x['topics'][2][26:] == PM: i_ += v
                r['native']['systemLogs'] = [str(o), str(i_)]
            try:
                flows[c] = native_flows(tx); r['native']['via'] = 'trace'
            except Exception as e:  # noqa
                r['native']['traceError'] = str(e)[:80]
                if cid == 5042: flows[c] = [int(v) for v in r['native']['systemLogs']]; r['native']['via'] = 'systemLogs'
                else: flows[c] = [max(0, -bd), max(0, bd)]; r['native']['via'] = 'balance'
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
    r['result'] = 'exact' if all(v['diff'] == '0' for v in res.values()) else 'differs'
    return r


if __name__ == '__main__':
    txs = {}
    for src in SRCS:
        for l in json.load(open(src))['logs']:
            if s256(int(l['data'][2 + 128:2 + 192], 16)) <= 0: txs[l['transactionHash']] = int(l['blockNumber'], 16)
    if ONLY is not None: txs = {k: v for k, v in txs.items() if k in ONLY}
    jobs = sorted(txs.items(), key=lambda kv: -kv[1])[:MAXTX]
    done = [0]

    def safe(j):
        done[0] += 1
        if done[0] % 50 == 0: print('progress', done[0], flush=True)
        try: return one(*j)
        except Aside as e: return {'tx': j[0], 'block': j[1], 'aside': str(e)}
        except Exception as e: return {'tx': j[0], 'block': j[1], 'error': repr(e)[:200]}
    with cf.ThreadPoolExecutor(THREADS) as ex: res = list(ex.map(safe, jobs))
    json.dump({'chainId': cid, 'results': res}, open(out, 'w'), indent=1)
    print(cid, 'tx', len(res), dict(Counter(r.get('aside') or ('error' if 'error' in r else 'checked') for r in res)))
    print(cid, 'results', dict(Counter(r['result'] for r in res if 'result' in r)))
    print(cid, 'storage mismatches', sum(1 for r in res if r.get('storageMismatch')), 'errors', Counter(r['error'][:70] for r in res if 'error' in r).most_common(5))
