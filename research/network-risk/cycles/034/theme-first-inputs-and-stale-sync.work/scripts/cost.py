"""Cheapest position that makes the first swap step of an existing pool see a getAmount1Delta product >= 2^256.
Up direction (oneForZero, SwapMath.sol:68 / :102): position [lo, hi] with lo = current tick rounded down to the spacing,
hi a multiple of the spacing at or below the next initialized tick above (refined-<label>.json nextUp) so the step target is hi,
L = ceil(2^256 / (sp(hi) - P)) - existing liquidity, at most maxLiquidityPerTick; cost0 = amount0 for [P, hi], cost1 = amount1 for [lo, P].
Down direction (zeroForOne, SwapMath.sol:85 / :89): position [lo, hi] with hi = next tick above, lo at or above nextDown.
Usage: python3 cost.py <label>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
label = sys.argv[1]; r = json.load(open(f'out/refined-{label}.json')); p0 = json.load(open(f'out/pools-{label}.json'))['pools']
sp = m.get_sqrt_price_at_tick; TOP = 1 << 256
def ml(ts):
    mn = -(887272 // ts) - (1 if 887272 % ts else 0); return ((1 << 128) - 1) // ((887272 // ts) - mn + 1)
out = {}
for pid, q in r['pools'].items():
    ts, t, L0 = q['tickSpacing'], q['tick'], q['liquidity']; P = p0[pid]['sqrtPriceX96']; Lmax = ml(ts)
    lo = (t // ts) * ts; maxUse = (887272 // ts) * ts; minUse = -maxUse
    best = None
    hi = lo + ts
    while hi <= min(q['nextUp'], maxUse):
        diff = sp(hi) - P
        need = -(-TOP // diff) - L0
        if diff > 0 and 0 < need <= Lmax and need < (1 << 127):
            c0 = m.amount0_delta(P, sp(hi), need, True); c1 = m.amount1_delta(sp(lo), P, need, True)
            if best is None or c0 + c1 < best['cost0'] + best['cost1']: best = {'dir': 'up', 'tickLower': lo, 'tickUpper': hi, 'L': need, 'cost0': c0, 'cost1': c1}
        hi += ts
    hiD = lo + ts; loD = lo
    while loD >= max(q['nextDown'], minUse) and hiD <= maxUse:
        diff = P - sp(loD)
        need = -(-TOP // diff) - L0 if diff > 0 else None
        if need and 0 < need <= Lmax and need < (1 << 127):
            c0 = m.amount0_delta(P, sp(hiD), need, True); c1 = m.amount1_delta(sp(loD), P, need, True)
            if best is None or c0 + c1 < best['cost0'] + best['cost1']: best = {'dir': 'down', 'tickLower': loD, 'tickUpper': hiD, 'L': need, 'cost0': c0, 'cost1': c1}
        loD -= ts
    out[pid] = {'tick': t, 'tickSpacing': ts, 'liquidity': L0, 'cheapest': best, 'currency0': q['currency0'], 'currency1': q['currency1'], 'hooks': q['hooks'],
                'log2CheapestCost': max(best['cost0'], best['cost1'], 1).bit_length() if best else None}
reach = {k: v for k, v in out.items() if v['cheapest']}
print(label, 'pools', len(out), 'reachable with one position of at most maxLiquidityPerTick', len(reach))
for k, v in sorted(reach.items(), key=lambda kv: kv[1]['log2CheapestCost'])[:12]:
    b = v['cheapest']; print(k[:18], v['tick'], v['tickSpacing'], b['dir'], b['tickLower'], b['tickUpper'], 'L 2^%d' % b['L'].bit_length(), 'cost0 2^%d cost1 2^%d' % (b['cost0'].bit_length(), b['cost1'].bit_length()), v['currency0'][:10], v['currency1'][:10], v['hooks'][:10])
json.dump({'label': label, 'pools': out, 'reachable': len(reach)}, open(f'out/cost-{label}.json', 'w'), indent=1, default=str)
