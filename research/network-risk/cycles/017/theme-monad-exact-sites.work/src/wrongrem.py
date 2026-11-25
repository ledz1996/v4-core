# FullMath.mulDiv (src/libraries/FullMath.sol:44-99) for a power-of-two denominator with the remainder replaced
# by an arbitrary word r: the quotient it would return, and the least r that drives it below 2^127 (the casts of
# Pool.sol) at prod1 = 1.
import random, json
M = (1 << 256) - 1
def tail(prod1, prod0, d, r):
    prod1 = (prod1 - (1 if r > prod0 else 0)) & M
    prod0 = (prod0 - r) & M
    twos = (-d & M) & d
    d //= twos; prod0 //= twos
    twos = (((0 - twos) & M) // twos + 1) & M
    prod0 |= (prod1 * twos) & M
    inv = (3 * d) ^ 2
    for _ in range(6): inv = (inv * (2 - d * inv)) & M
    return (prod0 * inv) & M
rnd = random.Random(1); out = {}
for k in (96, 128):
    N = 1 << k; worst = None; n = 0
    for _ in range(200000):
        prod0 = rnd.choice([0, 1, N - 1, N, N + 1, rnd.getrandbits(k), rnd.getrandbits(256)])
        r = rnd.choice([0, 1, N - 1, rnd.getrandbits(k), prod0 % N, (prod0 % N) + 1 if prod0 % N + 1 < N else 0])
        q = tail(1, prod0, N, r); n += 1
        worst = q if worst is None or q < worst else worst
    true_min = 1 << (256 - k)
    # least wrong remainder that gives a quotient below 2^127 at prod1 = 1, prod0 = 0
    thr = (1 << 256) - (1 << (127 + k))
    out[str(k)] = {'cases': n, 'lowestQuotientWithRemainderBelowN': worst, 'is2pow(256-k)-1': worst == true_min - 1,
                   'trueQuotientAtLeast': '2^%d' % (256 - k),
                   'leastRemainderForQuotientBelow2^127_prod0_0': hex(thr + 1), 'checkAtThreshold': tail(1, 0, N, thr + 1) < (1 << 127), 'checkBelow': tail(1, 0, N, thr) < (1 << 127)}
print(json.dumps(out, indent=1)); json.dump(out, open('out/wrongrem.json', 'w'), indent=1)
