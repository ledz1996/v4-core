"""Source model of the PoolManager for theme-state-replay (cycle 23).

Every entry point of src/PoolManager.sol, src/ProtocolFees.sol, src/ERC6909.sol, src/ERC6909Claims.sol,
src/Extsload.sol and src/Exttload.sol is written here from the text of src/, with the pool math taken from
tools/opdiff/v4math.py (a transcription of src/libraries checked earlier against integer mathematics).

The model is driven by a mined call trace (callTracer withLog). It walks the frames in execution order. For each
frame into the PoolManager it decodes the calldata, applies what the source does to a model of persistent storage
(started from the prestate of the transaction), transient storage (started empty) and the native balance, and
compares what it computed with what the chain returned: the frame output, the PoolManager's own logs, the calldata
the PoolManager passed to hooks (which carries the deltas it computed), and at the end every storage word the
transaction changed. Inputs taken from the trace are only what the source takes from outside: calldata, msg.sender,
msg.value, hook return data and token balanceOf return data. Frames that failed on chain are not applied.

Storage layout (src/PoolManager.sol:80 inheritance order; solmate Owned.owner first): owner 0,
protocolFeesAccrued 1, protocolFeeController 2, isOperator 3, balanceOf 4, allowance 5, _pools 6
(src/libraries/StateLibrary.sol:11 POOLS_SLOT = 6; offsets at lines 14-28)."""
import sys, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as V
from evm import keccak as _k, MASK

_KC = {}
def keccak(b):
    r = _KC.get(b)
    if r is None:
        r = _k(b);
        if len(_KC) < 2_000_000: _KC[b] = r
    return r
def H(*words): return int.from_bytes(keccak(b''.join((w & MASK).to_bytes(32, 'big') for w in words)), 'big')
def sel(sig): return keccak(sig.encode())[:4].hex()
U128 = (1 << 128) - 1; U160 = (1 << 160) - 1; I128MAX = (1 << 127) - 1
def s256(x): return x - (1 << 256) if x >> 255 else x
def sx(x, bits): x &= (1 << bits) - 1; return x - (1 << bits) if x >> (bits - 1) else x

class Revert(Exception): pass
class Unmodelled(Exception): pass

KEY = '(address,address,uint24,int24,address)'
S = {sel(k): v for k, v in {
    'unlock(bytes)': 'unlock', 'initialize(%s,uint160)' % KEY: 'initialize',
    'modifyLiquidity(%s,(int24,int24,int256,bytes32),bytes)' % KEY: 'modifyLiquidity', 'swap(%s,(bool,int256,uint160),bytes)' % KEY: 'swap',
    'donate(%s,uint256,uint256,bytes)' % KEY: 'donate', 'sync(address)': 'sync', 'take(address,address,uint256)': 'take', 'settle()': 'settle',
    'settleFor(address)': 'settleFor', 'clear(address,uint256)': 'clear', 'mint(address,uint256,uint256)': 'mint', 'burn(address,uint256,uint256)': 'burn',
    'updateDynamicLPFee(%s,uint24)' % KEY: 'updateDynamicLPFee', 'transfer(address,uint256,uint256)': 'transfer',
    'transferFrom(address,address,uint256,uint256)': 'transferFrom', 'approve(address,uint256,uint256)': 'approve', 'setOperator(address,bool)': 'setOperator',
    'setProtocolFee(%s,uint24)' % KEY: 'setProtocolFee', 'setProtocolFeeController(address)': 'setProtocolFeeController',
    'collectProtocolFees(address,address,uint256)': 'collectProtocolFees', 'transferOwnership(address)': 'transferOwnership',
    'extsload(bytes32)': 'extsload1', 'extsload(bytes32,uint256)': 'extsloadN', 'extsload(bytes32[])': 'extsloadA',
    'exttload(bytes32)': 'exttload1', 'exttload(bytes32[])': 'exttloadA', 'balanceOf(address,uint256)': 'balanceOf',
    'allowance(address,address,uint256)': 'allowance', 'isOperator(address,address)': 'isOperator', 'protocolFeesAccrued(address)': 'protocolFeesAccrued',
    'protocolFeeController()': 'protocolFeeController', 'owner()': 'owner', 'supportsInterface(bytes4)': 'supportsInterface',
}.items()}
HOOKSEL = {sel(k): v for k, v in {
    'beforeInitialize(address,%s,uint160)' % KEY: 'beforeInitialize', 'afterInitialize(address,%s,uint160,int24)' % KEY: 'afterInitialize',
    'beforeAddLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)' % KEY: 'beforeAddLiquidity',
    'beforeRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)' % KEY: 'beforeRemoveLiquidity',
    'afterAddLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)' % KEY: 'afterAddLiquidity',
    'afterRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)' % KEY: 'afterRemoveLiquidity',
    'beforeSwap(address,%s,(bool,int256,uint160),bytes)' % KEY: 'beforeSwap', 'afterSwap(address,%s,(bool,int256,uint160),int256,bytes)' % KEY: 'afterSwap',
    'beforeDonate(address,%s,uint256,uint256,bytes)' % KEY: 'beforeDonate', 'afterDonate(address,%s,uint256,uint256,bytes)' % KEY: 'afterDonate',
}.items()}
SEL_BALANCEOF = sel('balanceOf(address)'); SEL_TRANSFER = sel('transfer(address,uint256)')
SEL_UNLOCKCB = sel('unlockCallback(bytes)')
T_INIT = int.from_bytes(keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)'), 'big')
T_ML = int.from_bytes(keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)'), 'big')
T_SWAP = int.from_bytes(keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)'), 'big')
T_DONATE = int.from_bytes(keccak(b'Donate(bytes32,address,uint256,uint256)'), 'big')
T_6909 = int.from_bytes(keccak(b'Transfer(address,address,address,uint256,uint256)'), 'big')
T_APPROVAL = int.from_bytes(keccak(b'Approval(address,address,uint256,uint256)'), 'big')
T_OPSET = int.from_bytes(keccak(b'OperatorSet(address,address,bool)'), 'big')
T_PFU = int.from_bytes(keccak(b'ProtocolFeeUpdated(bytes32,uint24)'), 'big')
T_PFCU = int.from_bytes(keccak(b'ProtocolFeeControllerUpdated(address)'), 'big')
T_OWN = int.from_bytes(keccak(b'OwnershipTransferred(address,address)'), 'big')
T_ERC20 = int.from_bytes(keccak(b'Transfer(address,address,uint256)'), 'big')

# transient slots (src/libraries/Lock.sol, NonzeroDeltaCount.sol, CurrencyReserves.sol)
IS_UNLOCKED = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
NZ_COUNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
RES_SLOT = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
CUR_SLOT = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
# hook flags (src/libraries/Hooks.sol:29-47)
F = dict(BI=1 << 13, AI=1 << 12, BA=1 << 11, AA=1 << 10, BR=1 << 9, AR=1 << 8, BS=1 << 7, AS=1 << 6, BD=1 << 5, AD=1 << 4,
         BSD=1 << 3, ASD=1 << 2, AAD=1 << 1, ARD=1)
DYN = 0x800000

def words(hexdata):
    b = bytes.fromhex(hexdata[2:] if hexdata.startswith('0x') else hexdata)
    return b, [int.from_bytes(b[i:i + 32].ljust(32, b'\0'), 'big') for i in range(4, len(b), 32)]
def outwords(hexdata):
    b = bytes.fromhex((hexdata or '0x')[2:])
    return [int.from_bytes(b[i:i + 32].ljust(32, b'\0'), 'big') for i in range(0, len(b), 32)], b
def I(x): return int(x, 16) if isinstance(x, str) else int(x or 0)

class Key:
    def __init__(self, w):
        self.c0, self.c1, self.fee, self.ts, self.hooks = w[0] & U160, w[1] & U160, w[2] & 0xffffff, sx(w[3], 24), w[4] & U160
        self.raw = w[:5]
        self.id = H(*w[:5])
    def has(self, f): return bool(self.hooks & F[f])

def pack_delta(a0, a1): return ((a0 & U128) << 128) | (a1 & U128)
def unpack_delta(d): return sx(d >> 128, 128), sx(d, 128)
def to_i128(x):
    if not (-(1 << 127) <= x < (1 << 127)): raise Revert('SafeCastOverflow')
    return x
def u_to_i128(x):
    if x >= 1 << 127: raise Revert('SafeCastOverflow')
    return x

class Mismatch(Exception): pass

class Model:
    def __init__(self, pm, pre_storage, pre_balance):
        self.pm = pm.lower(); self.st = {int(k, 16): int(v, 16) for k, v in (pre_storage or {}).items()}
        self.pre_keys = set(self.st); self.pre_value = dict(self.st); self.tr = {}; self.bal = pre_balance; self.bal0 = pre_balance
        self.written = set(); self.unread = set(); self.mm = []; self.notes = []; self.counts = {}
        self.native = {'settle': 0, 'take': 0, 'collect': 0, 'in_frames': 0, 'out_frames': 0}
        self.erc20 = {}  # currency -> {'paid':, 'take':, 'collect':}
        self.words_compared = 0; self.actions = []
    # storage
    def sload(self, k):
        if k not in self.st:
            self.unread.add(k); return 0
        return self.st[k]
    def sstore(self, k, v): self.st[k] = v & MASK; self.written.add(k)
    def tload(self, k): return self.tr.get(k, 0)
    def tstore(self, k, v): self.tr[k] = v & MASK
    def snap(self): return (dict(self.st), dict(self.tr), self.bal, set(self.written), {k: dict(v) for k, v in self.erc20.items()}, dict(self.native), len(self.actions))
    def restore(self, s):
        self.st, self.tr, self.bal, self.written = dict(s[0]), dict(s[1]), s[2], set(s[3]); self.erc20 = {k: dict(v) for k, v in s[4].items()}
        self.native = dict(s[5]); del self.actions[s[6]:]
    def mis(self, kind, **kw): self.mm.append(dict(kind=kind, **kw))
    def cnt(self, k): self.counts[k] = self.counts.get(k, 0) + 1
    def e20(self, c): return self.erc20.setdefault(c, {'paid': 0, 'take': 0, 'collect': 0, 'synced_reads': 0})

    # deltas, src/libraries/CurrencyDelta.sol and src/PoolManager.sol:367-377
    def account(self, cur, delta, target):
        if delta == 0: return
        slot = H(target, cur)
        prev = s256(self.tload(slot)); nxt = prev + delta
        if not (-(1 << 255) <= nxt < (1 << 255)): raise Revert('overflow')
        self.tstore(slot, nxt)
        if nxt == 0: self.tstore(NZ_COUNT, self.tload(NZ_COUNT) - 1)
        elif prev == 0: self.tstore(NZ_COUNT, self.tload(NZ_COUNT) + 1)
    def account_pool(self, key, d, target):
        a0, a1 = unpack_delta(d); self.account(key.c0, a0, target); self.account(key.c1, a1, target)
    def unlocked(self): return self.tload(IS_UNLOCKED) != 0

    # pool storage, src/libraries/Pool.sol and StateLibrary.sol
    def base(self, pid): return H(pid, 6)
    def tick_slot(self, b, t): return H(t, b + 4)
    def word_slot(self, b, w): return H(w, b + 5)
    def pos_slot(self, b, pk): return H(pk, b + 6)
    def slot0(self, b):
        v = self.sload(b); return v & U160, sx(v >> 160, 24), (v >> 184) & 0xffffff, (v >> 208) & 0xffffff
    def set_slot0(self, b, p, t, pf, lf):
        old = self.sload(b)
        self.sstore(b, (old & ~((1 << 232) - 1) & MASK) | (lf << 208) | (pf << 184) | ((t & 0xffffff) << 160) | p)

    def tick_info(self, b, t):
        s = self.tick_slot(b, t); w = self.sload(s)
        return s, w & U128, sx(w >> 128, 128)
    def update_tick(self, b, t, ld, upper, cur_tick):
        s, gb, nb = self.tick_info(b, t)
        ga = V.add(gb, ld & MASK) if False else self.add_delta(gb, ld)
        flipped = (ga == 0) != (gb == 0)
        if gb == 0 and t <= cur_tick:
            self.sstore(s + 1, self.sload(b + 1)); self.sstore(s + 2, self.sload(b + 2))
        net = nb - ld if upper else nb + ld
        net = sx(net, 128)  # int128 arithmetic in checked mode would revert on overflow
        if not (-(1 << 127) <= (nb - ld if upper else nb + ld) < (1 << 127)): raise Revert('int128 overflow')
        self.sstore(s, (ga & U128) | ((net & MASK) << 128))
        return flipped, ga
    def add_delta(self, x, y):  # src/libraries/LiquidityMath.sol
        z = (x & U128) + y
        if z < 0 or z >> 128: raise Revert('SafeCastOverflow')
        return z
    def flip(self, b, t, ts):  # src/libraries/TickBitmap.sol flipTick
        if abs(t) % abs(ts) != 0: raise Revert('TickMisaligned')  # smod(tick, tickSpacing) != 0
        c = (abs(t) // abs(ts)) * (1 if (t >= 0) == (ts > 0) else -1)  # sdiv truncates toward zero
        w = c >> 8; bit = c & 0xff
        s = self.word_slot(b, w); self.sstore(s, self.sload(s) ^ (1 << bit))
    def next_init(self, b, tick, ts, lte):  # src/libraries/TickBitmap.sol nextInitializedTickWithinOneWord
        q = abs(tick) // abs(ts) * (1 if (tick >= 0) == (ts > 0) else -1)
        r = abs(tick) % abs(ts) * (1 if tick >= 0 else -1)
        comp = q - (1 if r < 0 else 0)
        if lte:
            w, bp = comp >> 8, comp & 0xff
            mask = MASK >> (255 - bp)
            m = self.sload(self.word_slot(b, w)) & mask
            init = m != 0
            nxt = (comp - (bp - V.most_significant_bit(m))) * ts if init else (comp - bp) * ts
        else:
            comp += 1
            w, bp = comp >> 8, comp & 0xff
            mask = (~((1 << bp) - 1)) & MASK
            m = self.sload(self.word_slot(b, w)) & mask
            init = m != 0
            nxt = (comp + (V.least_significant_bit(m) - bp)) * ts if init else (comp + (255 - bp)) * ts
        return sx(nxt, 24), init
    def fee_inside(self, b, tl, tu, tick):
        sl, su = self.tick_slot(b, tl), self.tick_slot(b, tu)  # Pool.sol:493-494 reads only the fee growth words
        l0, l1, u0, u1 = self.sload(sl + 1), self.sload(sl + 2), self.sload(su + 1), self.sload(su + 2)
        if tick < tl: return (l0 - u0) & MASK, (l1 - u1) & MASK
        if tick >= tu: return (u0 - l0) & MASK, (u1 - l1) & MASK
        return (self.sload(b + 1) - l0 - u0) & MASK, (self.sload(b + 2) - l1 - u1) & MASK

    def max_liq(self, ts):  # src/libraries/Pool.sol:565-582
        def sdiv(a, d): return abs(a) // abs(d) * (1 if (a >= 0) == (d > 0) else -1)
        def smod(a, d): return abs(a) % abs(d) * (1 if a >= 0 else -1)
        mn = sdiv(V.MIN_TICK, ts) - (1 if smod(V.MIN_TICK, ts) < 0 else 0)
        mx = sdiv(V.MAX_TICK, ts)
        return ((1 << 128) - 1) // (mx - mn + 1)

    def pool_modify(self, key, owner, tl, tu, ld, salt):  # src/libraries/Pool.sol:146-238
        b = self.base(key.id)
        if tl >= tu: raise Revert('TicksMisordered')
        if tl < V.MIN_TICK: raise Revert('TickLowerOutOfBounds')
        if tu > V.MAX_TICK: raise Revert('TickUpperOutOfBounds')
        p, tick, pf, lf = self.slot0(b)
        fl = fu = False
        if ld != 0:
            fl, gl = self.update_tick(b, tl, ld, False, tick)
            fu, gu = self.update_tick(b, tu, ld, True, tick)
            if ld >= 0:
                m = self.max_liq(key.ts)
                if gl > m or gu > m: raise Revert('TickLiquidityOverflow')
            if fl: self.flip(b, tl, key.ts)
            if fu: self.flip(b, tu, key.ts)
        fg0, fg1 = self.fee_inside(b, tl, tu, tick)
        pk = int.from_bytes(keccak(owner.to_bytes(20, 'big') + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt.to_bytes(32, 'big')), 'big')
        ps = self.pos_slot(b, pk)
        liq = self.sload(ps) & U128
        if ld == 0:
            if liq == 0: raise Revert('CannotUpdateEmptyPosition')
        else:
            self.sstore(ps, self.add_delta(liq, ld))
        o0 = V.mul_div((fg0 - self.sload(ps + 1)) & MASK, liq, 1 << 128)
        o1 = V.mul_div((fg1 - self.sload(ps + 2)) & MASK, liq, 1 << 128)
        self.sstore(ps + 1, fg0); self.sstore(ps + 2, fg1)
        fees = pack_delta(u_to_i128(o0), u_to_i128(o1))
        if ld < 0:
            if fl: self.sstore(self.tick_slot(b, tl), 0); self.sstore(self.tick_slot(b, tl) + 1, 0); self.sstore(self.tick_slot(b, tl) + 2, 0)
            if fu: self.sstore(self.tick_slot(b, tu), 0); self.sstore(self.tick_slot(b, tu) + 1, 0); self.sstore(self.tick_slot(b, tu) + 2, 0)
        d0 = d1 = 0
        if ld != 0:
            def a0(pa, pb):
                return V.amount0_delta(pa, pb, -ld, False) if ld < 0 else -V.amount0_delta(pa, pb, ld, True)
            def a1(pa, pb):
                return V.amount1_delta(pa, pb, -ld, False) if ld < 0 else -V.amount1_delta(pa, pb, ld, True)
            pl, pu = V.get_sqrt_price_at_tick(tl), V.get_sqrt_price_at_tick(tu)
            if tick < tl: d0 = a0(pl, pu)
            elif tick < tu:
                d0 = a0(p, pu); d1 = a1(pl, p)
                self.sstore(b + 3, self.add_delta(self.sload(b + 3) & U128, ld))
            else: d1 = a1(pl, pu)
            for x in (d0, d1):
                if abs(x) >= 1 << 255: raise Revert('SafeCastOverflow')
        return pack_delta(to_i128(d0), to_i128(d1)), fees, pk

    def pool_swap(self, key, amt, zfo, limit, fee_override):  # src/libraries/Pool.sol:279-463
        b = self.base(key.id)
        p0, t0, pf, lf = self.slot0(b)
        protocol_fee = (pf & 0xfff) if zfo else (pf >> 12)
        rem = amt; calc = 0; p = p0; tick = t0; liq = self.sload(b + 3) & U128
        lp = ((fee_override & 0xBFFFFF) if fee_override & 0x400000 else lf)
        if fee_override & 0x400000 and lp > 1000000: raise Revert('LPFeeTooLarge')
        swap_fee = lp if protocol_fee == 0 else (protocol_fee & 0xfff) + lp - ((protocol_fee & 0xfff) * lp) // 1000000
        if swap_fee >= 1000000 and amt > 0: raise Revert('InvalidFeeForExactOut')
        if amt == 0: return 0, 0, swap_fee, (p, tick, liq), 0
        if zfo:
            if limit >= p0: raise Revert('PriceLimitAlreadyExceeded')
            if limit <= V.MIN_SQRT_PRICE: raise Revert('PriceLimitOutOfBounds')
        else:
            if limit <= p0: raise Revert('PriceLimitAlreadyExceeded')
            if limit >= V.MAX_SQRT_PRICE: raise Revert('PriceLimitOutOfBounds')
        fg = self.sload(b + 1) if zfo else self.sload(b + 2)
        to_protocol = 0; steps = 0
        while not (rem == 0 or p == limit):
            steps += 1
            if steps > 100000: raise Unmodelled('too many steps')
            start = p
            tn, init = self.next_init(b, tick, key.ts, zfo)
            if tn <= V.MIN_TICK: tn = V.MIN_TICK
            if tn >= V.MAX_TICK: tn = V.MAX_TICK
            pn = V.get_sqrt_price_at_tick(tn)
            target = (limit if pn < limit else pn) if zfo else (limit if pn > limit else pn)
            p, ain, aout, fa = V.compute_swap_step(p, target, liq, rem, swap_fee)
            if amt > 0:
                rem = rem - aout
                calc -= ain + fa
            else:
                rem = rem + (ain + fa)
                calc += aout
            if ain + fa >= 1 << 255 or aout >= 1 << 255: raise Revert('SafeCastOverflow')
            if protocol_fee > 0:
                d = fa if swap_fee == protocol_fee else ((ain + fa) * protocol_fee) // 1000000
                fa = (fa - d) & MASK; to_protocol += d
            if liq > 0: fg = (fg + ((fa * (1 << 128)) & MASK) // liq) & MASK
            if p == pn:
                if init:
                    g0, g1 = (fg, self.sload(b + 2)) if zfo else (self.sload(b + 1), fg)
                    s, _, net = self.tick_info(b, tn)
                    self.sstore(s + 1, (g0 - self.sload(s + 1)) & MASK); self.sstore(s + 2, (g1 - self.sload(s + 2)) & MASK)
                    if zfo: net = -net
                    liq = self.add_delta(liq, net)
                tick = tn - 1 if zfo else tn
            elif p != start:
                tick = V.get_tick_at_sqrt_price(p)
        self.set_slot0(b, p, tick, pf, lf)
        if (self.sload(b + 3) & U128) != liq: self.sstore(b + 3, (self.sload(b + 3) & ~U128 & MASK) | liq)
        if not zfo: self.sstore(b + 2, fg)
        else: self.sstore(b + 1, fg)
        if zfo != (amt < 0):
            d = pack_delta(to_i128(calc), to_i128(amt - rem))
        else:
            d = pack_delta(to_i128(amt - rem), to_i128(calc))
        return d, to_protocol, swap_fee, (p, tick, liq), steps

    # trace walking
    def logs_of(self, f):
        return [l for l in f.get('logs', []) if l.get('address', '').lower() == self.pm]
    def check_log(self, f, topic0, expect_topics, expect_data, label):
        """find the PoolManager log with topic0 in frame f; compare topics and data words"""
        for l in self.logs_of(f):
            t = [I(x) for x in l['topics']]
            if t[0] != topic0 or l.get('_used'): continue
            l['_used'] = True
            dw, _ = outwords(l.get('data', '0x'))
            if t[1:] != [x & MASK for x in expect_topics] or dw != [x & MASK for x in expect_data]:
                self.mis('log', label=label, mined={'topics': l['topics'], 'data': l.get('data')},
                         expected={'topics': [hex(x & MASK) for x in expect_topics], 'data': [hex(x & MASK) for x in expect_data]})
            self.words_compared += len(expect_topics) + len(expect_data)
            return None if l.get('position') is None else I(l.get('position'))
        self.mis('log-missing', label=label)
        return None

    def run_children(self, kids):
        for c in kids: self.frame(c)

    def frame(self, f):
        if f.get('error'):
            if (f.get('to') or '').lower() == self.pm: self.cnt('pm-frame-reverted')
            return
        to = (f.get('to') or '').lower(); typ = f.get('type')
        val = I(f.get('value'))
        if typ in ('CALL', 'CALLCODE') and val:
            if to == self.pm and typ == 'CALL': self.bal += val; self.native['in_frames'] += val
            if (f.get('from') or '').lower() == self.pm: self.bal -= val; self.native['out_frames'] += val
        if typ in ('CREATE', 'CREATE2', 'SELFDESTRUCT'):
            if typ == 'SELFDESTRUCT' and to == self.pm: self.bal += val
            self.run_children(f.get('calls', [])); return
        if to == self.pm and typ in ('CALL', 'STATICCALL'):
            snap = self.snap()
            try:
                self.pm_call(f)
            except Revert as e:
                self.mis('model-reverted', reason=str(e), input=f.get('input', '')[:10], output=f.get('output'))
                self.restore(snap)
            return
        if to == self.pm and typ in ('DELEGATECALL', 'CALLCODE'):
            self.cnt('pm-code-in-other-context'); self.run_children(f.get('calls', [])); return
        self.run_children(f.get('calls', []))

    def split(self, f, pos, fallback_after):
        kids = f.get('calls', [])
        if pos is None:
            pos = next((i for i, c in enumerate(kids) if (c.get('input') or '')[2:10] in fallback_after), len(kids))
        return kids[:pos], kids[pos:]

    def hook_child(self, kids, key, name):
        for c in kids:
            if (c.get('to') or '').lower() == '0x%040x' % key.hooks and HOOKSEL.get((c.get('input') or '')[2:10]) == name: return c
        return None

    def pm_call(self, f):
        data = f.get('input') or '0x'
        selh = data[2:10]; name = S.get(selh)
        raw, w = words(data)
        sender = I(f.get('from')); val = I(f.get('value')) if f.get('type') == 'CALL' else 0
        self.cnt('call:' + (name or 'unknown'))
        out = f.get('output') or '0x'; ow, ob = outwords(out)
        static = f.get('type') == 'STATICCALL'
        def need_unlocked():
            if not self.unlocked(): raise Revert('ManagerLocked')
        def expect_out(vals, label):
            self.words_compared += len(vals)
            if ow != [v & MASK for v in vals]:
                self.mis('output', label=label, mined=out, expected=[hex(v & MASK) for v in vals])
        kids = f.get('calls', [])
        if name is None:
            self.mis('unknown-selector', input=data[:74]); self.run_children(kids); return
        if name not in ('extsload1', 'extsloadN', 'extsloadA', 'exttload1', 'exttloadA', 'balanceOf', 'allowance', 'isOperator', 'protocolFeesAccrued',
                        'protocolFeeController', 'owner', 'supportsInterface', 'settle', 'settleFor') and val:
            raise Revert('non-payable with value')
        if name == 'unlock':
            if self.unlocked(): raise Revert('AlreadyUnlocked')
            self.tstore(IS_UNLOCKED, 1)
            cb = [c for c in kids]
            self.run_children(cb)
            if self.tload(NZ_COUNT) != 0:
                self.mis('unlock-ended-unsettled', count=self.tload(NZ_COUNT), deltas={hex(k): hex(v) for k, v in self.tr.items() if v and k not in (IS_UNLOCKED, NZ_COUNT, RES_SLOT, CUR_SLOT)})
            self.tstore(IS_UNLOCKED, 0)
            # result = callback return data re-encoded as bytes
            if cb and not cb[0].get('error'):
                r = bytes.fromhex((cb[0].get('output') or '0x')[2:])
                # abi.decode(bytes) of the callback output, re-encoded by the PoolManager
                off = int.from_bytes(r[0:32], 'big') if len(r) >= 32 else 0  # abi.decode(bytes): the head word is the offset
                if len(r) >= 64 and off + 32 <= len(r):
                    ln = int.from_bytes(r[off:off + 32], 'big'); inner = r[off + 32:off + 32 + ln]
                    exp = (32).to_bytes(32, 'big') + ln.to_bytes(32, 'big') + inner + b'\0' * ((-ln) % 32)
                    self.words_compared += 1
                    if ob != exp: self.mis('output', label='unlock', mined=out[:200], expected='0x' + exp.hex()[:200])
            self.actions.append(('unlock',)); return
        if name == 'initialize':
            key = Key(w[0:5]); price = w[5] & U160
            if key.ts > 32767: raise Revert('TickSpacingTooLarge')
            if key.ts < 1: raise Revert('TickSpacingTooSmall')
            if key.c0 >= key.c1: raise Revert('CurrenciesOutOfOrderOrEqual')
            pos = self.find_pos(f, T_INIT)
            a, z = self.split(f, pos, {k for k, v in HOOKSEL.items() if v == 'afterInitialize'})
            self.run_children(a)
            b = self.base(key.id)
            if self.slot0(b)[0] != 0: raise Revert('PoolAlreadyInitialized')
            lf = 0 if key.fee == DYN else key.fee
            if key.fee != DYN and key.fee > 1000000: raise Revert('LPFeeTooLarge')
            tick = V.get_tick_at_sqrt_price(price)
            self.sstore(b, (lf << 208) | ((tick & 0xffffff) << 160) | price)
            self.check_log(f, T_INIT, [key.id, key.c0, key.c1], [key.fee, key.ts & MASK, key.hooks, price, tick & MASK], 'Initialize')
            self.run_children(z)
            expect_out([tick & MASK], 'initialize'); self.actions.append(('initialize', hex(key.id))); return
        if name == 'modifyLiquidity':
            need_unlocked()
            key = Key(w[0:5]); tl, tu, ldw, salt = sx(w[5], 24), sx(w[6], 24), s256(w[7]), w[8]
            b = self.base(key.id)
            if self.slot0(b)[0] == 0: raise Revert('PoolNotInitialized')
            pos = self.find_pos(f, T_ML)
            a, z = self.split(f, pos, {k for k, v in HOOKSEL.items() if v in ('afterAddLiquidity', 'afterRemoveLiquidity')})
            self.run_children(a)
            ld = to_i128(ldw)
            principal, fees, pk = self.pool_modify(key, sender, tl, tu, ld, salt)
            p0, p1 = unpack_delta(principal); q0, q1 = unpack_delta(fees)
            caller = pack_delta(to_i128(p0 + q0), to_i128(p1 + q1))
            self.check_log(f, T_ML, [key.id, sender], [tl & MASK, tu & MASK, ldw & MASK, salt], 'ModifyLiquidity')
            self.run_children(z)
            hookd = 0
            if sender != key.hooks:
                nm = 'afterAddLiquidity' if ldw > 0 else 'afterRemoveLiquidity'
                flag, dflag = ('AA', 'AAD') if ldw > 0 else ('AR', 'ARD')
                if key.has(flag):
                    hc = self.hook_child(z, key, nm)
                    if hc is None: self.mis('hook-call-missing', label=nm)
                    else:
                        _, hw = words(hc['input'])
                        # afterXLiquidity(sender, key(5), params(4), delta, feesAccrued, hookData): delta at word 10, fees at 11
                        self.words_compared += 2
                        if hw[10] != caller or hw[11] != fees:
                            self.mis('hook-input', label=nm, mined=[hex(hw[10]), hex(hw[11])], expected=[hex(caller), hex(fees)])
                        if key.has(dflag):
                            hov, hb = outwords(hc.get('output'))
                            if len(hb) != 64: raise Revert('InvalidHookResponse')
                            hookd = hov[1]
                            h0, h1 = unpack_delta(hookd); c0, c1 = unpack_delta(caller)
                            caller = pack_delta(to_i128(c0 - h0), to_i128(c1 - h1))
            if hookd: self.account_pool(key, hookd, key.hooks)
            self.account_pool(key, caller, sender)
            expect_out([caller, fees], 'modifyLiquidity')
            self.actions.append(('modifyLiquidity', hex(key.id), ld, hex(principal), hex(fees), hex(hookd))); return
        if name == 'swap':
            need_unlocked()
            key = Key(w[0:5]); zfo = bool(w[5]); amt = s256(w[6]); limit = w[7] & U160
            if amt == 0: raise Revert('SwapAmountCannotBeZero')
            b = self.base(key.id)
            if self.slot0(b)[0] == 0: raise Revert('PoolNotInitialized')
            pos = self.find_pos(f, T_SWAP)
            a, z = self.split(f, pos, {k for k, v in HOOKSEL.items() if v == 'afterSwap'})
            self.run_children(a)
            to_swap = amt; bsd = 0; ovr = 0
            if sender != key.hooks and key.has('BS'):
                hc = self.hook_child(a, key, 'beforeSwap')
                if hc is None: self.mis('hook-call-missing', label='beforeSwap'); raise Unmodelled('beforeSwap missing')
                hov, hb = outwords(hc.get('output'))
                if len(hb) != 96: raise Revert('InvalidHookResponse')
                if key.fee == DYN: ovr = hov[2] & 0xffffff
                if key.has('BSD'):
                    bsd = hov[1]; spec = sx(bsd >> 128, 128)
                    if spec != 0:
                        exact_in = to_swap < 0; to_swap += spec
                        if (to_swap > 0) if exact_in else (to_swap < 0): raise Revert('HookDeltaExceedsSwapAmount')
            # lpFeeOverride is taken as the uint24 the source assigns (src/libraries/ParseBytes.sol:21-25)
            d, to_prot, sfee, (p, t, l), steps = self.pool_swap(key, to_swap, zfo, limit, ovr)
            self.cnt('swap-steps-%s' % ('1' if steps <= 1 else 'multi'))
            if to_prot:
                inp = key.c0 if zfo else key.c1
                s_ = H(inp, 1); self.sstore(s_, self.sload(s_) + to_prot)
            a0, a1 = unpack_delta(d)
            self.check_log(f, T_SWAP, [key.id, sender], [a0 & MASK, a1 & MASK, p, l, t & MASK, sfee], 'Swap')
            self.run_children(z)
            spec = sx(bsd >> 128, 128); unspec = sx(bsd, 128); hookd = 0
            if sender != key.hooks:
                if key.has('AS'):
                    hc = self.hook_child(z, key, 'afterSwap')
                    if hc is None: self.mis('hook-call-missing', label='afterSwap')
                    else:
                        _, hw = words(hc['input'])
                        self.words_compared += 1
                        if hw[9] != d: self.mis('hook-input', label='afterSwap', mined=hex(hw[9]), expected=hex(d))
                        if key.has('ASD'):
                            hov, hb = outwords(hc.get('output'))
                            if len(hb) != 64: raise Revert('InvalidHookResponse')
                            unspec += to_i128(s256(hov[1]))
                            unspec = to_i128(unspec)
                if unspec or spec:
                    hookd = pack_delta(spec, unspec) if ((amt < 0) == zfo) else pack_delta(unspec, spec)
                    h0, h1 = unpack_delta(hookd); d = pack_delta(to_i128(a0 - h0), to_i128(a1 - h1))
            if hookd: self.account_pool(key, hookd, key.hooks)
            self.account_pool(key, d, sender)
            expect_out([d], 'swap')
            self.actions.append(('swap', hex(key.id), steps, hex(d), to_prot)); return
        if name == 'donate':
            need_unlocked()
            key = Key(w[0:5]); a0, a1 = w[5], w[6]
            b = self.base(key.id)
            if self.slot0(b)[0] == 0: raise Revert('PoolNotInitialized')
            pos = self.find_pos(f, T_DONATE)
            a, z = self.split(f, pos, {k for k, v in HOOKSEL.items() if v == 'afterDonate'})
            self.run_children(a)
            liq = self.sload(b + 3) & U128
            if liq == 0: raise Revert('NoLiquidityToReceiveFees')
            d = pack_delta(-u_to_i128(a0), -u_to_i128(a1))
            if a0: self.sstore(b + 1, self.sload(b + 1) + ((a0 * (1 << 128)) & MASK) // liq)
            if a1: self.sstore(b + 2, self.sload(b + 2) + ((a1 * (1 << 128)) & MASK) // liq)
            self.account_pool(key, d, sender)
            self.check_log(f, T_DONATE, [key.id, sender], [a0, a1], 'Donate')
            self.run_children(z)
            expect_out([d], 'donate'); self.actions.append(('donate', hex(key.id))); return
        if name == 'sync':
            cur = w[0] & U160
            if cur == 0:
                self.tstore(CUR_SLOT, 0); self.run_children(kids)
            else:
                bc = [c for c in kids if (c.get('input') or '')[2:10] == SEL_BALANCEOF]
                self.run_children(kids)
                if not bc: self.mis('balanceOf-missing', label='sync'); return
                ov, _ = outwords(bc[0].get('output'))
                self.tstore(CUR_SLOT, cur); self.tstore(RES_SLOT, ov[0] if ov else 0)
            self.actions.append(('sync', hex(cur))); return
        if name == 'take':
            need_unlocked()
            cur, to, amount = w[0] & U160, w[1] & U160, w[2]
            self.account(cur, -u_to_i128(amount), sender)
            self.run_children(kids)
            if cur == 0:
                self.native['take'] += amount
                vk = [c for c in kids if I(c.get('value')) == amount and I(c.get('to')) == to]
                if amount and not vk: self.mis('native-take-frame-missing', amount=amount)
            else:
                self.e20(cur)['take'] += amount
                tk = [c for c in kids if (c.get('input') or '')[2:10] == SEL_TRANSFER and I(c.get('to')) == cur]
                if not tk: self.mis('transfer-frame-missing', cur=hex(cur))
                else:
                    _, tw = words(tk[0]['input']); self.words_compared += 2
                    if tw[0] != to or tw[1] != amount: self.mis('transfer-args', mined=[hex(x) for x in tw[:2]], expected=[hex(to), hex(amount)])
            self.actions.append(('take', hex(cur), amount)); return
        if name in ('settle', 'settleFor'):
            need_unlocked()
            rcpt = sender if name == 'settle' else (w[0] & U160)
            cur = self.tload(CUR_SLOT) & U160
            self.run_children(kids)
            if cur == 0:
                paid = val; self.native['settle'] += paid
            else:
                if val > 0: raise Revert('NonzeroNativeValue')
                bc = [c for c in kids if (c.get('input') or '')[2:10] == SEL_BALANCEOF and I(c.get('to')) == cur]
                if not bc: self.mis('balanceOf-missing', label='settle'); return
                ov, _ = outwords(bc[0].get('output'))
                now = ov[0] if ov else 0; before = self.tload(RES_SLOT)
                if now < before: raise Revert('underflow')
                paid = now - before; self.tstore(CUR_SLOT, 0)
                self.e20(cur)['paid'] += paid
            self.account(cur, u_to_i128(paid), rcpt)
            expect_out([paid], name); self.actions.append(('settle', hex(cur), paid)); return
        if name == 'clear':
            need_unlocked()
            cur, amount = w[0] & U160, w[1]
            current = s256(self.tload(H(sender, cur)))
            ad = u_to_i128(amount)
            if ad != current: raise Revert('MustClearExactPositiveDelta')
            self.account(cur, -ad, sender); self.run_children(kids); self.actions.append(('clear', hex(cur), amount)); return
        if name in ('mint', 'burn'):
            need_unlocked()
            a, idv, amount = w[0] & U160, w[1], w[2]
            cur = idv & U160
            if name == 'mint':
                self.account(cur, -u_to_i128(amount), sender)
                bs = H(cur, H(a, 4)); nb = self.sload(bs) + amount
                if nb >> 256: raise Revert('overflow')
                self.sstore(bs, nb)
                self.check_log(f, T_6909, [0, a, cur], [sender, amount], 'mint')
            else:
                self.account(cur, u_to_i128(amount), sender)
                self.burn_from(a, cur, amount, sender)
                self.check_log(f, T_6909, [a, 0, cur], [sender, amount], 'burn')
            self.run_children(kids); self.actions.append((name, hex(cur), amount)); return
        if name in ('transfer', 'transferFrom'):
            if name == 'transfer': frm, rcv, idv, amount = sender, w[0] & U160, w[1], w[2]
            else:
                frm, rcv, idv, amount = w[0] & U160, w[1] & U160, w[2], w[3]
                if sender != frm and not self.sload(H(sender, H(frm, 3))):
                    s_ = H(idv, H(sender, H(frm, 5))); al = self.sload(s_)
                    if al != MASK:
                        if al < amount: raise Revert('underflow')
                        self.sstore(s_, al - amount)
            s1 = H(idv, H(frm, 4)); v1 = self.sload(s1)
            if v1 < amount: raise Revert('underflow')
            self.sstore(s1, v1 - amount)
            s2 = H(idv, H(rcv, 4)); v2 = self.sload(s2) + amount
            if v2 >> 256: raise Revert('overflow')
            self.sstore(s2, v2)
            self.check_log(f, T_6909, [frm, rcv, idv], [sender, amount], name)
            expect_out([1], name); self.run_children(kids); return
        if name == 'approve':
            sp, idv, amount = w[0] & U160, w[1], w[2]
            self.sstore(H(idv, H(sp, H(sender, 5))), amount); self.check_log(f, T_APPROVAL, [sender, sp, idv], [amount], 'approve'); expect_out([1], name); return
        if name == 'setOperator':
            op, ok = w[0] & U160, w[1]
            if ok > 1: raise Revert('bad bool')
            self.sstore(H(op, H(sender, 3)), ok); self.check_log(f, T_OPSET, [sender, op], [ok], 'setOperator'); expect_out([1], name); return
        if name == 'updateDynamicLPFee':
            key = Key(w[0:5]); nf = w[5]
            if nf >> 24: raise Revert('bad uint24')
            if key.fee != DYN or sender != key.hooks: raise Revert('UnauthorizedDynamicLPFeeUpdate')
            if nf > 1000000: raise Revert('LPFeeTooLarge')
            b = self.base(key.id); p, t, pf, lf = self.slot0(b)
            if p == 0: raise Revert('PoolNotInitialized')
            self.set_slot0(b, p, t, pf, nf); self.run_children(kids); self.actions.append(('updateDynamicLPFee', hex(key.id), nf)); return
        if name == 'setProtocolFee':
            key = Key(w[0:5]); nf = w[5]
            if sender != self.sload(2) & U160: raise Revert('InvalidCaller')
            if not ((nf & 0xfff) < 1001 and (nf & 0xfff000) < (1001 << 12)): raise Revert('ProtocolFeeTooLarge')
            b = self.base(key.id); p, t, pf, lf = self.slot0(b)
            if p == 0: raise Revert('PoolNotInitialized')
            self.set_slot0(b, p, t, nf & 0xffffff, lf); self.check_log(f, T_PFU, [key.id], [nf], 'setProtocolFee'); self.run_children(kids); self.actions.append(('setProtocolFee',)); return
        if name == 'setProtocolFeeController':
            if sender != self.sload(0) & U160: raise Revert('UNAUTHORIZED')
            self.sstore(2, w[0] & U160); self.check_log(f, T_PFCU, [w[0] & U160], [], 'setProtocolFeeController'); return
        if name == 'transferOwnership':
            if sender != self.sload(0) & U160: raise Revert('UNAUTHORIZED')
            self.sstore(0, (self.sload(0) & ~U160 & MASK) | (w[0] & U160)); self.check_log(f, T_OWN, [sender, w[0] & U160], [], 'transferOwnership'); return
        if name == 'collectProtocolFees':
            rc, cur, amount = w[0] & U160, w[1] & U160, w[2]
            if sender != self.sload(2) & U160: raise Revert('InvalidCaller')
            if cur != 0 and (self.tload(CUR_SLOT) & U160) == cur: raise Revert('ProtocolFeeCurrencySynced')
            s_ = H(cur, 1); acc = self.sload(s_); got = acc if amount == 0 else amount
            if acc < got: raise Revert('underflow')
            self.sstore(s_, acc - got); self.run_children(kids)
            if cur == 0: self.native['collect'] += got
            else: self.e20(cur)['collect'] += got
            expect_out([got], name); self.actions.append(('collectProtocolFees', hex(cur), got)); return
        # views: compare with the model state
        if name == 'extsload1': expect_out([self.sload(w[0])], name); return
        if name == 'extsloadN':
            n = w[1]
            if n > 100000: return
            expect_out([32, n] + [self.sload((w[0] + i) & MASK) for i in range(n)], name); return
        if name == 'extsloadA':
            n = w[w[0] // 32] if w else 0
            sl = w[w[0] // 32 + 1: w[0] // 32 + 1 + n]
            expect_out([32, n] + [self.sload(x) for x in sl], name); return
        if name == 'exttload1': expect_out([self.tload(w[0])], name); return
        if name == 'exttloadA':
            n = w[w[0] // 32]; sl = w[w[0] // 32 + 1: w[0] // 32 + 1 + n]
            expect_out([32, n] + [self.tload(x) for x in sl], name); return
        if name == 'balanceOf': expect_out([self.sload(H(w[1], H(w[0] & U160, 4)))], name); return
        if name == 'allowance': expect_out([self.sload(H(w[2], H(w[1] & U160, H(w[0] & U160, 5))))], name); return
        if name == 'isOperator': expect_out([self.sload(H(w[1] & U160, H(w[0] & U160, 3)))], name); return
        if name == 'protocolFeesAccrued': expect_out([self.sload(H(w[0] & U160, 1))], name); return
        if name == 'protocolFeeController': expect_out([self.sload(2) & U160], name); return
        if name == 'owner': expect_out([self.sload(0) & U160], name); return
        if name == 'supportsInterface': return

    def burn_from(self, frm, cur, amount, sender):  # src/ERC6909Claims.sol and src/ERC6909.sol:_burn
        if frm != sender and not self.sload(H(sender, H(frm, 3))):
            s_ = H(cur, H(sender, H(frm, 5))); al = self.sload(s_)
            if al != MASK:
                if al < amount: raise Revert('underflow')
                self.sstore(s_, al - amount)
        bs = H(cur, H(frm, 4)); v = self.sload(bs)
        if v < amount: raise Revert('underflow')
        self.sstore(bs, v - amount)

    def find_pos(self, f, topic0):
        for l in self.logs_of(f):
            if I(l['topics'][0]) == topic0 and not l.get('_used'):
                return None if l.get('position') is None else I(l.get('position'))
        return None

    def finish(self, diff_pre, diff_post, pre_balance_known=True):
        """compare every storage word the model holds with the mined post state"""
        post = {int(k, 16): int(v, 16) for k, v in (diff_post.get('storage') or {}).items()}
        dpre = {int(k, 16): int(v, 16) for k, v in (diff_pre.get('storage') or {}).items()}
        changed = set(post) | set(dpre)
        for k in changed:
            mined = post.get(k, 0)
            if k not in self.st and k not in self.written:
                self.mis('storage-unexplained', slot=hex(k), pre=hex(dpre.get(k, 0)), mined=hex(mined)); continue
            exp = self.st.get(k, 0)
            self.words_compared += 1
            if exp != mined: self.mis('storage', slot=hex(k), pre=hex(dpre.get(k, self.st.get(k, 0))), expected=hex(exp), mined=hex(mined))
        for k in self.written - changed:
            self.words_compared += 1
            start = self.pre_storage_value(k, dpre)
            if self.st.get(k, 0) != start:
                self.mis('storage-not-written', slot=hex(k), expected=hex(self.st.get(k, 0)), mined_unchanged=hex(start))
        # native balance
        if 'balance' in diff_post or 'balance' in diff_pre:
            b0 = I(diff_pre.get('balance', diff_post.get('balance'))); b1 = I(diff_post.get('balance', diff_pre.get('balance')))
        else:
            b0 = b1 = self.bal0
        self.bal_mined = (b0, b1)

    def pre_storage_value(self, k, dpre):
        return self.pre_value.get(k, 0)
