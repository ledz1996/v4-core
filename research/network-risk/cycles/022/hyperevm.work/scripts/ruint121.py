"""Vectors aimed at the arithmetic paths that ruint 1.21.x rewrote (mul_mod, add_mod, div_rem with
power-of-two, one- and two-limb divisors, numerators one limb longer than the divisor, single-limb
quotients, pow with power-of-two bases, cmp) and at the FullMath constant-modulus remainder shapes.
Reuses the dispatcher and reference of tools/opdiff/battery.py. Read-only eth_call with state override.
Usage: python3 ruint121.py <out.json> <rpc> [<rpc> ...]"""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery
from evm import MASK
R = random.Random(17999)
L = 1 << 64
def rl(n):  # random value with exactly n limbs (top limb nonzero)
    if n == 0: return 0
    return (R.getrandbits(64 * (n - 1))) | ((R.getrandbits(64) | 1 << R.randrange(64)) << (64 * (n - 1)))
V = []
# 1. DIV/MOD/SDIV/SMOD with power-of-two divisors and their neighbours
for k in range(256):
    for d in ((1 << k), (1 << k) - 1 if k else 1, (1 << k) + 1):
        d &= MASK
        for a in (MASK, MASK - 1, (1 << 255), rl(4), rl(3), rl(2), rl(1), (1 << k) * 3 & MASK, d - 1 if d else 0):
            for op in ('DIV', 'MOD', 'SDIV', 'SMOD', 'DIVUP'):
                V.append((op, a & MASK, d, 0))
# 2. divisor of n limbs, numerator of n+1 limbs, single-limb quotients, remainders at d-1 and 0
for n in (1, 2, 3):
    for _ in range(600):
        d = rl(n)
        q = R.choice([R.getrandbits(64), L - 1, 1, 2, R.getrandbits(R.randrange(1, 65))])
        r = R.choice([0, d - 1, R.randrange(d), 1])
        a = q * d + r
        if a > MASK: continue
        for op in ('DIV', 'MOD', 'DIVUP'):
            V.append((op, a, d, 0))
        a2 = rl(n + 1)
        for op in ('DIV', 'MOD'):
            V.append((op, a2, d, 0))
    # top limb of numerator equal to top limb of divisor
    for _ in range(300):
        d = rl(n); top = d >> (64 * (n - 1))
        a = (top << (64 * n)) | R.getrandbits(64 * n)
        if n < 4 and a <= MASK:
            V += [('DIV', a, d, 0), ('MOD', a, d, 0)]
# 3. ADDMOD with operands below twice the modulus, including sums that pass 2^256
for _ in range(2000):
    m = R.choice([rl(4), MASK, MASK - R.getrandbits(8), (1 << 255) + R.getrandbits(64), rl(R.randrange(1, 5))])
    a = R.randrange(min(2 * m, MASK + 1)); b = R.randrange(min(2 * m, MASK + 1))
    V.append(('ADDMOD', a, b, m))
for m in (MASK, MASK - 1, 1 << 255, (1 << 255) + 1):
    for a in (MASK, MASK - 1, m - 1, m, m + 1 & MASK):
        for b in (MASK, 1, m - 1, m):
            V.append(('ADDMOD', a & MASK, b & MASK, m))
# 4. MULMOD: modulus 2^256-1 with high-limb operands; product high word whose top limbs equal the modulus's (ruint #681 shape)
for _ in range(1500):
    a = MASK - R.getrandbits(R.choice((1, 8, 64, 128, 192))); b = MASK - R.getrandbits(R.choice((1, 8, 64, 128, 192)))
    V.append(('MULMOD', a, b, MASK)); V.append(('MULDIV512', a, b, MASK))
for _ in range(3000):
    m = rl(4) | (1 << 255) if R.random() < 0.5 else rl(4)
    tops = m >> 64
    low = R.randrange(m & (L - 1)) if (m & (L - 1)) else 0
    H = (tops << 64) | low
    if H >= m: continue
    a = MASK - R.getrandbits(R.choice((0, 1, 16, 64)))
    target = H << 256 | R.getrandbits(256)
    b = target // a
    if b > MASK: continue
    V.append(('MULMOD', a, b, m)); V.append(('MULDIV512', a, b, m))
    # product just below m*2^256
    b2 = (m << 256) // a
    if b2 <= MASK: V.append(('MULMOD', a, b2, m)); V.append(('MULDIV512', a, b2, m))
# 5. FullMath constant moduli 2^96 and 2^128: prod1 = 1 with prod0 at the edges, and prod1 at its largest
for den in (1 << 96, 1 << 128):
    for p0 in (0, 1, (1 << 96) - 1, 1 << 96, (1 << 128) - 1, 1 << 128, den - 1, den + 1, MASK, MASK - 1):
        P = (1 << 256) | p0
        for a in (1 << 128, (1 << 160) - 1, (1 << 255), 3, 1 << 1, 1 << 200):
            if P % a == 0 and P // a <= MASK:
                V.append(('MULMOD', a, P // a, den)); V.append(('MULDIV512', a, P // a, den))
    for _ in range(400):
        a = R.getrandbits(256) | 1 << 255; b = R.randrange(1 << 256)
        if (a * b) >> 256 < den:
            V.append(('MULMOD', a, b, den)); V.append(('MULDIV512', a, b, den))
        a = R.getrandbits(R.randrange(129, 257)); b = (den << 256) // max(a, 1) - R.getrandbits(4)
        if 0 <= b <= MASK: V.append(('MULMOD', a, b, den)); V.append(('MULDIV512', a, b, den))
# 6. EXP with power-of-two bases and long exponents
for k in range(0, 256, 1):
    for e in (0, 1, 2, 3, 255 // max(k, 1), 256 // max(k, 1), 256 // max(k, 1) + 1, 64, 255, 256, 1 << 64, MASK):
        V.append(('EXP', 1 << k, e & MASK, 0))
# 7. comparisons where only one limb differs
for _ in range(1500):
    a = R.getrandbits(256); i = R.randrange(4); b = a ^ (R.getrandbits(64) << (64 * i))
    for op in ('LT', 'GT', 'SLT', 'SGT', 'EQ'):
        V.append((op, a, b, 0))
print(len(V), 'vectors', flush=True)
code = battery.dispatcher()
out = {'vectors': len(V), 'results': []}
for url in sys.argv[2:]:
    done, bad, errors = battery.run(url, code, V, size=400)
    print(url, 'ran', done, 'mismatches', len(bad), 'errors', len(errors), errors[:3], flush=True)
    out['results'].append({'rpc': url, 'ran': done, 'mismatches': bad[:200], 'mismatchCount': len(bad), 'errors': errors})
per = {}
for t in V: per[t[0]] = per.get(t[0], 0) + 1
out['perOp'] = per
json.dump(out, open(sys.argv[1], 'w'), indent=1)
