"""Differential tests of the compiled internal functions of the built runtime against the
meaning of the source lines, at the edges listed in OPCODES.md. Each Yul function is entered
at its entry point in the reference interpreter (harness.py), with inputs that include dirty
upper bits where the Yul parameter is a narrower Solidity type.
Usage: python3 -I fntests.py <out.json> [random cases per function]"""
import sys, json, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
sys.path.insert(0, H.OPD)
import v4math as V

M = 1 << 256; MASK = M - 1; U160 = (1 << 160) - 1; U128 = (1 << 128) - 1
def s(x): return x - M if x >> 255 else x
def u(x): return x % M
def sx(x, bits): x &= (1 << bits) - 1; return x - (1 << bits) if x >> (bits - 1) else x
rnd = random.Random(9_2026_11_24); N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
out = {}

def edges256():
    e = {0, 1, 2, 3, MASK, MASK - 1, 1 << 255, (1 << 255) - 1, (1 << 255) + 1}
    for k in (32, 64, 96, 127, 128, 129, 160, 192, 224, 255):
        e |= {1 << k, (1 << k) - 1, (1 << k) + 1}
    e |= {10 ** 6, 15625, 999999}
    return sorted(x & MASK for x in e)
def rwide(): return rnd.choice([rnd.getrandbits(256), rnd.getrandbits(rnd.randint(1, 256)), (1 << rnd.randint(0, 255)) + rnd.randint(-3, 3)]) & MASK
def dirty(x, bits):
    """same low bits, random garbage above them"""
    return (x & ((1 << bits) - 1)) | (rnd.getrandbits(256 - bits) << bits)

def check(name, fn, args, expect, ret_count=1):
    r = H.run(fn, args)
    if r[0] is False: got = 'revert'
    else: got = r[1][-ret_count:] if ret_count else []
    if expect == 'revert': good = got == 'revert'
    else: good = got != 'revert' and [g & MASK for g in got] == [x & MASK for x in (expect if isinstance(expect, list) else [expect])]
    d = out.setdefault(name, {'cases': 0, 'reverts': 0, 'mismatch': []}); d['cases'] += 1; d['reverts'] += expect == 'revert'
    if not good and len(d['mismatch']) < 10: d['mismatch'].append({'args': [hex(a) for a in args], 'expect': expect if expect == 'revert' else [hex(x & MASK) for x in (expect if isinstance(expect, list) else [expect])], 'got': got if got == 'revert' else [hex(g) for g in got]})

# FullMath.mulDiv (src/libraries/FullMath.sol:14-102): floor(a*b/d), revert if d == 0 or result >= 2^256
def mul_div(a, b, d):
    if d == 0: return 'revert'
    q = a * b // d
    return 'revert' if q >= M else q
def mul_div_up(a, b, d):
    if d == 0: return 'revert'
    q = -(-(a * b) // d)
    return 'revert' if q >= M else q
E = edges256()
pairs = [(a, b) for a in E for b in E][::3]
# the ruint 1.21.0 shape: quotient within 2^129 of 2^256 with a four limb denominator
def near_top():
    d = rnd.getrandbits(256) | (1 << 255); q = M - 1 - rnd.getrandbits(129); r = rnd.randrange(d)
    p = q * d + r; a = rnd.getrandbits(128) | 1
    while p % a: a = rnd.getrandbits(rnd.randint(1, 200)) | 1
    return a, p // a, d
for (a, b) in pairs:
    for d in (1, 3, 1 << 96, 1 << 128, 10 ** 6, MASK, (1 << 255) + 1, b | 1, 0):
        check('mulDiv', 'fun_mulDiv', [a, b, d], mul_div(a, b, d))
for _ in range(N):
    a, b, d = rwide(), rwide(), rwide(); check('mulDiv', 'fun_mulDiv', [a, b, d], mul_div(a, b, d))
    a, b, d = near_top(); check('mulDiv', 'fun_mulDiv', [a, b, d], mul_div(a, b, d)); check('mulDivRoundingUp', 'fun_mulDivRoundingUp', [a, b, d], mul_div_up(a, b, d))
    a, b, d = rwide(), rwide(), rwide(); check('mulDivRoundingUp', 'fun_mulDivRoundingUp', [a, b, d], mul_div_up(a, b, d))
for (a, b) in pairs:
    for d in (1, MASK, 1 << 128, 0, 7):
        check('mulDivRoundingUp', 'fun_mulDivRoundingUp', [a, b, d], mul_div_up(a, b, d))
# constant-denominator clones made by the optimizer
for (a, b) in pairs + [(rwide(), rwide()) for _ in range(N)]:
    check('mulDiv_40234 (d = 2^128)', 'fun_mulDiv_40234', [a, b], mul_div(a, b, 1 << 128))
    check('mulDiv_40430 (d = 10^6)', 'fun_mulDiv_40430', [a, b], mul_div(a, b, 10 ** 6))
    check('mulDiv_40437 (d = 2^96)', 'fun_mulDiv_40437', [a, b], mul_div(a, b, 1 << 96))
    check('mulDiv_40456 (b = 2^96)', 'fun_mulDiv_40456', [a, b], mul_div(a, 1 << 96, b))

# BitMath.mostSignificantBit (src/libraries/BitMath.sol:14-27)
for x in E + [rwide() for _ in range(N)] + [1 << k for k in range(256)] + [(1 << k) - 1 for k in range(1, 257)]:
    x &= MASK; check('mostSignificantBit', 'fun_mostSignificantBit', [x], 'revert' if x == 0 else x.bit_length() - 1)

# TickMath.getSqrtPriceAtTick (src/libraries/TickMath.sol:56-112): int24 argument, may arrive with dirty upper bits
ticks = set(range(-887272, -887262)) | set(range(887262, 887273)) | set(range(-40, 41)) | {887273, -887273, 8388607, -8388608, 1 << 19, -(1 << 19)}
ticks |= {rnd.randint(-887272, 887272) for _ in range(N)}
for t in sorted(ticks):
    exp = 'revert' if abs(t) > 887272 else V.get_sqrt_price_at_tick(t)
    check('getSqrtPriceAtTick', 'fun_getSqrtPriceAtTick', [u(t)], exp)
    check('getSqrtPriceAtTick dirty', 'fun_getSqrtPriceAtTick', [dirty(u(t), 24)], exp)
# monotonic, and exact for every power of two tick and its negation
for k in range(20):
    for t in (1 << k, -(1 << k)):
        check('getSqrtPriceAtTick', 'fun_getSqrtPriceAtTick', [u(t)], V.get_sqrt_price_at_tick(t))

# TickMath.getTickAtSqrtPrice (src/libraries/TickMath.sol:119-235)
MIN_P, MAX_P = 4295128739, 1461446703485210103287273052203988822378723970342
prices = {MIN_P - 1, MIN_P, MIN_P + 1, MAX_P - 1, MAX_P, MAX_P + 1, 0, U160, 1 << 96, (1 << 96) - 1, (1 << 96) + 1}
for _ in range(N):
    t = rnd.randint(-887272, 887271); p = V.get_sqrt_price_at_tick(t); prices |= {p, p - 1, p + 1}
    prices.add(rnd.randint(MIN_P, MAX_P - 1))
def tick_of(p):
    if p < MIN_P or p >= MAX_P: return 'revert'
    return V.get_tick_at_sqrt_price(p)
for p in sorted(prices):
    exp = tick_of(p)
    check('getTickAtSqrtPrice', 'fun_getTickAtSqrtPrice', [p], exp if exp == 'revert' else u(exp))
    check('getTickAtSqrtPrice dirty', 'fun_getTickAtSqrtPrice', [dirty(p, 160)], exp if exp == 'revert' else u(exp))

# SqrtPriceMath.getAmount0Delta / getAmount1Delta (unsigned, src/libraries/SqrtPriceMath.sol:188-254)
def amt0(pa, pb, L, up):
    pa, pb = min(pa, pb), max(pa, pb)
    if pa == 0: return 'revert'
    n1 = L << 96; n2 = pb - pa
    if up:
        q = mul_div_up(n1, n2, pb)
        return q if q == 'revert' else -(-q // pa)
    q = mul_div(n1, n2, pb)
    return q if q == 'revert' else q // pa
def amt1(pa, pb, L, up):
    n = abs(pa - pb); q = L * n // (1 << 96)
    return q + (1 if up and (L * n) % (1 << 96) else 0)
for _ in range(N):
    pa, pb = rnd.choice([rnd.getrandbits(160), rnd.randint(MIN_P, MAX_P), 0, 1, U160]), rnd.choice([rnd.getrandbits(160), rnd.randint(MIN_P, MAX_P), U160])
    L = rnd.choice([rnd.getrandbits(128), U128, 0, 1, rnd.getrandbits(rnd.randint(1, 128))])
    check('getAmount0Delta_40418 (roundUp)', 'fun_getAmount0Delta_40418', [dirty(pa, 160), dirty(pb, 160), dirty(L, 128)], amt0(pa, pb, L, True))
    check('getAmount0Delta_40419 (roundDown)', 'fun_getAmount0Delta_40419', [dirty(pa, 160), dirty(pb, 160), dirty(L, 128)], amt0(pa, pb, L, False))
    check('getAmount1Delta_40416 (roundUp)', 'fun_getAmount1Delta_40416', [dirty(pa, 160), dirty(pb, 160), dirty(L, 128)], amt1(pa, pb, L, True))
    check('getAmount1Delta_40417 (roundDown)', 'fun_getAmount1Delta_40417', [dirty(pa, 160), dirty(pb, 160), dirty(L, 128)], amt1(pa, pb, L, False))
    # signed wrappers (SqrtPriceMath.sol:261-288): int128 liquidity, toInt256 check
    l = sx(rnd.getrandbits(128), 128) if rnd.random() < .8 else rnd.choice([-(1 << 127), (1 << 127) - 1, 0, -1, 1])
    a0 = amt0(pa, pb, -l, False) if l < 0 else amt0(pa, pb, l, True)
    e0 = a0 if a0 == 'revert' else ('revert' if a0 >= 1 << 255 else u(a0 if l < 0 else -a0))
    check('getAmount0Delta signed', 'fun_getAmount0Delta', [dirty(pa, 160), dirty(pb, 160), dirty(u(l), 128)], e0)
    a1 = amt1(pa, pb, -l, False) if l < 0 else amt1(pa, pb, l, True)
    e1 = 'revert' if a1 >= 1 << 255 else u(a1 if l < 0 else -a1)
    check('getAmount1Delta signed', 'fun_getAmount1Delta', [dirty(pa, 160), dirty(pb, 160), dirty(u(l), 128)], e1)

# getNextSqrtPriceFromAmount0RoundingUp, add = true (fun_...) and add = false (_40426): SqrtPriceMath.sol:31-74
def np0(p, L, a, add):
    if a == 0: return p
    n1 = L << 96
    if add:
        prod = (a * p) & MASK
        if prod // a == p and n1 + prod < M:
            return mul_div_up(n1, p, n1 + prod) & U160 if mul_div_up(n1, p, n1 + prod) != 'revert' else 'revert'
        if p == 0: return 'revert'
        den = n1 // p + a
        if den >= M: return 'revert'
        return (-(-n1 // den)) & U160
    prod = (a * p) & MASK
    if not (prod // a == p and n1 > prod): return 'revert'
    r = mul_div_up(n1, p, n1 - prod)
    return 'revert' if r == 'revert' or r > U160 else r
for _ in range(N):
    p = rnd.choice([rnd.randint(MIN_P, MAX_P), MIN_P, MAX_P - 1, rnd.getrandbits(160) | 1]); L = rnd.choice([rnd.getrandbits(128) | 1, U128, 1, rnd.getrandbits(rnd.randint(1, 128)) | 1])
    a = rnd.choice([0, 1, rnd.getrandbits(rnd.randint(1, 256)), MASK, rnd.getrandbits(96)])
    dp = dirty(p, 160)
    check('getNextSqrtPriceFromAmount0RoundingUp (add)', 'fun_getNextSqrtPriceFromAmount0RoundingUp', [dp, dirty(L, 128), a], np0(p, L, a, True) if a else dp)
    e = np0(p, L, a, False)
    check('getNextSqrtPriceFromAmount0RoundingUp_40426 (subtract)', 'fun_getNextSqrtPriceFromAmount0RoundingUp_40426', [p, L, a], e)

# LiquidityMath.addDelta (src/libraries/LiquidityMath.sol:10-19)
for _ in range(N):
    x = rnd.choice([rnd.getrandbits(128), U128, 0, 1]); y = rnd.choice([sx(rnd.getrandbits(128), 128), -(1 << 127), (1 << 127) - 1, -1, 1, 0, -x, U128 - x]); y = sx(y, 128)
    z = x + y; e = 'revert' if z < 0 or z > U128 else z
    check('addDelta', 'fun_addDelta', [dirty(x, 128), dirty(u(y), 128)], e)
# BalanceDelta sub (src/types/BalanceDelta.sol:34-46) and SafeCast casts
def bd(a0, a1): return ((a0 & U128) << 128) | (a1 & U128)
for _ in range(N):
    a0, a1, b0, b1 = (rnd.choice([sx(rnd.getrandbits(128), 128), -(1 << 127), (1 << 127) - 1, 0, -1]) for _ in range(4))
    r0, r1 = a0 - b0, a1 - b1
    e = 'revert' if not (-(1 << 127) <= r0 < 1 << 127 and -(1 << 127) <= r1 < 1 << 127) else bd(r0, r1)
    check('BalanceDelta.sub', 'fun_sub', [bd(a0, a1), bd(b0, b1)], e)
for x in E + [rwide() for _ in range(N)]:
    check('toUint160', 'fun_toUint160', [x], x if x <= U160 else 'revert')
    check('toInt128(int256)', 'fun_toInt128', [x], x if -(1 << 127) <= s(x) < 1 << 127 else 'revert')
    check('toInt128(uint256)', 'fun_toInt128_5750', [x], x if x < 1 << 127 else 'revert')
    y = rwide()
    check('wrapping_div_uint256', 'wrapping_div_uint256', [x, y], 'revert' if y == 0 else x // y)
    check('checked_add_int256', 'checked_add_int256', [x, y], 'revert' if not (-(1 << 255) <= s(x) + s(y) < 1 << 255) else u(s(x) + s(y)))
    a, b = sx(x, 128), sx(y, 128)
    check('checked_add_int128', 'checked_add_int128', [x, y], 'revert' if not (-(1 << 127) <= a + b < 1 << 127) else u(a + b))

# TickBitmap.flipTick (src/libraries/TickBitmap.sol:47-75): reads and writes storage
def slot_of(word, base):
    return int.from_bytes(H.mod['keccak'](u(word).to_bytes(32, 'big') + base.to_bytes(32, 'big')), 'big')
flip = out.setdefault('flipTick', {'cases': 0, 'reverts': 0, 'mismatch': []})
for _ in range(N):
    ts = rnd.choice([1, 2, 3, 10, 60, 200, 32767, rnd.randint(1, 32767)])
    t = rnd.choice([rnd.randint(-887272 // ts, 887272 // ts) * ts, rnd.randint(-887272, 887272), -ts, ts, 0, (-887272 // ts) * ts])
    base = rnd.getrandbits(256)
    w = H.World({H.PM: H.HCODE}); w.max_steps = 100000
    w.init_stack = [H.RET, dirty(u(ts), 24), dirty(u(t), 24), base]; w.init_pc = H.EP['fun_flipTick']
    ok, ret = w.run(H.PM, H.PM, 0, 0, b'', False, 0)
    flip['cases'] += 1
    if t % ts:  # Solidity % truncates toward zero, Python's toward -inf; both are 0 together
        flip['reverts'] += 1
        good = (not ok) and ret[:4] == bytes.fromhex('d4d8f3e6') and int.from_bytes(ret[4:36], 'big') == u(t) and int.from_bytes(ret[36:68], 'big') == u(ts)
    else:
        c = int(t / ts)  # exact
        sl = slot_of(c >> 8, base)
        good = ok and w.storage == {(H.PM, sl): 1 << (c & 0xff)}
    if not good and len(flip['mismatch']) < 10: flip['mismatch'].append({'tick': t, 'tickSpacing': ts, 'ok': ok, 'ret': ret.hex(), 'storage': {hex(k[1]): hex(v) for k, v in w.storage.items()}})

summary = {k: {'cases': v['cases'], 'reverts': v['reverts'], 'mismatches': len(v['mismatch'])} for k, v in out.items()}
json.dump({'summary': summary, 'detail': out}, open(sys.argv[1], 'w'), indent=1)
for k, v in summary.items(): print('%-58s %6d cases %5d reverts %3d mismatches' % (k, v['cases'], v['reverts'], v['mismatches']))
print('total', sum(v['cases'] for v in summary.values()), 'mismatches', sum(v['mismatches'] for v in summary.values()))
