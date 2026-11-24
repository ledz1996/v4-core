"""Vectors aimed at known weak spots of big integer libraries, run through the same
dispatcher as battery.py.

1. ruint 1.21.0 (2026-10-20, yanked) skipped the top quotient limb of the mul_mod
   reduction when the top two limbs of the normalised product were <= the top two
   limbs of the normalised modulus. Equality gives a wrong remainder (#681, fixed in
   1.21.1). The vectors below make the top 128 bits equal, for moduli of 2, 3 and 4
   limbs and every normalisation shift, with and without reduced operands.
2. A modulus of 2^256-1 has its own fast path in several libraries (end-around carry).
   FullMath.mulDiv uses that modulus on every call. The vectors make high + low equal
   2^256-1, 2^256 and 2^256+1, and products that are exact multiples of the modulus.
3. Shifts at limb boundaries with every sign pattern, for SAR, SHL and SHR.

Usage: python3 targeted.py <out.json> [chainId ...]
"""
import sys, json, random, hashlib, concurrent.futures as cf
from evm import *
from battery import dispatcher, run


def vectors(seed=681):
    rnd = random.Random(seed); V = []
    # 1. equal top limbs after normalisation
    for n in (2, 3, 4):
        for shift in list(range(0, 64)):
            for rep in range(6):
                bits = 64 * n - shift
                mod = rnd.getrandbits(bits) | (1 << (bits - 1))
                if rep == 1: mod |= (1 << (bits - 64)) - 1 if bits > 64 else 0  # low limbs all ones
                if rep == 2: mod &= ~((1 << (64 * (n - 2))) - 1) | 1  # low limbs nearly zero
                if rep == 3: mod = (1 << bits) - 1 - rnd.getrandbits(8)
                mnorm = mod << shift
                top = mnorm >> (64 * (n - 2))  # 128 bits
                lo, hi = -(-(top << 384) >> shift), (((top + 1) << 384) - 1) >> shift
                for where in ('low', 'mid', 'high', 'rand'):
                    target = {'low': lo + rnd.getrandbits(40), 'high': hi - rnd.getrandbits(40), 'mid': (lo + hi) // 2,
                              'rand': rnd.randrange(lo, hi + 1)}[where]
                    if target >> 512: continue
                    a = rnd.getrandbits(256) | (1 << 255) if rnd.random() < 0.5 else MASK - rnd.getrandbits(rnd.choice((8, 64, 120)))
                    b = target // a
                    for bb in (b, b + 1):
                        if bb > MASK or bb == 0: continue
                        if lo <= a * bb <= hi: V.append(('MULMOD', a, bb, mod)); V.append(('MULDIV512', a, bb, mod))
                # reduced operands (a, b < mod) where that is possible
                if n == 4:
                    for _ in range(4):
                        a = mod - 1 - rnd.getrandbits(rnd.choice((1, 20, 64, 100)))
                        if a <= 0: continue
                        b0 = lo // a
                        for bb in (b0, b0 + 1, mod - 1, mod - 2):
                            if 0 < bb < mod: V.append(('MULMOD', a, bb, mod))
    # 2. modulus 2^256 - 1
    f1, f2 = (1 << 128) - 1, (1 << 128) + 1
    for _ in range(1500):
        k = rnd.getrandbits(rnd.choice((1, 8, 64, 127))) or 1; j = rnd.getrandbits(rnd.choice((1, 8, 64, 127))) or 1
        a, b = (k * f1) & MASK, (j * f2) & MASK
        if k * f1 <= MASK and j * f2 <= MASK:
            for da, db in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                V.append(('MULMOD', (a + da) & MASK, (b + db) & MASK, MASK)); V.append(('MULDIV512', (a + da) & MASK, (b + db) & MASK, MASK - rnd.getrandbits(4)))
    for _ in range(1500):
        a = rnd.getrandbits(256) | 1
        for r in (0, 1, 2, MASK - 1, MASK - 2):
            try:
                b = (r * pow(a, -1, MASK)) % MASK
            except ValueError:
                continue
            V.append(('MULMOD', a, b, MASK)); V.append(('MULDIV512', a, b, rnd.getrandbits(256) | (1 << 255)))
        V.append(('MULMOD', MASK, a, MASK)); V.append(('MULMOD', a, MASK, MASK)); V.append(('ADDMOD', a, MASK - a, MASK)); V.append(('ADDMOD', a, (MASK - a + 1) & MASK, MASK))
    # ADDMOD around overflow and around operands above the modulus
    for _ in range(3000):
        c = rnd.choice([rnd.getrandbits(256) | (1 << 255), rnd.getrandbits(rnd.choice((64, 65, 128, 129, 192, 193))) | 1, MASK - rnd.getrandbits(64)])
        a = rnd.choice([c - 1, c, (c + 1) & MASK, (2 * c) & MASK, (2 * c - 1) & MASK, MASK, rnd.getrandbits(256)])
        b = rnd.choice([c - 1, c, (c + 1) & MASK, MASK - a, (MASK - a + 1) & MASK, MASK, rnd.getrandbits(256), (c - a) % c if c else 0])
        V.append(('ADDMOD', a & MASK, b & MASK, c))
    # DIV / MOD fast paths
    for _ in range(4000):
        d = rnd.choice([1 << rnd.randrange(0, 256), (1 << rnd.randrange(1, 256)) - 1, (1 << rnd.randrange(1, 256)) + 1, rnd.getrandbits(rnd.choice((1, 63, 64, 65, 127, 128, 129, 191, 192, 193, 256))) or 1])
        nmr = rnd.choice([d - 1, d, (d + 1) & MASK, MASK, rnd.getrandbits(256), (d * rnd.getrandbits(40)) & MASK, rnd.getrandbits(rnd.choice((64, 128, 192)))])
        for op in ('DIV', 'MOD', 'SDIV', 'SMOD', 'DIVUP'):
            V.append((op, nmr & MASK, d & MASK, 0))
    # 3. shifts at limb boundaries
    shifts = [0, 1, 7, 8, 31, 32, 33, 62, 63, 64, 65, 66, 95, 96, 97, 126, 127, 128, 129, 130, 159, 160, 161, 190, 191, 192, 193, 194, 223, 224, 254, 255, 256, 257, 300, 1 << 8, 1 << 16, 1 << 32, 1 << 64, 1 << 128, MASK]
    vals = [rnd.getrandbits(256) for _ in range(40)] + [rnd.getrandbits(256) | SIGN for _ in range(40)] + [MASK, SIGN, SIGN - 1, 1, 0, SIGN | 1, MASK << 64 & MASK, MASK >> 64, MASK << 128 & MASK, MASK >> 128, MASK << 192 & MASK, MASK >> 192]
    for sh in shifts:
        for v in vals:
            for op in ('SAR', 'SHL', 'SHR'): V.append((op, sh, v, 0))
    for _ in range(3000):
        V.append(('MUL', rnd.getrandbits(rnd.choice((64, 128, 192, 256))), rnd.getrandbits(rnd.choice((64, 128, 192, 256))), 0))
        V.append(('MULDIV512', rnd.getrandbits(rnd.choice((128, 192, 256))), rnd.getrandbits(rnd.choice((128, 192, 256))), rnd.getrandbits(256) | 1))
    return V


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = dispatcher(); V = vectors()
    per = {}
    for t in V: per[t[0]] = per.get(t[0], 0) + 1
    print(len(V), 'vectors', per)
    nets = [n for n in networks() if not only or n[0] in only]

    def work(n):
        cid, name, url = n
        done, bad, errors = run(url, code, V)
        if errors and done < len(V):
            retry = [t for i, _ in errors for t in V[i:i + 600]]
            d2, b2, e2 = run(url, code, retry, size=150); done += d2; bad += b2; errors = e2
        return {'chainId': cid, 'name': name, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:10]}

    res = []
    with cf.ThreadPoolExecutor(8) as ex:
        for r in ex.map(work, nets):
            print(f"{r['chainId']:>8} {r['name']:16} ran {r['ran']}/{r['vectors']} mismatches {r['mismatchCount']} errors {len(r['errors'])}", flush=True); res.append(r)
    json.dump({'vectors': len(V), 'perOp': per, 'results': res}, open(out, 'w'), indent=1)
