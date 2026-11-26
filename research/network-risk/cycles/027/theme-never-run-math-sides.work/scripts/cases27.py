"""Cycle 27 Task 2 cases for the cycle 25 driver (cycles/025/theme-unexecuted-sides.work/src/Driver.sol).
Deterministic grid, no random sampling (no seed needed).
usage: python3 cases27.py <out.json>
Groups:
  LSB b   : leastSignificantBit at every bit position b = 0..255 of a bitmap word (one-for-zero search,
            TickBitmap.sol:105-117, BitMath.sol:31-50). Only Monad's mined frames used some of these shift values
            at pc 21364.
  MSB b   : mostSignificantBit at every bit position b = 0..255 (zero-for-one search, TickBitmap.sol:85-100,
            BitMath.sol:12-24); b = 255 gives an operand >= 2^255 at BitMath.sol:15 (LT of opposite sign).
  R105 L  : the mulDivRoundingUp(amount, Q96, liquidity) of SqrtPriceMath.sol:105 (sides 20942:0, 20963:0/1, run
            only by cycle 25) with the liquidity word varied, by the same storage override as cycle 25 case 1477.
  MIS t   : negative misaligned ticks into modifyLiquidity (TickBitmap.sol:53 SMOD of a negative inexact tick).
  DON a   : donate amounts at and above 2^255 (SafeCast.sol:57 LT with an operand of the other sign).
Token addresses: 0x20000000 + 2k, distinct from cycle 25 (0x10000000 + 2k)."""
import sys, os, json
NR = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, NR + '/cycles/025/theme-unexecuted-sides.work/scripts')
from common import MIN_SQRT, MAX_SQRT
import v4math as V

cases = []


def add(c, tag):
    k = len(cases) + 1
    t0 = 0x20000000 + 2 * k
    c.setdefault('hooks', 0); c.update(t0=t0, t1=t0 + 1, tag=tag, id=len(cases))
    cases.append(c)


P = V.get_sqrt_price_at_tick
L = 10 ** 18
for b in range(256):
    if b == 0:
        add(dict(kind=0, fee=500, ts=1, sqrtP=P(-1), tl=-300, tu=0, liq=L, zfo=False, amt=-1000, lim=P(520)), 'LSB b=0')
    else:
        add(dict(kind=0, fee=500, ts=1, sqrtP=P(0), tl=-300, tu=b, liq=L, zfo=False, amt=-1000, lim=P(520)), f'LSB b={b}')
for b in range(256):
    add(dict(kind=0, fee=500, ts=1, sqrtP=P(255), tl=b, tu=600, liq=L, zfo=True, amt=-1000, lim=P(-260)), f'MSB b={b}')
# R105: copies of cycle 25 case 1477 with a different liquidity word
allc = {c['id']: c for c in json.load(open(NR + '/cycles/025/theme-unexecuted-sides.work/out/allcases.json'))['cases']}
base = allc[1477]
slots = sorted(base['storage'])
for nm, liq in [('2^100', 1 << 100), ('2^100+1', (1 << 100) + 1), ('3*2^99', 3 << 99), ('2^101-1', (1 << 101) - 1),
                ('2^127+1', (1 << 127) + 1), ('2^128-1', (1 << 128) - 1), ('2^100+2^61', (1 << 100) + (1 << 61))]:
    c = {k: v for k, v in base.items() if k not in ('id', 'tag', 't0', 't1')}
    c['storage'] = dict(base['storage']); c['storage'][slots[1]] = hex(liq)
    # the override keys belong to the cycle 25 pool id, so keep its token addresses
    c2 = dict(c); c2['tag'] = f'R105 L={nm}'; c2['id'] = len(cases); c2['t0'] = base['t0']; c2['t1'] = base['t1']
    cases.append(c2)
for t in (-61, -1, -59, -887221, -119):
    add(dict(kind=0, fee=3000, ts=60, sqrtP=1 << 96, tl=t, tu=600, liq=L, zfo=True, amt=-1000, lim=MIN_SQRT + 1), f'MIS tl={t}')
for nm, a in [('2^255', 1 << 255), ('2^256-1', (1 << 256) - 1), ('2^255+2^127', (1 << 255) + (1 << 127))]:
    add(dict(kind=1, fee=500, ts=60, sqrtP=1 << 96, tl=-600, tu=600, liq=L, p=[a, 0]), f'DON amount0={nm}')
    add(dict(kind=1, fee=500, ts=60, sqrtP=1 << 96, tl=-600, tu=600, liq=L, p=[0, a]), f'DON amount1={nm}')
json.dump({'note': 'deterministic grid, no seed', 'cases': cases}, open(sys.argv[1], 'w'), indent=0)
print(len(cases))
