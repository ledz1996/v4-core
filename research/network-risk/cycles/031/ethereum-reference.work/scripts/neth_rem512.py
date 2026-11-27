"""Cycle 31 ethereum-reference. Line-by-line Python transcription of Remainder512By256Bits from
Nethermind.Numerics.Int256 1.15.0 (dl/i256-1.15.0/UInt256.divmod.cs), with its helpers EstimateQhat, UDivRem2By1,
Reciprocal2By1 (from neth_int256.py), SubMulTo4 and AddTo4, in both the x86 DivRem arm and the reciprocal arm. It is
the remainder routine MULMOD reaches in Nethermind 2.3.0-rc for a 4-limb modulus with a nonzero high half of the
product, for example FullMath.mulDivRoundingUp at src/libraries/FullMath.sol:112 called from
src/libraries/SqrtPriceMath.sol:47 with a denominator near 2^256. 1.15.0 added one test that drops the leading
quotient digit when the top limb of the dividend is below the divisor's top limb; NOSKIP=1 runs without it.
PLANT512=1 turns the strict test into <= (the shape of the ruint 1.21.0 fault). Usage: python3 neth_rem512.py <out.json> [N]"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neth_int256 as ni
M64 = ni.M64; PLANT = int(os.environ.get('PLANT512', '0')); NOSKIP = os.environ.get('NOSKIP') == '1'

def udivrem2by1(uh, rec, d, ul):
    hi, low = ni.mul64(rec, uh); low = (low + ul) & M64
    q = (hi + uh + 1) & M64
    if low < ul: q = (q + 1) & M64
    r1 = (ul - q * d) & M64
    if r1 > low: q = (q - 1) & M64; r1 = (r1 + d) & M64
    if r1 >= d: q = (q + 1) & M64; r1 = (r1 - d) & M64
    return q, r1

def divrem(lo, hi, d, x86, rec):
    if x86: n = (hi << 64) | lo; return n // d, n % d
    return udivrem2by1(hi, rec, d, lo)

def estimate_qhat(u2, u1, u0, dh, dl, rec, x86):
    if u2 > dh: return M64
    if u2 == dh:
        qhat = M64; rhat = (u1 + dh) & M64
        if rhat < u1: return qhat
    else:
        qhat, rhat = divrem(u1, u2, dh, x86, rec)
    while True:
        ph, pl = ni.mul64(qhat, dl)
        if ph < rhat or (ph == rhat and pl <= u0): break
        qhat = (qhat - 1) & M64; prev = rhat; rhat = (rhat + dh) & M64
        if rhat < prev: break
    return qhat

def submul4(un, j, y, mul):
    borrow = 0
    for k in range(4):
        v = un[j + k]; h, l = ni.mul64(y[k], mul)
        if k == 0:
            un[j] = (v - l) & M64; borrow = h + (1 if l > v else 0)
        else:
            t = (v - borrow) & M64; un[j + k] = (t - l) & M64
            borrow = h + (1 if borrow > v else 0) + (1 if l > t else 0)
    return borrow & M64

def addto4(un, j, y):
    c = 0
    for k in range(4):
        t = (un[j + k] + y[k]) & M64; s = (t + c) & M64
        c = (1 if t < un[j + k] else 0) | (1 if s < c else 0); un[j + k] = s
    return c

def rem512by256(lo, hi, d, x86=True):
    L = ni.limbs(lo); H = ni.limbs(hi); D = ni.limbs(d)
    assert D[3] != 0 and hi != 0
    d0, d1, d2, d3 = D
    shift = 64 - d3.bit_length()
    u4, u5, u6, u7 = H
    uLen = 8 if u7 else (7 if u6 else (6 if u5 else 5))
    if shift == 0:
        un = L + H + [0]
        if not NOSKIP and un[uLen - 1] < d3: uLen -= 1
        nd = [d0, d1, d2, d3]
    else:
        rs = 64 - shift; u0, u1n, u2n, u3n = L
        un = [0] * 9
        un[8] = u7 >> rs; un[7] = ((u7 << shift) | (u6 >> rs)) & M64; un[6] = ((u6 << shift) | (u5 >> rs)) & M64
        un[5] = ((u5 << shift) | (u4 >> rs)) & M64; un[4] = ((u4 << shift) | (u3n >> rs)) & M64
        un[3] = ((u3n << shift) | (u2n >> rs)) & M64; un[2] = ((u2n << shift) | (u1n >> rs)) & M64
        un[1] = ((u1n << shift) | (u0 >> rs)) & M64; un[0] = (u0 << shift) & M64
        nd = [(d0 << shift) & M64, ((d1 << shift) | (d0 >> rs)) & M64, ((d2 << shift) | (d1 >> rs)) & M64, ((d3 << shift) | (d2 >> rs)) & M64]
        top = u6 if u6 else (u5 if u5 else u4)
        cmp = (lambda a, b: a <= b) if PLANT == 1 else (lambda a, b: a < b)
        if not NOSKIP and (cmp(u7, d3) and (u7 != 0 or cmp(top, d3))): uLen -= 1
    nd0, nd1, nd2, nd3 = nd
    m = uLen - 4
    rec = 0 if x86 else ni.reciprocal2by1(nd3)
    for j in range(m, -1, -1):
        u8, u9, u10 = un[j + 4], un[j + 3], un[j + 2]
        full = False
        if u8 >= nd3:
            qhat = estimate_qhat(u8, u9, u10, nd3, nd2, rec, x86); full = True
        else:
            qhat, rhat = divrem(u9, u8, nd3, x86, rec)
            ph, pl = ni.mul64(qhat, nd2)
            while ph > rhat or (ph == rhat and pl > u10):
                qhat = (qhat - 1) & M64; prev = rhat; rhat = (rhat + nd3) & M64
                if rhat < prev: full = True; break
                ph = (ph - (1 if pl < nd2 else 0)) & M64; pl = (pl - nd2) & M64
            if not full:
                v0 = un[j]; hi0, lo0 = ni.mul64(nd0, qhat); un[j] = (v0 - lo0) & M64; b2 = hi0 + (1 if lo0 > v0 else 0)
                v1 = un[j + 1]; hi1, lo1 = ni.mul64(nd1, qhat); t1 = (v1 - b2) & M64; un[j + 1] = (t1 - lo1) & M64
                b2 = hi1 + (1 if b2 > v1 else 0) + (1 if lo1 > t1 else 0)
                v2 = un[j + 2]; hi2, lo2 = ni.mul64(nd2, qhat); t2 = (v2 - b2) & M64; un[j + 2] = (t2 - lo2) & M64
                b2 = hi2 + (1 if b2 > v2 else 0) + (1 if lo2 > t2 else 0)
                un[j + 3] = (rhat - b2) & M64
                if b2 > rhat: addto4(un, j, nd)
                continue
        borrow = submul4(un, j, nd, qhat)
        if u8 < borrow: addto4(un, j, nd)
    rw = un[0:4]
    if shift == 0: return ni.join(rw)
    rs = 64 - shift
    return ni.join([((rw[0] >> shift) | (rw[1] << rs)) & M64, ((rw[1] >> shift) | (rw[2] << rs)) & M64, ((rw[2] >> shift) | (rw[3] << rs)) & M64, rw[3] >> shift])

def main():
    out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    rnd = random.Random(3131); st = {'cases': 0, 'mismatch': 0, 'skipTaken': 0, 'byShape': {}}; bad = []
    def shape_case():
        k = rnd.randrange(6)
        if k == 0:  # FullMath at SqrtPriceMath.sol:44-47: numerator1 = liquidity << 96, sqrtP, denominator = numerator1 + amount*sqrtP
            liq = rnd.getrandbits(rnd.randint(1, 128)) or 1; sp = rnd.randint(4295128739, 1461446703485210103287273052203988822378723970342)
            n1 = liq << 96; amt = rnd.getrandbits(rnd.randint(1, 256)); prod = (amt * sp) & ((1 << 256) - 1)
            den = (n1 + prod) & ((1 << 256) - 1)
            return n1 * sp, den, 'sqrtPriceMath47'
        d = rnd.getrandbits(256) | (1 << 192)
        d3 = d >> 192
        if k == 1:  # top limb of dividend equal to, one below or one above the divisor top limb
            T = max(1, d3 + rnd.choice([-1, 0, 1])) & M64; pos = rnd.randint(4, 7)
            n = (T << (64 * pos)) | rnd.getrandbits(64 * pos); return n, d, 'topLimbEdge'
        if k == 2:  # products of reduced operands
            a = rnd.getrandbits(256) % d; b = rnd.getrandbits(256) % d; return a * b, d, 'reduced'
        if k == 3:  # all-ones-ish divisor shapes and shift 0
            d = ((1 << 256) - 1) ^ rnd.getrandbits(rnd.randint(1, 255)); return rnd.getrandbits(512), d, 'topHeavyDivisor'
        if k == 4:
            sh = rnd.randint(0, 63); d = ((rnd.getrandbits(64) | (1 << 63)) >> sh) << 192 | rnd.getrandbits(192)
            return rnd.getrandbits(rnd.randint(257, 512)), d, 'randomShift'
        return rnd.getrandbits(512), d, 'random'
    for i in range(N):
        n, d, shp = shape_case()
        lo, hi = n & ((1 << 256) - 1), n >> 256
        if hi == 0 or (d >> 192) == 0: continue
        want = n % d
        for x86 in (True, False):
            got = rem512by256(lo, hi, d, x86)
            st['cases'] += 1; bs = st['byShape'].setdefault(shp, [0, 0]); bs[0] += 1
            if got != want:
                st['mismatch'] += 1; bs[1] += 1
                if len(bad) < 20: bad.append({'lo': hex(lo), 'hi': hex(hi), 'd': hex(d), 'x86': x86, 'got': hex(got), 'want': hex(want)})
    res = {'plant': PLANT, 'noSkip': NOSKIP, **st, 'firstMismatches': bad}
    json.dump(res, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'firstMismatches'}))

if __name__ == '__main__': main()
