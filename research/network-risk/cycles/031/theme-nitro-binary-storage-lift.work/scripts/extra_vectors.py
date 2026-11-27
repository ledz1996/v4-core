"""Aimed vectors for the uint256 branches the cycle 30 mix left unreached (seed 31_1210_01). usage: python3 -I extra_vectors.py <out.json>"""
import json, random, sys
rnd = random.Random(31_1210_01)
M = (1 << 256) - 1
def neg(x): return (-x) & M
V = []
def limbs(k, top_norm=None):
    if k == 0: return 0
    x = rnd.getrandbits(64 * k) | (1 << (64 * k - 1 - (0 if top_norm else rnd.randrange(64))))
    return x & ((1 << (64 * k)) - 1)
# EXP with exponent bit lengths 1..256, all limb positions, base shapes
for bl in range(1, 257):
    for _ in range(3):
        e = rnd.getrandbits(bl) | (1 << (bl - 1))
        b = rnd.choice([2, 3, M, 1 << 128, rnd.getrandbits(256), rnd.getrandbits(64), 0, 1])
        V.append(('EXP', b, e, 0))
# DIV / MOD / SDIV / SMOD over limb counts of numerator and divisor, both signs, normalized and not
for kx in range(0, 5):
    for ky in range(1, 5):
        for _ in range(40):
            x = limbs(kx, rnd.random() < 0.3); y = limbs(ky, rnd.random() < 0.3)
            for a, b in ((x, y), (y, y), (x, x | 1), (y - 1 if y else 0, y)):
                for op in ('DIV', 'MOD'):
                    V.append((op, a, b, 0))
                for sa, sb in ((a, b), (neg(a), b), (a, neg(b)), (neg(a), neg(b))):
                    V.append(('SDIV', sa, sb, 0)); V.append(('SMOD', sa, sb, 0))
for a in (0, 1, M, 1 << 255, (1 << 255) - 1, neg(5), 5):
    for b in (0, 1, M, 1 << 255, (1 << 255) - 1, neg(5), 5, 2):
        for op in ('DIV', 'MOD', 'SDIV', 'SMOD', 'EXP', 'SAR'):
            V.append((op, a, b, 0))
# ADDMOD / MULMOD with modulus of each limb count, operands above and below the modulus
for km in range(1, 5):
    for _ in range(150):
        m = limbs(km, rnd.random() < 0.3)
        a, b = rnd.getrandbits(256), rnd.choice([rnd.getrandbits(256), rnd.getrandbits(64 * km), m - 1, m, m + 1 & M])
        V.append(('MULMOD', a, b, m)); V.append(('ADDMOD', a, b, m)); V.append(('MULMOD', a % m, b % m, m))
# SAR across shift counts with negative and positive values
for s in list(range(0, 260)) + [M, 1 << 64]:
    V.append(('SAR', s, neg(rnd.getrandbits(200) + 1), 0)); V.append(('SAR', s, rnd.getrandbits(255), 0))
json.dump([[op, hex(a), hex(b), hex(c)] for op, a, b, c in V], open(sys.argv[1], 'w'))
print(len(V))
