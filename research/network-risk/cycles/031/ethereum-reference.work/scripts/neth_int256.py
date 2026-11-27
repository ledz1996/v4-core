"""Cycle 31 ethereum-reference. Line-by-line Python transcription of the Nethermind.Numerics.Int256 1.15.0 routines
that Nethermind 2.3.0-rc reaches for the PoolManager's MULMOD, DIV, MOD, SDIV and SMOD operand shapes, run against
Python integers. Sources: dl/i256-1.15.0/UInt256.divmod.cs, UInt256.barrett.cs, Int256.cs, UInt256.lookups.cs and
dl/neth-2.3.0-rc/EvmInstructions.Math2Param.cs (PowerOfTwoExp). No network access. Usage: python3 neth_int256.py <out.json> [N]
Planted faults (env PLANT=1..6) must produce mismatches, which shows the harness can see a fault."""
import sys, os, json, random, re
M64 = (1 << 64) - 1; M256 = (1 << 256) - 1
PLANT = int(os.environ.get('PLANT', '0'))
HERE = os.path.dirname(os.path.abspath(__file__))
seed_src = open(os.path.join(HERE, '..', 'dl', 'i256-1.15.0', 'UInt256.lookups.cs')).read()
blk = seed_src[seed_src.index('ReciprocalSeedTable'):]
blk = blk[blk.index('['):blk.index('];')]
SEED = [int(x, 16) for x in re.findall(r'0x[0-9A-Fa-f]+', blk)]
assert len(SEED) == 256, len(SEED)

def limbs(x): return [(x >> (64 * i)) & M64 for i in range(4)]
def join(l): return sum(v << (64 * i) for i, v in enumerate(l))
def mul64(a, b):  # returns (hi, lo)
    p = a * b; return p >> 64, p & M64
def addc(a, b, c):
    s = a + b + c; return s & M64, s >> 64

def reciprocal2by1(d):
    assert d >> 63
    v0 = SEED[(d >> 55) & 0xFF]
    d40 = ((d >> 24) + 1) & M64
    v1 = ((v0 << 11) - ((v0 * v0 * d40 & M64) >> 40) - 1) & M64
    v2 = ((v1 << 13) + ((v1 * ((0x1000000000000000 - v1 * d40) & M64) & M64) >> 47)) & M64
    d0 = d & 1; d63 = (d >> 1) + d0
    e = (((v2 >> 1) & ((0 - d0) & M64)) - (v2 * d63)) & M64
    v3 = (((v2 * e) >> 64 >> 1) + (v2 << 31)) & M64
    ph, pl = mul64(v3, d)
    ph = (ph + (1 if pl > (~d & M64) else 0)) & M64
    r = (v3 - ph - d) & M64
    if PLANT == 1: r ^= 1
    return r

def urem2by1(uh, rec, d, ul, branchless=True):
    hi, low = mul64(rec, uh)
    low = (low + ul) & M64
    q = (hi + uh + 1) & M64
    if low < ul: q = (q + 1) & M64
    r1 = (ul - q * d) & M64
    if r1 > low: r1 = (r1 + d) & M64
    if PLANT == 2: return r1
    if r1 >= d: r1 = (r1 - d) & M64
    return r1

def rem128by64(hi, lo, dn, rec, shift):
    if shift == 0:
        r = urem2by1(0, rec, dn, hi); return urem2by1(r, rec, dn, lo)
    rs = 64 - shift
    un2 = hi >> rs; un1 = ((hi << shift) | (lo >> rs)) & M64; un0 = (lo << shift) & M64
    r = urem2by1(un2, rec, dn, un1); r = urem2by1(r, rec, dn, un0)
    return r >> shift

def rem_by64_recip(x, d):
    shift = 64 - d.bit_length(); dn = (d << shift) & M64; rec = reciprocal2by1(dn)
    x0, x1, x2, x3 = limbs(x)
    if shift == 0: u0, u1, u2, u3, r = x0, x1, x2, x3, 0
    else:
        cs = 64 - shift
        u0 = (x0 << shift) & M64; u1 = ((x1 << shift) | (x0 >> cs)) & M64
        u2 = ((x2 << shift) | (x1 >> cs)) & M64; u3 = ((x3 << shift) | (x2 >> cs)) & M64; r = x3 >> cs
    for u in (u3, u2, u1, u0):
        if (r | u) != 0: r = urem2by1(r, rec, dn, u)
    return r >> shift

def divrem_hw(lower, upper, d):
    assert upper < d
    n = (upper << 64) | lower; return n // d, n % d

def rem_by64_hw(x, d):
    u = limbs(x); r = u[3]
    if u[3] >= d: _, r = divrem_hw(u[3], 0, d)
    for k in (2, 1, 0):
        if r != 0 or u[k] >= d: _, r = divrem_hw(u[k], r, d)
        else: r = u[k]
    return r

def quot_by64_x86(x, d):
    u = limbs(x); rem = u[3]; q3 = 0
    if u[3] >= d: q3, rem = divrem_hw(u[3], 0, d)
    qs = [0, 0, 0]
    for idx, k in enumerate((2, 1)):
        if rem != 0 or u[k] >= d: qs[k], rem = divrem_hw(u[k], rem, d)
        else: rem = u[k]
    q0 = 0
    if rem != 0 or u[0] >= d: q0, _ = divrem_hw(u[0], rem, d)
    if PLANT == 3 and q0: q0 -= 1
    return join([q0, qs[1], qs[2], q3])

def pseudo_mersenne(lo, hi, c):
    L = limbs(lo); H = limbs(hi)
    hl = [mul64(h, c) for h in H]
    car = 0; r = [0] * 4
    for i in range(4): r[i], car = addc(L[i], hl[i][1], car)
    top = hl[3][0] + car; car = 0
    r[1], car = addc(r[1], hl[0][0], car); r[2], car = addc(r[2], hl[1][0], car); r[3], car = addc(r[3], hl[2][0], car)
    top += car
    th, tl = mul64(top, c); car = 0
    r[0], car = addc(r[0], tl, car); r[1], car = addc(r[1], th, car); r[2], car = addc(r[2], 0, car); r[3], car = addc(r[3], 0, car)
    if car and PLANT != 4:
        car = 0
        r[0], car = addc(r[0], c, car); r[1], car = addc(r[1], 0, car); r[2], car = addc(r[2], 0, car); r[3] = (r[3] + car) & M64
    car = 0; s = [0] * 4
    s[0], car = addc(r[0], c, car); s[1], car = addc(r[1], 0, car); s[2], car = addc(r[2], 0, car); s[3], car = addc(r[3], 0, car)
    return join(s) if car else join(r)

def mulmod_allones_fold(lo, hi):
    s = lo + hi; carry = s >> 256; res = s & M256
    if carry: res = (res + 1) & M256  # limb-wise increment chain; cannot overflow past 2^256 here
    if res == M256 and PLANT != 5: res = 0
    return res

def negate_limbs(x):
    x0, x1, x2, x3 = limbs(x)
    b = 1 if x0 else 0
    r1 = (0 - x1 - b) & M64; b |= 1 if x1 else 0
    r2 = (0 - x2 - b) & M64; b |= 1 if x2 else 0
    return join([(0 - x0) & M64, r1, r2, (0 - x3 - b) & M64])

def s(x): return x - (1 << 256) if x >> 255 else x
def int256_mod(x, y):  # Int256.Mod 1.15.0, then wrapped by OpSMod (y in {0,1} -> 0)
    xn, yn = x >> 255, y >> 255
    if not (xn | yn): return x % y
    dv = negate_limbs(x) if xn else x; ds = negate_limbs(y) if yn else y
    r = dv % ds
    if xn and PLANT != 6: r = negate_limbs(r)
    return r

def pow2exp(a, e):
    u = limbs(a)
    ispow = (bin(u[0] | u[1] | u[2] | u[3]).count('1') == 1) and ((u[0] & u[1]) | (u[2] & u[3]) | ((u[0] | u[1]) & (u[2] | u[3]))) == 0
    if not ispow: return None
    if e > 255: return 0
    shift = (255 - (256 - a.bit_length())) * e
    if shift > 255: return 0
    return 1 << shift

def main():
    out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    rnd = random.Random(31)
    edges = [0, 1, 2, 3, (1 << 63) - 1, 1 << 63, (1 << 63) + 1, M64 - 1, M64, 1 << 64, (1 << 64) + 1, 1 << 96, 1 << 128, (1 << 128) - 1,
             1 << 160, (1 << 160) - 1, 1 << 192, (1 << 192) - 1, (1 << 255), (1 << 255) - 1, (1 << 255) + 1, M256 - 1, M256,
             1461446703485210103287273052203988822378723970342, 4295128739, 79228162514264337593543950336, 10 ** 6, 10 ** 6 - 3000]
    def rv():
        k = rnd.random()
        if k < 0.25: return rnd.choice(edges) ^ (rnd.getrandbits(3) if rnd.random() < 0.3 else 0)
        if k < 0.5: return rnd.getrandbits(rnd.randint(1, 256))
        if k < 0.7: return (M256 >> rnd.randint(0, 255)) ^ (1 << rnd.randint(0, 255)) & M256
        return rnd.getrandbits(256)
    stats = {}; bad = []
    def chk(name, got, want, inp):
        st = stats.setdefault(name, [0, 0]); st[0] += 1
        if got != want:
            st[1] += 1
            if len(bad) < 50: bad.append({'fn': name, 'in': [hex(v) for v in inp], 'got': hex(got), 'want': hex(want)})
    d64 = [10 ** 6, 10 ** 6 - 100, 10 ** 6 - 3000, 10 ** 6 - 10000, 999999, 3, 7, (1 << 63) + 1, M64, M64 - 2, 1 << 63]
    for it in range(N):
        x = rv(); d = rnd.choice(d64) if rnd.random() < 0.3 else (rnd.getrandbits(rnd.randint(2, 64)) | 2)
        d &= M64
        if d < 2: d = 2
        chk('RemainderBy64Reciprocal', rem_by64_recip(x, d), x % d, [x, d])
        chk('RemainderBy64Hardware', rem_by64_hw(x, d), x % d, [x, d])
        if d & (d - 1): chk('QuotientBy64BitsX86Base', quot_by64_x86(x, d), x // d, [x, d])
        hi = rnd.getrandbits(64) % d; lo = rnd.getrandbits(64)
        shift = 64 - d.bit_length(); dn = (d << shift) & M64
        chk('Remainder128By64Bits', rem128by64(hi, lo, dn, reciprocal2by1(dn), shift) if shift else rem128by64(hi, lo, dn, reciprocal2by1(dn), 0), ((hi << 64) | lo) % d, [hi, lo, d])
        dd = rnd.getrandbits(63) | (1 << 63)
        v = reciprocal2by1(dd); chk('Reciprocal2By1', v, ((1 << 128) - 1) // dd - (1 << 64), [dd])
        a, b = rv(), rv(); p = a * b; lo, hi = p & M256, p >> 256
        if hi: chk('MulMod fold 2^256-1', mulmod_allones_fold(lo, hi), p % M256, [a, b])
        c = rnd.choice([1, 2, 977 + (1 << 32), rnd.getrandbits(rnd.randint(1, 63)) | 1, M64 - 1]) & M64
        if 1 <= c <= M64 - 1:
            hi2 = rv(); lo2 = rv()
            chk('Remainder512ByPseudoMersenne', pseudo_mersenne(lo2, hi2, c), ((hi2 << 256) | lo2) % ((1 << 256) - c), [lo2, hi2, c])
        y = rv()
        if y > 1:
            want = abs(s(x)) % abs(s(y)); want = (-want if s(x) < 0 else want) & M256
            chk('Int256.Mod (SMOD)', int256_mod(x, y), want, [x, y])
        chk('NegateLimbs', negate_limbs(x), (-x) & M256, [x])
        a = (1 << rnd.randint(1, 255)); e = rnd.choice([rnd.randint(0, 300), rnd.getrandbits(rnd.randint(1, 256))])
        if e: chk('PowerOfTwoExp', pow2exp(a, e), pow(a, e, 1 << 256), [a, e])
    # every limb-boundary pair for the fold and the pseudo-Mersenne edge where r equals m exactly
    for lo in edges:
        for hi in edges:
            if hi: chk('MulMod fold 2^256-1', mulmod_allones_fold(lo, hi), ((hi << 256) | lo) % M256, [lo, hi])
            for c in (1, 2, 0x1000003D1, M64 - 1):
                chk('Remainder512ByPseudoMersenne', pseudo_mersenne(lo, hi, c), ((hi << 256) | lo) % ((1 << 256) - c), [lo, hi, c])
    total = sum(v[0] for v in stats.values()); mism = sum(v[1] for v in stats.values())
    res = {'plant': PLANT, 'cases': total, 'mismatches': mism, 'perFunction': stats, 'firstMismatches': bad[:20]}
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({'plant': PLANT, 'cases': total, 'mismatches': mism, 'per': {k: v for k, v in stats.items()}}))

if __name__ == '__main__': main()
