"""Task 1: largest product liquidity * |sqrtP_target - sqrtP_cur| one swap step can see, per tick spacing,
from src/libraries/Pool.sol (maxLiquidityPerTick, swap loop), TickBitmap.nextInitializedTickWithinOneWord,
SwapMath.computeSwapStep, SqrtPriceMath.getAmount1Delta. Uses v4math (transcription of src/) for prices."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from math import log2
MAXT = m.MAX_TICK
def max_liq_per_tick(ts):
    mn = -(887272 // ts) - (1 if 887272 % ts else 0)   # sdiv truncates toward zero, minus 1 when smod < 0
    mx = 887272 // ts
    return ((1 << 128) - 1) // (mx - mn + 1)
def sp(t): return m.get_sqrt_price_at_tick(t)
out = []
for ts in (1, 10, 60, 100, 200, 1000, 10000, 32767):
    L1 = max_liq_per_tick(ts); Lmax = (1 << 128) - 1
    # one-word step upward: from the first usable tick of the word that contains the top usable tick, to min(MAX_TICK, word end)
    top = (MAXT // ts) * ts
    comp = top // ts; wordStart = (comp >> 8) << 8
    lo = max(wordStart * ts, -((887272 // ts) + (1 if 887272 % ts else 0)) * ts)
    lo = max(lo, -887272)
    diff_word = sp(MAXT) - sp(lo) if lo < MAXT else 0
    # also the previous word (full 256 compressed ticks) in case the top word is short
    w2s = (wordStart - 256) * ts
    diff_prev = sp(min(MAXT, wordStart * ts)) - sp(max(-887272, w2s))
    d = max(diff_word, diff_prev)
    # cheapest single position reaching 2^256 with a single-position liquidity L1: smallest price diff needed
    need = (1 << 256) // L1 + 1
    # lowest tick t such that one word step above t gives diff >= need (scan coarse)
    rec = {'tickSpacing': ts, 'maxLiquidityPerTick': L1, 'log2MaxLiquidityPerTick': round(log2(L1), 3),
           'maxDiffOneStep': d, 'log2MaxDiffOneStep': round(log2(d), 3),
           'log2MaxProductSinglePosition': round(log2(L1 * d), 3), 'log2MaxProductPoolLiquidity': round(log2(Lmax * d), 3),
           'singlePositionReaches2^256': L1 * d >= (1 << 256), 'poolLiquidityReaches2^256': Lmax * d >= (1 << 256)}
    # lowest start tick where a one-word step with L1 reaches 2^256 (step from t to t+256*ts capped at MAX_TICK)
    lowest = None
    t = -887272
    step = max(ts, 64)
    for t in range(-(887272 // ts) * ts, top, ts * max(1, 2000 // ts)):
        tgt = min(MAXT, t + 256 * ts)
        if L1 * (sp(tgt) - sp(t)) >= (1 << 256): lowest = t; break
    rec['lowestStartTickSinglePosition'] = lowest
    if lowest is not None:
        tgt = min(MAXT, lowest + 256 * ts); pc, pt = sp(lowest), sp(tgt)
        # position [lowest, tgt] with current price at lowest: token0 needed = amount0Delta(pc, pt, L1, up), token1 = 0
        a0 = m.amount0_delta(pc, pt, L1, True)
        rec['position'] = {'tickLower': lowest, 'tickUpper': tgt, 'liquidity': L1, 'token0Units': a0, 'token1Units': 0,
                           'amount1ToTargetLog2': round(log2(L1 * (pt - pc) >> 96), 2)}
    # lowest start tick reaching 2^256 with pool liquidity 2^128-1 (needs many stacked positions)
    for t in range(-(887272 // ts) * ts, top, ts * max(1, 2000 // ts)):
        tgt = min(MAXT, t + 256 * ts)
        if Lmax * (sp(tgt) - sp(t)) >= (1 << 256): rec['lowestStartTickPoolLiquidityMax'] = t; break
    out.append(rec)
for r in out: print(json.dumps({k: (v if not isinstance(v, int) or abs(v) < 1 << 64 else hex(v)) for k, v in r.items()}))
json.dump(out, open('out/bounds.json', 'w'), indent=1, default=str)
