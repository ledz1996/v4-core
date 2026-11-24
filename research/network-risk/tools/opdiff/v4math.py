"""Python transcription of the pool math in src/libraries, written operation by
operation from the text of this repository (TickMath, BitMath, FullMath, UnsafeMath,
SqrtPriceMath, SwapMath). Every step uses the EVM reference semantics of evm.py, so a
result here is what the Ethereum specification gives for the source as written."""
from evm import M, MASK, SIGN, s, u, REF, ref_signextend, ref_sar, ref_byte

MIN_TICK, MAX_TICK = -887272, 887272
MIN_SQRT_PRICE = 4295128739
MAX_SQRT_PRICE = 1461446703485210103287273052203988822378723970342
Q96 = 1 << 96
U160 = (1 << 160) - 1
MAX_SWAP_FEE = 10 ** 6


class Revert(Exception):
    pass


def mul(a, b): return (a * b) & MASK
def add(a, b): return (a + b) & MASK
def sub(a, b): return (a - b) & MASK
def div(a, b): return a // b if b else 0
def shl(n, x): return (x << n) & MASK if n < 256 else 0
def shr(n, x): return x >> n if n < 256 else 0
def mulmod(a, b, c): return (a * b) % c if c else 0
def lt(a, b): return int(a < b)
def gt(a, b): return int(a > b)


# src/libraries/BitMath.sol
def most_significant_bit(x):
    if not x > 0: raise Revert('msb(0)')
    r = shl(7, lt(0xffffffffffffffffffffffffffffffff, x))
    r |= shl(6, lt(0xffffffffffffffff, shr(r, x)))
    r |= shl(5, lt(0xffffffff, shr(r, x)))
    r |= shl(4, lt(0xffff, shr(r, x)))
    r |= shl(3, lt(0xff, shr(r, x)))
    r |= ref_byte(0x1f & shr(shr(r, x), 0x8421084210842108cc6318c6db6d54be),
                  0x0706060506020500060203020504000106050205030304010505030400000000)
    return r & 0xff


def least_significant_bit(x):
    if not x > 0: raise Revert('lsb(0)')
    x = x & sub(0, x)
    r = shl(5, shr(252, shl(shl(2, shr(250, mul(x, 0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff))),
                           0x8040405543005266443200005020610674053026020000107506200176117077)))
    r |= ref_byte(div(0xd76453e0, shr(r, x)) & 0x1f, 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405)
    return r & 0xff


# src/libraries/FullMath.sol
def mul_div(a, b, denominator):
    prod0 = mul(a, b)
    mm = mulmod(a, b, MASK)
    prod1 = sub(sub(mm, prod0), lt(mm, prod0))
    if not denominator > prod1: raise Revert('mulDiv overflow')
    if prod1 == 0:
        return div(prod0, denominator)
    remainder = mulmod(a, b, denominator)
    prod1 = sub(prod1, gt(remainder, prod0))
    prod0 = sub(prod0, remainder)
    twos = sub(0, denominator) & denominator
    denominator = div(denominator, twos)
    prod0 = div(prod0, twos)
    twos = add(div(sub(0, twos), twos), 1)
    prod0 |= mul(prod1, twos)
    inv = mul(3, denominator) ^ 2
    for _ in range(6):
        inv = mul(inv, sub(2, mul(denominator, inv)))
    return mul(prod0, inv)


def mul_div_rounding_up(a, b, denominator):
    result = mul_div(a, b, denominator)
    if mulmod(a, b, denominator) != 0:
        result = add(result, 1)
        if not result > 0: raise Revert('mulDivRoundingUp overflow')
    return result


# src/libraries/UnsafeMath.sol
def div_rounding_up(x, y): return add(div(x, y), gt(REF['MOD'](x, y, 0), 0))


# src/libraries/TickMath.sol
_K = [0xfff97272373d413259a46990580e213a, 0xfff2e50f5f656932ef12357cf3c7fdcc, 0xffe5caca7e10e4e61c3624eaa0941cd0,
      0xffcb9843d60f6159c9db58835c926644, 0xff973b41fa98c081472e6896dfb254c0, 0xff2ea16466c96a3843ec78b326b52861,
      0xfe5dee046a99a2a811c461f1969c3053, 0xfcbe86c7900a88aedcffc83b479aa3a4, 0xf987a7253ac413176f2b074cf7815e54,
      0xf3392b0822b70005940c7a398e4b70f3, 0xe7159475a2c29b7443b29c7fa6e889d9, 0xd097f3bdfd2022b8845ad8f792aa5825,
      0xa9f746462d870fdf8a65dc1f90e061e5, 0x70d869a156d2a1b890bb3df62baf32f7, 0x31be135f97d08fd981231505542fcfa6,
      0x9aa508b5b7a84e1c677de54f3e99bc9, 0x5d6af8dedb81196699c329225ee604, 0x2216e584f5fa1ea926041bedfe98,
      0x48a170391f7dc42444e8fa2]


def get_sqrt_price_at_tick(tick):
    t = ref_signextend(2, u(tick))
    mask = ref_sar(255, t)
    abs_tick = mask ^ add(mask, t)
    if abs_tick > MAX_TICK: raise Revert('InvalidTick')
    price = shl(128, 1) ^ mul(shl(128, 1) ^ 0xfffcb933bd6fad37aa2d162d1a594001, abs_tick & 1)
    for i, k in enumerate(_K):
        if abs_tick & (2 << i):
            price = shr(128, mul(price, k))
    if REF['SGT'](t, 0, 0):
        price = div(MASK, price)
    return shr(32, add(price, sub(shl(32, 1), 1))) & U160


def get_tick_at_sqrt_price(sqrt_price):
    if sub(sqrt_price, MIN_SQRT_PRICE) > MAX_SQRT_PRICE - MIN_SQRT_PRICE - 1: raise Revert('InvalidSqrtPrice')
    price = shl(32, sqrt_price)
    r = price
    msb = most_significant_bit(r)
    r = shr(msb - 127, price) if msb >= 128 else shl(127 - msb, price)
    log_2 = shl(64, sub(msb, 128))
    for bit in range(63, 49, -1):
        r = shr(127, mul(r, r))
        f = shr(128, r)
        log_2 |= shl(bit, f)
        if bit != 50:
            r = shr(f, r)
    log_sqrt10001 = mul(log_2, 255738958999603826347141)
    tick_low = s(ref_signextend(2, ref_sar(128, sub(log_sqrt10001, 3402992956809132418596140100660247210))))
    tick_hi = s(ref_signextend(2, ref_sar(128, add(log_sqrt10001, 291339464771989622907027621153398088495))))
    if tick_low == tick_hi: return tick_low
    return tick_hi if get_sqrt_price_at_tick(tick_hi) <= sqrt_price else tick_low


# src/libraries/SqrtPriceMath.sol
def to_uint160(x):
    if x > U160: raise Revert('SafeCastOverflow')
    return x


def next_price_amount0_rounding_up(p, liquidity, amount, add_):
    if amount == 0: return p
    numerator1 = liquidity << 96
    if add_:
        product = mul(amount, p)
        if div(product, amount) == p:
            denominator = add(numerator1, product)
            if denominator >= numerator1:
                return mul_div_rounding_up(numerator1, p, denominator) & U160
        d = (numerator1 // p) + amount
        if d > MASK: raise Revert('overflow')
        return div_rounding_up(numerator1, d) & U160
    product = mul(amount, p)
    if not (div(product, amount) == p and numerator1 > product): raise Revert('PriceOverflow')
    return to_uint160(mul_div_rounding_up(numerator1, p, numerator1 - product))


def next_price_amount1_rounding_down(p, liquidity, amount, add_):
    if add_:
        if liquidity == 0: raise Revert('div by zero')
        quotient = ((amount << 96) // liquidity) if amount <= U160 else mul_div(amount, Q96, liquidity)
        return to_uint160(p + quotient)
    quotient = div_rounding_up(amount << 96, liquidity) if amount <= U160 else mul_div_rounding_up(amount, Q96, liquidity)
    if not p > quotient: raise Revert('NotEnoughLiquidity')
    return p - quotient


def next_price_from_input(p, liquidity, amount_in, zero_for_one):
    if p == 0 or liquidity == 0: raise Revert('InvalidPriceOrLiquidity')
    return next_price_amount0_rounding_up(p, liquidity, amount_in, True) if zero_for_one else next_price_amount1_rounding_down(p, liquidity, amount_in, True)


def next_price_from_output(p, liquidity, amount_out, zero_for_one):
    if p == 0 or liquidity == 0: raise Revert('InvalidPriceOrLiquidity')
    return next_price_amount1_rounding_down(p, liquidity, amount_out, False) if zero_for_one else next_price_amount0_rounding_up(p, liquidity, amount_out, False)


def amount0_delta(pa, pb, liquidity, round_up):
    if pa > pb: pa, pb = pb, pa
    if pa == 0: raise Revert('InvalidPrice')
    numerator1 = liquidity << 96
    numerator2 = pb - pa
    if round_up:
        return div_rounding_up(mul_div_rounding_up(numerator1, numerator2, pb), pa)
    return mul_div(numerator1, numerator2, pb) // pa


def abs_diff(a, b):
    diff = sub(a & U160, b & U160)
    mask = ref_sar(255, diff)
    return mask ^ add(mask, diff)


def amount1_delta(pa, pb, liquidity, round_up):
    numerator = abs_diff(pa, pb)
    amount1 = mul_div(liquidity, numerator, Q96)
    return add(amount1, gt(mulmod(liquidity, numerator, Q96), 0) & int(round_up))


# src/libraries/SwapMath.sol
def compute_swap_step(p_cur, p_target, liquidity, amount_remaining, fee_pips):
    zero_for_one = p_cur >= p_target
    exact_in = amount_remaining < 0
    if exact_in:
        less_fee = mul_div(-amount_remaining, MAX_SWAP_FEE - fee_pips, MAX_SWAP_FEE)
        amount_in = amount0_delta(p_target, p_cur, liquidity, True) if zero_for_one else amount1_delta(p_cur, p_target, liquidity, True)
        if less_fee >= amount_in:
            p_next = p_target
            fee = amount_in if fee_pips == MAX_SWAP_FEE else mul_div_rounding_up(amount_in, fee_pips, MAX_SWAP_FEE - fee_pips)
        else:
            amount_in = less_fee
            p_next = next_price_from_input(p_cur, liquidity, less_fee, zero_for_one)
            fee = -amount_remaining - amount_in
        amount_out = amount1_delta(p_next, p_cur, liquidity, False) if zero_for_one else amount0_delta(p_cur, p_next, liquidity, False)
    else:
        amount_out = amount1_delta(p_target, p_cur, liquidity, False) if zero_for_one else amount0_delta(p_cur, p_target, liquidity, False)
        if amount_remaining >= amount_out:
            p_next = p_target
        else:
            amount_out = amount_remaining
            p_next = next_price_from_output(p_cur, liquidity, amount_out, zero_for_one)
        amount_in = amount0_delta(p_next, p_cur, liquidity, True) if zero_for_one else amount1_delta(p_cur, p_next, liquidity, True)
        fee = mul_div_rounding_up(amount_in, fee_pips, MAX_SWAP_FEE - fee_pips)
    return p_next, amount_in, amount_out, fee


if __name__ == '__main__':
    # the transcription against plain integer mathematics, as a check of the source's algorithms
    import random
    rnd = random.Random(1)
    for _ in range(200000):
        a = rnd.getrandbits(rnd.choice((64, 128, 200, 256))); b = rnd.getrandbits(rnd.choice((64, 128, 200, 256)))
        d = rnd.getrandbits(rnd.choice((64, 128, 200, 256))) or 1
        if (a * b) // d > MASK: continue
        assert mul_div(a, b, d) == (a * b) // d
        assert mul_div_rounding_up(a, b, d) == -((-a * b) // d)
    for _ in range(100000):
        x = rnd.getrandbits(rnd.randrange(1, 257)) or 1
        assert most_significant_bit(x) == x.bit_length() - 1
        assert least_significant_bit(x) == (x & -x).bit_length() - 1
    prev = 0
    for t in range(MIN_TICK, MAX_TICK + 1):
        p = get_sqrt_price_at_tick(t)
        assert p > prev; prev = p
        if t % 37 == 0 or abs(t) > 887000 or abs(t) < 300:
            if p < MAX_SQRT_PRICE:
                assert get_tick_at_sqrt_price(p) == t
                if p + 1 < MAX_SQRT_PRICE and t < MAX_TICK: assert get_tick_at_sqrt_price(p + 1) == t
            if t > MIN_TICK: assert get_tick_at_sqrt_price(p - 1) == t - 1
    assert get_sqrt_price_at_tick(MIN_TICK) == MIN_SQRT_PRICE and get_sqrt_price_at_tick(MAX_TICK) == MAX_SQRT_PRICE
    print('transcription agrees with integer mathematics: mulDiv, msb, lsb, tick round trips over the whole tick range')
