"""Task 4: the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp (src/libraries/SqrtPriceMath.sol:40-52).

Usage: python3 task4.py <out.json> [seed]
1. Boundary per price: largest amount whose product fits, first that wraps, the window where the product fits and
   numerator1 + product wraps (line 45).
2. Search for a wrapped product that passes line 43 (product / amount == sqrtPX96). A proof that none exists is
   written in the output; the search is a check of the proof, with the seed recorded.
3. Reachability inside a swap step: for every input that reaches the fallback with amount <= 2^127 (the specified
   amount must fit int128 at Pool.sol:455-459 because the fallback consumes all of it), the step output
   L*(s - next)/2^96 is computed with Python integers. The claim checked is that it always exceeds 2^127 - 1, so
   Pool.sol:455-459 reverts, and that next is never below the exact price N/(N/s + a) nor below the step target.
"""
import sys, json, random
from fractions import Fraction as F
M = (1 << 256) - 1; Q96 = 1 << 96; MAXS = 1461446703485210103287273052203988822378723970342; MINS = 4295128739
I127 = (1 << 127) - 1
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 25025
rnd = random.Random(seed)
out = {'seed': seed}


def ceil_div(a, b): return -(-a // b)


def fallback_next(s, L, a):
    N = L << 96
    return ceil_div(N, N // s + a)


def path(s, L, a):
    N = L << 96; prod = (a * s) & M
    if prod // a == s:
        if (N + prod) & M >= N: return 'precise'
        return 'line45'
    return 'line43'


# 1. boundaries
rows = []
for name, s in [('2^129', 1 << 129), ('2^130', 1 << 130), ('2^150', 1 << 150), ('2^158', 1 << 158), ('2^159', 1 << 159),
                ('MAX-1', MAXS - 1)]:
    amax = M // s
    r = {'price': name, 'largestFittingAmount': amax, 'firstWrappingAmount': amax + 1,
         'pathAt': {str(a): path(s, 1 << 100, a) for a in (amax, amax + 1)}}
    for Ln, L in [('2^64', 1 << 64), ('2^100', 1 << 100), ('2^128-1', (1 << 128) - 1)]:
        N = L << 96
        lo45 = ceil_div((1 << 256) - N, s)
        r['line45Window_L=' + Ln] = [lo45, amax] if lo45 <= amax else None
        if lo45 <= amax:
            assert path(s, L, lo45) == 'line45' and path(s, L, lo45 - 1) == 'precise' and path(s, L, amax) == 'line45'
    rows.append(r)
out['boundaries'] = rows

# 2. wrapped product passing line 43: proof and search
out['proof43'] = ('Let a >= 1 and s < 2^160 with a*s >= 2^256. The EVM product is p = a*s - k*2^256 with k >= 1, so '
                  'p <= a*s - 2^256 < a*s and floor(p/a) <= (a*s - 2^256)/a < s. The test product / amount == sqrtPX96 '
                  'is therefore false for every wrapped product.')
bad = 0; n = 0
for _ in range(300000):
    s = rnd.randrange(MINS, MAXS)
    lo = M // s + 1
    a = rnd.choice([lo, lo + 1, rnd.randrange(lo, lo * 2 + 2), rnd.randrange(lo, 1 << 255), (1 << 256) - 1 - rnd.randrange(1000)])
    p = (a * s) & M; n += 1
    if p // a == s: bad += 1
for s in [MINS, MINS + 1, MAXS - 1, (1 << 159), (1 << 160) - 1]:
    for a in [M // s + 1, M // s + 2, 1 << 255, M]:
        p = (a * s) & M; n += 1
        if p // a == s: bad += 1
out['search43'] = {'cases': n, 'wrappedPassingLine43': bad}

# 3. reachability inside a swap step
viol = []; stats = {'precise': 0, 'line45': 0, 'line43': 0}; minout = None; cnt = 0
for _ in range(200000):
    # step start price above 2^129 is forced by a <= 2^127 (shown below); sample it on the whole range anyway
    s = rnd.randrange(1 << 96, MAXS)
    L = rnd.choice([rnd.randrange(1, 1 << 128), (1 << 128) - 1, 1 << rnd.randrange(1, 128)])
    N = L << 96
    a = rnd.choice([ceil_div((1 << 256) - N, s), M // s + 1, rnd.randrange(max(1, ceil_div((1 << 256) - N, s)), I127 + 2)])
    if a < 1 or a > I127: continue
    pth = path(s, L, a)
    if pth == 'precise': continue
    # the step target: price s_t at or above 2^96 (tick 0 starts bitmap word 0; a step from a positive tick stays in it)
    st = rnd.choice([Q96, rnd.randrange(Q96, s), s - 1])
    amt_to_target = ceil_div(ceil_div(N * (s - st), s), st)   # getAmount0Delta(st, s, L, roundUp) as exact ceiling
    if a >= amt_to_target: continue      # the step reaches its target and never calls the function
    cnt += 1; stats[pth] += 1
    nxt = fallback_next(s, L, a)
    exact = F(N * s, N + a * s)
    o = L * (s - nxt) // Q96
    if nxt < exact: viol.append({'s': s, 'L': L, 'a': a, 'why': 'next below exact'})
    if nxt < st: viol.append({'s': s, 'L': L, 'a': a, 'why': 'next below target'})
    if o <= I127: viol.append({'s': s, 'L': L, 'a': a, 'out': o, 'why': 'output fits int128'})
    minout = o if minout is None else min(minout, o)
out['reach'] = {'samples': cnt, 'paths': stats, 'violations': viol[:50], 'violationCount': len(viol),
                'minOutputBits': minout.bit_length() if minout else None}
out['bounds'] = ('With a <= 2^127 and a*s >= 2^256 - L*2^96 >= 2^256 - 2^224, s > 2^128.99, so the step starts at a '
                 'positive tick; nextInitializedTickWithinOneWord never returns a tick below the start of the word that '
                 'holds tick 0, so the target s_t >= 2^96. a < amount to target gives L > (2^160 - 2^65)*s_t/s, and '
                 'the step output is at least about 2^64*s_t >= 2^160, so amountCalculated.toInt128 at Pool.sol:455-459 '
                 'reverts. The pool would also have to hold more than 2^160 units of currency1 in that range.')
# the smallest s for which a <= 2^127 can reach the fallback
out['minStartPrice'] = {'value': ceil_div((1 << 256) - ((1 << 128) - 1) * Q96, I127), 'bits': ceil_div((1 << 256) - ((1 << 128) - 1) * Q96, I127).bit_length()}
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=str)
print(json.dumps({k: out[k] for k in ('search43', 'reach', 'minStartPrice')}, default=str)[:1500])
