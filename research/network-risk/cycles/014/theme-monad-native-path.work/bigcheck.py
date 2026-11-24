"""Mined Monad swaps (v4 PoolManager and v3 style pools) against the formulas of src/ as
transcribed in tools/opdiff/v4math.py, with every FullMath.mulDiv call tagged by call site and
by whether its product needs more than 256 bits (prod1 != 0), plus the overflow fallback of
getNextSqrtPriceFromAmount0RoundingUp (src/libraries/SqrtPriceMath.sol:42-52).
FAULT=mm1  plants MULMOD(a,b,2^256-1) off by one on every call
FAULT=mm1big plants it only when a*b >= 2^256 (the large-number branch only)."""
import sys, os, json, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from evm import s, MASK

import threading
_tl = threading.local()
def T():
    if not hasattr(_tl, 't'): _tl.t = []
    return _tl.t
_orig_mulmod = m.mulmod
FAULT = os.environ.get('FAULT', '')
def mulmod_f(a, b, c):
    r = _orig_mulmod(a, b, c)
    if c == MASK and (FAULT == 'mm1' or (FAULT == 'mm1big' and a * b >> 256)):
        r = (r + 1) % c
    return r
m.mulmod = mulmod_f
_orig_muldiv = m.mul_div
SKIP = {'mul_div', 'mul_div_rounding_up', 'tagged_muldiv'}
def tagged_muldiv(a, b, d):
    f = sys._getframe(1)
    while f.f_code.co_name in SKIP: f = f.f_back
    T().append((f.f_code.co_name, bool((a * b) >> 256)))
    return _orig_muldiv(a, b, d)
m.mul_div = tagged_muldiv
_orig_np0 = m.next_price_amount0_rounding_up
def np0(p, L, amount, add_):
    if amount and add_:
        n1 = L << 96; prod = amount * p
        T().append(('amount0_fallback', prod > MASK or n1 + prod > MASK))
    return _orig_np0(p, L, amount, add_)
m.next_price_amount0_rounding_up = np0
_orig_np1 = m.next_price_amount1_rounding_down
def np1(p, L, amount, add_):
    T().append(('amount1_over_160', amount > m.U160))
    return _orig_np1(p, L, amount, add_)
m.next_price_amount1_rounding_down = np1

def attempt(fn):
    del T()[:]
    try:
        ok = fn()
    except m.Revert:
        ok = False
    return ok, list(T())

def check(p0, p1, liq, paid, got, fee):
    """paid, got >= 0 from the swapper's side. Returns (mode, trace) or (None, [])."""
    zfo = p1 < p0
    def out_(): return m.amount1_delta(p1, p0, liq, False) if zfo else m.amount0_delta(p0, p1, liq, False)
    def in_(): return m.amount0_delta(p1, p0, liq, True) if zfo else m.amount1_delta(p0, p1, liq, True)
    def exact_in():
        lf = m.mul_div(paid, m.MAX_SWAP_FEE - fee, m.MAX_SWAP_FEE)
        return m.next_price_from_input(p0, liq, lf, zfo) == p1 and out_() == got
    ok, tr = attempt(exact_in)
    if ok: return 'exactIn', tr
    if fee >= m.MAX_SWAP_FEE: return None, []
    def total(): a = in_(); return a + m.mul_div_rounding_up(a, fee, m.MAX_SWAP_FEE - fee)
    def exact_out(): return total() == paid and got <= out_() and m.next_price_from_output(p0, liq, got, zfo) == p1
    ok, tr = attempt(exact_out)
    if ok: return 'exactOut', tr
    def target(): return total() == paid and out_() == got
    ok, tr = attempt(target)
    if ok: return 'target', tr
    return None, []

def word(d, i): return int(d[2 + 64 * i:2 + 64 * (i + 1)], 16)
