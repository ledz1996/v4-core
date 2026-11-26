"""Second case list: raw call sequences (driver kind 7), pools whose state is written by override, and calls made
while the PoolManager is locked. Deterministic, no seed. Usage: python3 extra_cases.py <cases.json> <out.json>
The first file is read only to continue its token address counter."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
import v4math as V
from cases import maxL, usable

I127 = (1 << 127) - 1
base = json.load(open(sys.argv[1]))['cases']
cases = []
k0 = len(base)


def new(tag, fee, ts, calls_fn, mint0=0, mint1=0, settle=True, hooks=0, storage_fn=None):
    i = k0 + len(cases)
    t0 = 0x0000000000000000000000000000000020000000 + 2 * i
    c = dict(kind=7, t0=t0, t1=t0 + 1, fee=fee, ts=ts, hooks=hooks, id=i, tag=tag)
    c['p'] = raw_p(mint0, mint1, settle, calls_fn(c))
    if storage_fn:
        c['storage'] = {hex(s): hex(v) for s, v in storage_fn(c).items()}
    cases.append(c)
    return c


def ov_pool(sqrtP, L, protocolFee=0, lpFee=0):
    def f(c):
        ps = pool_slot(c)
        return {ps: slot0_word(sqrtP, V.get_tick_at_sqrt_price(sqrtP), protocolFee, lpFee), ps + 3: L}
    return f


# A. overflow fallback of getNextSqrtPriceFromAmount0RoundingUp, pool state by override (ts 32767, so the first
#    step of a zeroForOne swap from a price above 2^129 targets tick 0, the start of bitmap word 0)
for sname, s in [('2^159.9', (MAX_SQRT * 15) // 16), ('2^150', 1 << 150), ('2^130', 1 << 130)]:
    for L in (1 << 100, 1 << 120, (1 << 128) - 1):
        N = L << 96
        amax = M // s
        afit = ((1 << 256) - N - 1) // s
        rows = [('precise path, line 47', afit), ('line 45 wraps', afit + 1), ('largest fitting product, line 45', amax),
                ('first wrapped product, line 43', amax + 1), ('wrapped 2^127-1', I127), ('wrapped 2^126', 1 << 126)]
        for name, a in rows:
            if a <= 0 or a > I127 or (name.startswith('line 45') and afit + 1 > amax):
                continue
            new(f'override fallback P={sname} L=2^{L.bit_length() - 1 if L & (L - 1) == 0 else "128-1"} {name} a={a}', 0, 32767,
                lambda c, a=a: [c_swap(c, True, -a, MIN_SQRT + 1)], mint1=1 << 200, storage_fn=ov_pool(s, L))
# B. 512-bit getAmount1Delta and mulDiv copies with real deposits (ts 32767, L 2^100)
ts = 32767; lo, hi = usable(ts)
for nm, amt, zfo in [('ofz in 1', -1, False), ('ofz in 2^64', -(1 << 64), False), ('ofz in 2^96', -(1 << 96), False),
                     ('ofz in 2^120', -(1 << 120), False), ('ofz in 2^126', -(1 << 126), False),
                     ('ofz out 2^64', 1 << 64, False), ('ofz out 2^99', 1 << 99, False),
                     ('zfo in 2^64', -(1 << 64), True), ('zfo in 2^99', -(1 << 99), True), ('zfo out 2^64', 1 << 64, True),
                     ('zfo out 2^99', 1 << 99, True),
                     ('ofz in 2^161 (amount above uint160, line 97)', -(1 << 161), False),
                     ('ofz in -(2^255-1) to limit (fee copy 512 path)', -((1 << 255) - 1), False),
                     ('zfo in -(2^255-1) to limit (fee copy 512 path)', -((1 << 255) - 1), True)]:
    for fee in (0, 3000):
        def calls(c, amt=amt, zfo=zfo):
            lim = MIN_SQRT + 1 if zfo else MAX_SQRT - 1
            if '2^255' in nm:
                lim = V.get_sqrt_price_at_tick(-32767 * 3) if zfo else V.get_sqrt_price_at_tick(32767 * 3)
            return [c_init(c, 1 << 96), c_mlp(c, -23 * ts, hi, 1 << 100), c_swap(c, zfo, amt, lim)]
        new(f'deposit ts=32767 L=2^100 P=2^96 {nm} fee={fee}', fee, ts, calls)
# C. amount above uint160 in the subtract branch (SqrtPriceMath.sol:105) and protocol fee branch, by override
for nm, s, L, amt, zfo in [('zfo out 2^161 (line 105)', 1 << 159, 1 << 100, 1 << 161, True),
                           ('zfo out 2^161 (line 105) odd liquidity', 1 << 159, (1 << 100) + 1, 1 << 161, True),
                           ('ofz in 2^161 (line 97)', 1 << 96, 1 << 100, -(1 << 161), False)]:
    new(f'override ts=32767 {nm}', 0, 32767, lambda c, amt=amt, zfo=zfo: [c_swap(c, zfo, amt, MIN_SQRT + 1 if zfo else MAX_SQRT - 1)],
        mint0=1 << 200, mint1=1 << 200, storage_fn=ov_pool(s, L))
for pf in (1000 | (1000 << 12), 1 | (999 << 12), 500 | (0 << 12)):
    for lp in (0, 3000, 1000000):
        for zfo in (True, False):
            for amt in (-(1 << 64), 1 << 60):
                if lp == 1000000 and amt > 0: continue
                fee = lp
                new(f'override protocol fee pf={pf:#x} lp={lp} {"zfo" if zfo else "ofz"} {"in" if amt < 0 else "out"}', fee, 60,
                    lambda c, zfo=zfo, amt=amt: [c_swap(c, zfo, amt, MIN_SQRT + 1 if zfo else MAX_SQRT - 1)],
                    mint0=1 << 120, mint1=1 << 120, storage_fn=ov_pool(1 << 96, 1 << 64, pf, lp))
# D. Position fee copy of mulDiv with prod1 != 0: three donations of 2^127-1 to liquidity 2, then a poke
new('position fee 512 path: 3 donations to L=2 then poke', 500, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, -60, 60, 2)] + [c_donate(c, I127, 0)] * 3 + [c_mlp(c, -60, 60, 0)])
new('position fee 512 path: 2 donations to L=2 then poke (no wrap)', 500, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, -60, 60, 2)] + [c_donate(c, I127, 0)] * 2 + [c_mlp(c, -60, 60, 0)])
# E. clamp at MAX_TICK and SafeCast at the end of the swap, real deposits
new('clamp tickNext >= MAX_TICK: ofz exact-in through empty words to MAX-1', 500, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, -600, 600, 1 << 64), c_swap(c, False, -I127, MAX_SQRT - 1)])
new('clamp tickNext <= MIN_TICK: zfo exact-in through empty words to MIN+1', 500, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, -600, 600, 1 << 64), c_swap(c, True, -I127, MIN_SQRT + 1)])
new('swap end cast: zfo exact-in 2^130 over full range L=2^64', 0, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, *usable(60), 1 << 64), c_swap(c, True, -(1 << 130), MIN_SQRT + 1)])
new('swap end cast: ofz exact-out 2^126 over full range L=2^64', 0, 60,
    lambda c: [c_init(c, 1 << 96), c_mlp(c, *usable(60), 1 << 64), c_swap(c, False, 1 << 126, MAX_SQRT - 1)])
# F. revert sides inside unlock
def bad(tag, fn, ts=60, fee=500, hooks=0, settle=True):
    new('revert ' + tag, fee, ts, fn, settle=settle, hooks=hooks)
bad('initialize tickSpacing 32768', lambda c: [c_init(c, 1 << 96)], ts=32768)
bad('initialize tickSpacing 0', lambda c: [c_init(c, 1 << 96)], ts=0)
def swapped(c):
    d = dict(c); d['t0'], d['t1'] = c['t1'], c['t0']; return [c_init(d, 1 << 96), c_init(dict(c, t1=c['t0']), 1 << 96)]
bad('initialize currencies out of order and equal', swapped)
bad('initialize no hook with dynamic fee', lambda c: [c_init(c, 1 << 96)], fee=0x800000)
bad('initialize hook with return-delta flag only', lambda c: [c_init(c, 1 << 96)], hooks=0x0000000000000000000000000000000000000004)
bad('initialize twice', lambda c: [c_init(c, 1 << 96), c_init(c, 1 << 96)])
bad('initialize price MIN-1 and MAX', lambda c: [c_init(c, MIN_SQRT - 1), c_init(c, MAX_SQRT)])
bad('modifyLiquidity on uninitialized pool, swap and donate on uninitialized pool',
    lambda c: [c_mlp(c, -60, 60, 1000), c_swap(c, True, -1000, MIN_SQRT + 1), c_donate(c, 1, 1)])
bad('modifyLiquidity tick errors', lambda c: [c_init(c, 1 << 96), c_mlp(c, 60, 60, 1000), c_mlp(c, MIN_TICK - 60, 60, 1000),
                                               c_mlp(c, -60, MAX_TICK + 60, 1000), c_mlp(c, -61, 60, 1000),
                                               c_mlp(c, -60, 60, 0), c_mlp(c, -60, 60, 1 << 200), c_mlp(c, -60, 60, (-(1 << 200)) & M)])
bad('modifyLiquidity remove more than the position', lambda c: [c_init(c, 1 << 96), c_mlp(c, -60, 60, 1000), c_mlp(c, -60, 60, (-1001) & M)])
bad('modifyLiquidity above maxLiquidityPerTick, lower then upper', lambda c: [c_init(c, 1 << 96), c_mlp(c, -60, 60, maxL(60) + 1),
                                                                               c_mlp(c, -120, 60, maxL(60)), c_mlp(c, -60, 60, 1)])
bad('swap zero amount, limits out of bounds and already exceeded', lambda c: [c_init(c, 1 << 96), c_mlp(c, -60, 60, 1 << 64),
    c_swap(c, True, 0, MIN_SQRT + 1), c_swap(c, True, -1000, MIN_SQRT), c_swap(c, False, -1000, MAX_SQRT),
    c_swap(c, True, -1000, 1 << 96), c_swap(c, False, -1000, 1 << 96), c_swap(c, True, -1000, (1 << 96) + 1)])
bad('sync on an address without code and on a contract whose balanceOf reverts', lambda c: [c_simple('sync(address)', 0x123456789), c_simple('sync(address)', S)])
bad('unlock inside unlock', lambda c: [c_simple('unlock(bytes)', 32, 0)])
bad('leave a delta open: CurrencyNotSettled', lambda c: [c_simple('mint(address,uint256,uint256)', D, c['t0'], 5)], settle=False)
bad('updateDynamicLPFee by a non-hook and on a static fee pool', lambda c: [c_init(c, 1 << 96),
    pm_call('updateDynamicLPFee((address,address,uint24,int24,address),uint24)', key_words(c) + [3000])])
bad('take, mint and burn above int128', lambda c: [c_simple('take(address,address,uint256)', c['t0'], D, 1 << 127),
    c_simple('mint(address,uint256,uint256)', D, c['t0'], 1 << 127), c_simple('burn(address,uint256,uint256)', D, c['t0'], 1 << 127)])

# G. calls while locked
dummy = dict(t0=0x1111, t1=0x2222, fee=500, ts=60, hooks=0)
OUT = [('modifyLiquidity', c_mlp(dummy, -60, 60, 1)), ('swap', c_swap(dummy, True, -1, MIN_SQRT + 1)), ('donate', c_donate(dummy, 1, 1)),
       ('take', c_simple('take(address,address,uint256)', 0x1111, D, 1)), ('settle', c_simple('settle()')),
       ('settleFor', c_simple('settleFor(address)', D)), ('clear', c_simple('clear(address,uint256)', 0x1111, 1)),
       ('mint', c_simple('mint(address,uint256,uint256)', D, 0x1111, 1)), ('burn', c_simple('burn(address,uint256,uint256)', D, 0x1111, 1)),
       ('setProtocolFee by a non-controller', pm_call(f'setProtocolFee({KEY},uint24)', key_words(dummy) + [0])),
       ('sync while locked', c_simple('sync(address)', 0)),
       ('ERC-6909 transfer of 0 while locked', c_simple('transfer(address,uint256,uint256)', B_, 0x1111, 0)),
       ('ERC-6909 approve while locked', c_simple('approve(address,uint256,uint256)', S, 0x1111, 7))]
json.dump({'note': 'deterministic, no seed', 'cases': cases, 'outside': [{'tag': t, 'data': d.hex()} for t, d in OUT]},
          open(sys.argv[2], 'w'), indent=0)
print(len(cases), 'cases,', len(OUT), 'outside calls')
