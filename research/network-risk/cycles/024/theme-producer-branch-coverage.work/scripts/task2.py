"""Task 2: arithmetic sites, counts per network and operand ranges. writes ../out/task2.json"""
import json, glob, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
from aggregate import load
NETS = (143, 4326, 999, 8453)
BR = {}; W = {}; DET = {}
for c in NETS:
    br, w, tot, mm, pertx = load(c); BR[c] = br; W[c] = w
    d = collections.Counter()
    for f in glob.glob('%s/../out/%d/shard*.json' % (HERE, c)): d.update(json.load(open(f))['detail'])
    DET[c] = dict(d)
def j(pc): return {str(c): [BR[c].get('%d:1' % pc, 0), BR[c].get('%d:0' % pc, 0)] for c in NETS}
def w(pc, sig=False):
    out = {}
    for c in NETS:
        e = W[c].get(str(pc))
        if not e: out[str(c)] = {'n': 0}; continue
        out[str(c)] = {'n': e[1], 'operands': [{'min': hex(a[0]), 'max': hex(a[1]), 'sminBits': (a[2]).bit_length() * (-1 if a[2] < 0 else 1), 'smax': a[3] if abs(a[3]) < 1 << 64 else hex(a[3]), 'smin': a[2] if abs(a[2]) < 1 << 64 else hex(a[2]), 'negCount': a[4], 'bitlens': [min(a[5]), max(a[5])]} for a in e[2]]}
    return out
def det(pc): return {str(c): {k.split('|', 1)[1]: v for k, v in DET[c].items() if k.split('|')[0] == str(pc)} for c in NETS}
T = {
 'FullMath.mulDiv general copy (entry 22851; getAmount0Delta SqrtPriceMath.sol:209 and mulDivRoundingUp FullMath.sol:111): JUMPI 22917 prod1==0 [taken=prod1==0, fallthrough=prod1!=0]': j(22917),
 'same copy, MULMOD 22892 mm := mulmod(a,b,not(0)) operands': w(22892),
 'same copy, MULMOD 22921 remainder := mulmod(a,b,denominator) (prod1!=0 path only) operands': w(22921),
 'FullMath copy 1 (Position.sol:94/96 fees, denominator 2^128): JUMPI 22358': j(22358), 'copy 1 remainder MULMOD 22378': w(22378),
 'FullMath copy 2 (SwapMath.sol:65 exact-in fee, denominator 1e6): JUMPI 22473': j(22473), 'copy 2 remainder MULMOD 22513': w(22513),
 'FullMath copy 3 (SqrtPriceMath.sol:250 getAmount1Delta, denominator 2^96): JUMPI 22623': j(22623), 'copy 3 remainder MULMOD 22639': w(22639),
 'FullMath copy 4 (SqrtPriceMath.sol:97, amount > uint160 max, add): JUMPI 22746': j(22746), 'copy 4 remainder MULMOD 22763': w(22763),
 'mulDivRoundingUp FullMath.sol:112 (shared copy) round-up JUMPI 23682 [taken=remainder!=0 increments]': j(23682), 'its MULMOD 23678': w(23678),
 'mulDivRoundingUp(amount, Q96, liquidity) SqrtPriceMath.sol:105 (amount > uint160 max, subtract): JUMPI 20963 [fallthrough=increment]': j(20963), 'its MULMOD 20958': w(20958),
 'getAmount1Delta round-up MULMOD 23094 (SqrtPriceMath.sol:252)': w(23094),
 'getNextSqrtPriceFromAmount0RoundingUp SqrtPriceMath.sol:37 amount==0 JUMPI 23823 (add) / 23705 (subtract)': {'add': j(23823), 'subtract': j(23705)},
 'getNextSqrtPriceFromAmount0RoundingUp SqrtPriceMath.sol:43 product/amount==sqrtP JUMPI 23900 [taken=no overflow]': j(23900),
 'getNextSqrtPriceFromAmount0RoundingUp SqrtPriceMath.sol:45 denominator>=numerator1 JUMPI 23942 [fallthrough=no wrap]': j(23942),
 'getNextSqrtPriceFromAmount0RoundingUp subtract PriceOverflow check SqrtPriceMath.sol:59 JUMPI 23781': j(23781), 'its DIV 23774 operands': w(23774),
 'UnsafeMath.divRoundingUp SqrtPriceMath.sol:52 fallback DIV 23928 / MOD 23924': {'div': w(23928), 'mod': w(23924)},
 'getNextSqrtPriceFromAmount1RoundingDown: getNextSqrtPriceFromOutput ternary SqrtPriceMath.sol:175 JUMPI 20748': j(20748),
 'getNextSqrtPriceFromAmount1RoundingDown subtract divRoundingUp DIV 20806 / MOD 20802 (SqrtPriceMath.sol:104)': {'div': w(20806), 'mod': w(20802)},
 'getNextSqrtPriceFromAmount1RoundingDown NotEnoughLiquidity JUMPI 20840': j(20840),
 'getAmount0Delta order swap SqrtPriceMath.sol:194 JUMPI 23217 / 23399': {'23217': j(23217), '23399': j(23399)},
 'getAmount0Delta roundUp divRoundingUp DIV 23326 / MOD 23322': {'div': w(23326), 'mod': w(23322)},
 'absDiff SAR 23075 / 23154 (SqrtPriceMath.sol:219)': {'23075': w(23075), '23154': w(23154)},
 'getSqrtPriceAtTick SAR 16736 sign mask (TickMath.sol:60) by tick sign': det(16736),
 'getSqrtPriceAtTick GT 16746 absTick vs MAX_TICK (TickMath.sol:70) by absTick': det(16746), 'GT 16746 operands': w(16746),
 'getSqrtPriceAtTick DIV 17034 (TickMath.sol:102, tick>0)': w(17034),
 'getTickAtSqrtPrice GT 17995 (TickMath.sol:127) a=sqrtPrice-MIN, b=MAX-MIN-1': det(17995), 'GT 17995 operands': w(17995),
 'getTickAtSqrtPrice SAR 18533 / 18558 (TickMath.sol ~ log_sqrt10001 >> 128)': {'18533': w(18533), '18558': w(18558)},
 'getTickAtSqrtPrice tickLow==tickHi / choice JUMPI 18635 (TickMath.sol:235)': j(18635),
 'TickBitmap.position SAR 19307 (lte search) by compressed sign and bitPos': det(19307),
 'TickBitmap.position SAR 21130 (gt search, ++compressed) by sign and bitPos': det(21130),
 'TickBitmap.flipTick SAR 16675 by sign and bitPos': det(16675),
 'TickBitmap.compress SMOD/SDIV 19221 / 19224': {'smod': w(19221), 'sdiv': w(19224)},
 'TickBitmap.flipTick SMOD 16665 / SDIV 16670': {'smod': w(16665), 'sdiv': w(16670)},
 'TickBitmap initialized ternary lte JUMPI 19371 / gt JUMPI 21204': {'lte': j(19371), 'gt': j(21204)},
 'BitMath.mostSignificantBit BYTE 23652 / leastSignificantBit BYTE 21416': {'msb': w(23652), 'lsb': w(21416)},
 'LiquidityMath.addDelta SIGNEXTEND 17796 by sign of y': det(17796), 'LiquidityMath shr(128) JUMPI 17808 [taken=revert]': j(17808),
 'BalanceDelta amount0 SAR 1832 / 13947 / 15519 / 15785': {str(p): w(p) for p in (1832, 13947, 15519, 15785)},
 'toBalanceDelta / add / sub SAR 6059 6063 17866 17870': {str(p): w(p) for p in (6059, 6063, 17866, 17870)},
 'Pool.swap protocolFee > 0 JUMPI 19803 (Pool.sol:385)': j(19803), 'PoolManager.sol:238 amountToProtocol > 0 JUMPI 1765': j(1765),
 'ProtocolFeeLibrary.calculateSwapFee DIV 22238': w(22238), 'Pool.sol:401 liquidity>0 feeGrowth JUMPI 19832': j(19832), 'UnsafeMath.simpleMulDiv DIV 20231': w(20231),
 'Pool.sol:311 swapFee >= MAX_SWAP_FEE JUMPI 18969': j(18969), 'Pool.sol:351 tickNext <= MIN_TICK 19422 / 354 >= MAX_TICK 19441': {'min': j(19422), 'max': j(19441)},
 'Pool.donate Pool.sol:473/476 JUMPI 10277 / 10283': {'473': j(10277), '476': j(10283)},
}
json.dump(T, open(HERE + '/../out/task2.json', 'w'), indent=1)
for k, v in T.items(): print(k, '\n   ', json.dumps(v)[:700])
