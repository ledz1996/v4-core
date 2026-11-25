"""Builds the division and modular vectors for the ruint harness.
Sources: battery.vectors() and targeted.vectors() of tools/opdiff (fixed seeds), filtered to
DIV MOD SDIV SMOD ADDMOD MULMOD DIVUP MULDIV512, plus an extra set aimed at the normalisation
step in front of reciprocal_mg10 and reciprocal_2_mg10: divisors of every bit length 1..256 (so every
leading-zero shift of every limb count), numerators of every limb count, and FullMath shaped inputs.
Usage: python3 -I vectors.py <out.bin> <meta.json>"""
import sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../tools/opdiff'))
import battery, targeted
MASK = (1 << 256) - 1
CODE = {'DIV': 0, 'MOD': 1, 'SDIV': 2, 'SMOD': 3, 'ADDMOD': 4, 'MULMOD': 5, 'MULDIV512': 6, 'DIVUP': 7}
def extra(seed=17017):
    rnd = random.Random(seed); V = []
    for bits in range(1, 257):
        for _ in range(60):
            d = rnd.getrandbits(bits) | (1 << (bits - 1))
            if rnd.random() < 0.2: d = (1 << bits) - 1
            if rnd.random() < 0.1: d = 1 << (bits - 1)
            for nb in (bits, bits + 1, min(256, bits + 63), min(256, bits + 64), min(256, bits + 65), 256, rnd.randint(bits, 256)):
                n = rnd.getrandbits(nb) | (1 << (nb - 1))
                for x in (n, d * rnd.getrandbits(max(1, 256 - bits)) & MASK, d, d - 1 if d > 1 else 1):
                    for op in ('DIV', 'MOD', 'SDIV', 'SMOD', 'DIVUP'):
                        V.append((op, x & MASK, d, 0))
                    V.append(('SDIV', x & MASK, (-d) & MASK, 0)); V.append(('SMOD', (-x) & MASK, d, 0))
            # 512 bit numerators (MULMOD) and 257 bit numerators (ADDMOD) against the same divisor
            for _ in range(6):
                a = rnd.getrandbits(256); b = rnd.getrandbits(rnd.choice((1, 64, 128, 192, 256)))
                V.append(('MULMOD', a, b, d)); V.append(('MULDIV512', a, b, d))
                V.append(('ADDMOD', a, MASK - rnd.getrandbits(rnd.choice((1, 64, 200))), d))
                V.append(('ADDMOD', a, b, d))
    # FullMath shaped: denominators 2^96, 2^128, Q96 sqrt prices, liquidity values, fee pips
    Q96, Q128 = 1 << 96, 1 << 128
    dens = [Q96, Q128, 10**6, 10**6 - 1, 4295128739, 1461446703485210103287273052203988822378723970342]
    for _ in range(20000):
        den = rnd.choice(dens + [rnd.getrandbits(rnd.choice((128, 160, 192, 255, 256))) | 1])
        a = rnd.getrandbits(rnd.choice((128, 160, 192, 255, 256))); b = rnd.getrandbits(rnd.choice((24, 96, 128, 160, 256)))
        V.append(('MULDIV512', a, b, den)); V.append(('MULMOD', a, b, den)); V.append(('MULMOD', a, b, MASK))
        V.append(('DIVUP', (a * b) & MASK, den, 0)); V.append(('DIV', (a << 96) & MASK, den, 0))
    return V
V = [t for t in battery.vectors() + targeted.vectors() if t[0] in CODE]
nb = len(V); X = extra(); V += X
per = {}
with open(sys.argv[1], 'wb') as f:
    for op, a, b, c in V:
        per[op] = per.get(op, 0) + 1
        f.write(bytes([CODE[op]]) + (a & MASK).to_bytes(32, 'big') + (b & MASK).to_bytes(32, 'big') + (c & MASK).to_bytes(32, 'big'))
json.dump({'fromBatteryTargeted': nb, 'extra': len(X), 'total': len(V), 'perOp': per}, open(sys.argv[2], 'w'), indent=1)
print(nb, len(X), len(V), per)
