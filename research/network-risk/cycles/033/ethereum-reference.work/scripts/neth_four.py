"""Cycle 33 ethereum-reference, lead L-1232. Line-by-line Python transcription of four routines of
Nethermind.Numerics.Int256 1.15.0 (UInt256.divmod.cs, sha256 4703d1a5..., fetched from
raw.githubusercontent.com/NethermindEth/int256/v1.15.0/src/Nethermind.Int256/UInt256.divmod.cs):
MulModBy128Bits (with Remainder128By128Bits, Remainder256By128Bits, Mul128, KnuthStep), Remainder512By192Bits
(with EstimateQhat, SubMulTo3, AddTo3), DivideBy192Bits (with AddBack3, Sub) and DivideBy128BitsX86Base.
Both the x86 hardware DivRem arm (modelled as exact 128/64 division with the #DE precondition asserted) and the
reciprocal arm (Reciprocal2By1 and UDivRem2By1, used on hosts without X86Base.X64) are run where the source has both.
Usage: python3 -I neth_four.py <seed-table.cs> <out.json> [N].  PLANT=1..6 plants one fault (see the PLANT tests).
Branch counters in the output show how often each rare correction and add-back branch ran."""
import sys, os, json, random, re
M64 = (1 << 64) - 1
PLANT = int(os.environ.get('PLANT', '0'))
src = open(sys.argv[1]).read()
blk = src[src.index('ReciprocalSeedTable'):]; blk = blk[blk.index('['):blk.index('];')]
SEED = [int(x, 16) for x in re.findall(r'0x[0-9A-Fa-f]+', blk)]; assert len(SEED) == 256

def mul64(a, b): p = a * b; return p >> 64, p & M64
def lzc(x): return 64 - x.bit_length()

def reciprocal2by1(d):
    assert d >> 63
    v0 = SEED[(d >> 55) & 0xFF]; d40 = ((d >> 24) + 1) & M64
    v1 = ((v0 << 11) - ((v0 * v0 * d40 & M64) >> 40) - 1) & M64
    v2 = ((v1 << 13) + ((v1 * ((0x1000000000000000 - v1 * d40) & M64) & M64) >> 47)) & M64
    d0 = d & 1; d63 = (d >> 1) + d0
    e = (((v2 >> 1) & ((0 - d0) & M64)) - (v2 * d63)) & M64
    v3 = (((v2 * e) >> 64 >> 1) + (v2 << 31)) & M64
    ph, pl = mul64(v3, d); ph = (ph + (1 if pl > (~d & M64) else 0)) & M64
    return (v3 - ph - d) & M64

def udivrem2by1(uh, rec, d, ul):
    hi, low = mul64(rec, uh); low = (low + ul) & M64
    q = (hi + uh + 1) & M64
    if low < ul: q = (q + 1) & M64
    r1 = (ul - q * d) & M64
    if r1 > low: q = (q - 1) & M64; r1 = (r1 + d) & M64
    if r1 >= d: q = (q + 1) & M64; r1 = (r1 - d) & M64
    return q, r1

def hwdiv(lo, hi, d):  # X86Base.X64.DivRem(lower, upper, divisor); #DE when upper >= divisor
    assert hi < d, 'x86 #DE'
    n = (hi << 64) | lo; return n // d, n % d

def dr(lo, hi, d, x86, rec):
    return hwdiv(lo, hi, d) if x86 else udivrem2by1(hi, rec, d, lo)

# ---------------- KnuthStep and the 128-bit modulus reducers (MulModBy128Bits) ----------------
def knuth_step(u, i0, i1, i2, d0, d1, rec, x86):
    oldU2 = u[i2]
    full = False
    if oldU2 >= d1:
        qhat = M64; full = True
    else:
        qhat, rhat = dr(u[i1], oldU2, d1, x86, rec)
        v0 = u[i0]; hi0, lo0 = mul64(d0, qhat)
        u[i0] = (v0 - lo0) & M64
        b0 = hi0 + (1 if lo0 > v0 else 0)
        u[i1] = (rhat - b0) & M64
        if b0 <= rhat and PLANT != 1:
            u[i2] = 0; return
        stats['knuthCorrect'] += 1; u[i2] = M64; correct_step(u, i0, i1, i2, d0, d1); return
    # FullSubMul
    hi0, lo0 = mul64(d0, qhat); hi1, lo1 = mul64(d1, qhat)
    x00 = u[i0]; u[i0] = (x00 - lo0) & M64; b0 = 1 if x00 < lo0 else 0
    mid = (hi0 + lo1) & M64; cm = 1 if mid < hi0 else 0
    mid2 = (mid + b0) & M64; cm |= 1 if mid2 < b0 else 0; mid = mid2
    x11 = u[i1]; u[i1] = (x11 - mid) & M64; b1 = 1 if x11 < mid else 0
    borrow = (hi1 + cm + b1) & M64
    u[i2] = (oldU2 - borrow) & M64
    stats['knuthFullSubMul'] += 1
    if oldU2 < borrow: stats['knuthFullCorrect'] += 1; correct_step(u, i0, i1, i2, d0, d1)

def add_to2(u, i0, i1, y0, y1):
    x00 = u[i0]; s0 = (x00 + y0) & M64; c0 = 1 if s0 < x00 else 0; u[i0] = s0
    x11 = u[i1]; s1 = (x11 + y1) & M64; c1 = 1 if s1 < x11 else 0
    s1c = (s1 + c0) & M64; c2 = 1 if s1c < s1 else 0; u[i1] = s1c
    return c1 | c2

def correct_step(u, i0, i1, i2, d0, d1):
    u[i2] = (u[i2] + add_to2(u, i0, i1, d0, d1)) & M64
    if u[i2] != 0: u[i2] = (u[i2] + add_to2(u, i0, i1, d0, d1)) & M64

def rem128by128(u0, u1, d0, d1, x86):
    if u1 == 0: return u0, 0
    if u1 < d1 or (u1 == d1 and u0 < d0): return u0, u1
    sh = lzc(d1)
    if sh == 0: u = [u0, u1, 0]; nd0, nd1 = d0, d1
    else:
        rs = 64 - sh; u = [(u0 << sh) & M64, ((u1 << sh) | (u0 >> rs)) & M64, u1 >> rs]
        nd0 = (d0 << sh) & M64; nd1 = ((d1 << sh) | (d0 >> rs)) & M64
    rec = 0 if x86 else reciprocal2by1(nd1)
    knuth_step(u, 0, 1, 2, nd0, nd1, rec, x86)
    if sh == 0: return u[0], u[1]
    rs = 64 - sh; return ((u[0] >> sh) | (u[1] << rs)) & M64, u[1] >> sh

def rem256by128(u0, u1, u2, u3, d0, d1, x86):
    if (u2 | u3) == 0:
        if u1 == 0: return u0, 0
        if u1 < d1 or (u1 == d1 and u0 < d0): return u0, u1
    sh = lzc(d1)
    if sh == 0: u = [u0, u1, u2, u3, 0]; nd0, nd1 = d0, d1
    else:
        rs = 64 - sh
        u = [(u0 << sh) & M64, ((u1 << sh) | (u0 >> rs)) & M64, ((u2 << sh) | (u1 >> rs)) & M64,
             ((u3 << sh) | (u2 >> rs)) & M64, u3 >> rs]
        nd0 = (d0 << sh) & M64; nd1 = ((d1 << sh) | (d0 >> rs)) & M64
    rec = 0 if x86 else reciprocal2by1(nd1)
    if u3 != 0:
        knuth_step(u, 2, 3, 4, nd0, nd1, rec, x86); knuth_step(u, 1, 2, 3, nd0, nd1, rec, x86); knuth_step(u, 0, 1, 2, nd0, nd1, rec, x86)
    elif u2 != 0:
        knuth_step(u, 1, 2, 3, nd0, nd1, rec, x86); knuth_step(u, 0, 1, 2, nd0, nd1, rec, x86)
    else:
        knuth_step(u, 0, 1, 2, nd0, nd1, rec, x86)
    if sh == 0: return u[0], u[1]
    rs = 64 - sh; return ((u[0] >> sh) | (u[1] << rs)) & M64, u[1] >> sh

def L(x): return [(x >> (64 * i)) & M64 for i in range(4)]

def mul128(a0, a1, b0, b1):
    hi00, p0 = mul64(a0, b0); hi01, lo01 = mul64(a0, b1); hi10, lo10 = mul64(a1, b0); hi11, lo11 = mul64(a1, b1)
    s1 = (hi00 + lo01) & M64; c1 = 1 if s1 < hi00 else 0
    t1 = (s1 + lo10) & M64; c1 += 1 if t1 < s1 else 0; p1 = t1
    s2 = (hi01 + hi10) & M64; c2 = 1 if s2 < hi01 else 0
    t2 = (s2 + lo11) & M64; c2 += 1 if t2 < s2 else 0
    t3 = (t2 + c1) & M64; c2 += 1 if t3 < t2 else 0; p2 = t3
    p3 = (hi11 + c2) & M64
    return p0, p1, p2, p3

def mulmod_by128(x, y, m0, m1, x86):
    q = x if y == 1 else (y if x == 1 else None)
    if q is None:
        if x <= M64 and y <= M64:
            hi, lo = mul64(x, y); r0, r1 = rem128by128(lo, hi, m0, m1, x86)
        else:
            x0, x1 = rem256by128(*L(x), m0, m1, x86); y0, y1 = rem256by128(*L(y), m0, m1, x86)
            p = mul128(x0, x1, y0, y1); r0, r1 = rem256by128(*p, m0, m1, x86)
    else:
        r0, r1 = rem256by128(*L(q), m0, m1, x86)
    return r0 | (r1 << 64)

# ---------------- Remainder512By192Bits ----------------
def submul3(u, j, y0, y1, y2, mul):
    ph0, pl0 = mul64(y0, mul); v0 = u[j]; u[j] = (v0 - pl0) & M64; borrow = ph0 + (1 if v0 < pl0 else 0)
    ph1, pl1 = mul64(y1, mul); v1 = u[j + 1]; s1 = (pl1 + borrow) & M64; c1 = 1 if s1 < borrow else 0
    u[j + 1] = (v1 - s1) & M64; borrow = ph1 + c1 + (1 if v1 < s1 else 0)
    ph2, pl2 = mul64(y2, mul); v2 = u[j + 2]; s2 = (pl2 + borrow) & M64; c2 = 1 if s2 < borrow else 0
    u[j + 2] = (v2 - s2) & M64; borrow = (ph2 + c2 + (1 if v2 < s2 else 0)) & M64
    return borrow

def add3(u, j, y0, y1, y2):
    a, b, c = u[j], u[j + 1], u[j + 2]
    s0 = (a + y0) & M64; c0 = 1 if s0 < a else 0
    t1 = (b + y1) & M64; s1 = (t1 + c0) & M64; c1 = (1 if t1 < b else 0) | (1 if s1 < c0 else 0)
    t2 = (c + y2) & M64; s2 = (t2 + c1) & M64; c2 = (1 if t2 < c else 0) | (1 if s2 < c1 else 0)
    u[j], u[j + 1], u[j + 2] = s0, s1, s2
    return c2

def estimate_qhat(u2, u1, u0, dh, dl, rec, x86):
    if u2 > dh: return M64
    if u2 == dh:
        qhat = M64; rhat = (u1 + dh) & M64
        if rhat < u1: return qhat
    else:
        qhat, rhat = dr(u1, u2, dh, x86, rec)
    while True:
        ph, pl = mul64(qhat, dl)
        if ph < rhat or (ph == rhat and pl <= u0): break
        qhat = (qhat - 1) & M64; prev = rhat; rhat = (rhat + dh) & M64
        if rhat < prev: break
    return qhat

def rem512by192(lo, hi, d, x86):
    d0, d1, d2, _ = L(d); assert d2 and not (d >> 192) and hi
    sh = lzc(d2)
    l0, l1, l2, l3 = L(lo); u4, u5, u6, u7 = L(hi)
    uLen = 8 if u7 else (7 if u6 else (6 if u5 else 5))
    if sh == 0:
        un = [l0, l1, l2, l3, u4, u5, u6, u7, 0]
        if un[uLen - 1] < d2: uLen -= 1
        nd0, nd1, nd2 = d0, d1, d2
    else:
        rs = 64 - sh
        w = [l0, l1, l2, l3, u4, u5, u6, u7]
        un = [0] * 9; un[8] = u7 >> rs
        for k in range(7, 0, -1): un[k] = ((w[k] << sh) | (w[k - 1] >> rs)) & M64
        un[0] = (l0 << sh) & M64
        nd0 = (d0 << sh) & M64; nd1 = ((d1 << sh) | (d0 >> rs)) & M64; nd2 = ((d2 << sh) | (d1 >> rs)) & M64
        top = u6 if u6 else (u5 if u5 else u4)
        if (u7 <= d2 if PLANT == 2 else u7 < d2) and (u7 != 0 or top < d2): uLen -= 1
    m = uLen - 3
    rec = 0 if x86 else reciprocal2by1(nd2)
    stats['skipTaken'] += 1 if uLen < (8 if u7 else (7 if u6 else (6 if u5 else 5))) else 0
    for j in range(m, -1, -1):
        u8, u9, u10 = un[j + 3], un[j + 2], un[j + 1]
        full = False
        if u8 >= nd2:
            qhat = estimate_qhat(u8, u9, u10, nd2, nd1, rec, x86); full = True
        else:
            qhat, rhat = dr(u9, u8, nd2, x86, rec)
            ph, pl = mul64(qhat, nd1)
            while ph > rhat or (ph == rhat and pl > u10):
                qhat = (qhat - 1) & M64; prev = rhat; rhat = (rhat + nd2) & M64
                if rhat < prev: full = True; break
                ph = (ph - (1 if pl < nd1 else 0)) & M64; pl = (pl - nd1) & M64
            if not full:
                v0 = un[j]; hi0, lo0 = mul64(nd0, qhat); un[j] = (v0 - lo0) & M64
                borrow1 = hi0 + (1 if lo0 > v0 else 0)
                v1 = u10; t1 = (v1 - borrow1) & M64; un[j + 1] = (t1 - pl) & M64
                borrow1 = (ph + (1 if borrow1 > v1 else 0) + (1 if pl > t1 else 0)) & M64
                un[j + 2] = (rhat - borrow1) & M64
                if borrow1 > rhat and PLANT != 3: stats['r192InlineAddBack'] += 1; add3(un, j, nd0, nd1, nd2)
                continue
        stats['r192FullSubMul'] += 1
        borrow = submul3(un, j, nd0, nd1, nd2, qhat)
        if u8 < borrow and PLANT != 6: stats['r192FullAddBack'] += 1; add3(un, j, nd0, nd1, nd2)
    rw0, rw1, rw2 = un[0], un[1], un[2]
    if sh == 0: return rw0 | (rw1 << 64) | (rw2 << 128)
    rs = 64 - sh
    return (((rw0 >> sh) | (rw1 << rs)) & M64) | ((((rw1 >> sh) | (rw2 << rs)) & M64) << 64) | ((rw2 >> sh) << 128)

# ---------------- DivideBy192Bits ----------------
def sub(x, y, borrow):
    t = (x - y) & M64; b1 = 1 if x < y else 0; t2 = (t - borrow) & M64; b2 = 1 if t < borrow else 0
    return t2, (b1 | b2)

def addback3(u, v0, v1, v2):  # u = [u0,u1,u2,u3]
    s = (u[0] + v0) & M64; carry = 1 if s < u[0] else 0; u[0] = s
    s = (u[1] + v1) & M64; c = 1 if s < u[1] else 0; s = (s + carry) & M64; carry = c | (1 if s < carry else 0); u[1] = s
    s = (u[2] + v2) & M64; c = 1 if s < u[2] else 0; s = (s + carry) & M64; carry = c | (1 if s < carry else 0); u[2] = s
    u[3] = (u[3] + carry) & M64

def div192(x, y, x86):
    y0, y1, y2, _ = L(y); assert y2 and not (y >> 192)
    sh = lzc(y2)
    if sh == 0: v0, v1n, v2n = y0, y1, y2
    else:
        rs = 64 - sh; v0 = (y0 << sh) & M64; v1n = ((y1 << sh) | (y0 >> rs)) & M64; v2n = ((y2 << sh) | (y1 >> rs)) & M64
    x0, x1, x2, x3 = L(x)
    if sh == 0: u0, u1, u2, u3, u4 = x0, x1, x2, x3, 0
    else:
        rs = 64 - sh
        u0 = (x0 << sh) & M64; u1 = ((x1 << sh) | (x0 >> rs)) & M64; u2 = ((x2 << sh) | (x1 >> rs)) & M64
        u3 = ((x3 << sh) | (x2 >> rs)) & M64; u4 = x3 >> rs
    rec = 0 if x86 else reciprocal2by1(v2n)
    if u4 == 0 and u3 < v2n:
        q1 = 0
    else:
        assert u4 < v2n
        qhat, rhat = dr(u3, u4, v2n, x86, rec); rcarry = 0
        if rcarry == 0:
            pH, pL = mul64(qhat, v1n)
            if pH > rhat or (pH == rhat and pL > u2):
                qhat = (qhat - 1) & M64; s1 = (rhat + v2n) & M64
                if s1 < rhat: rcarry = 1
                rhat = s1
        if rcarry == 0 and PLANT != 4:
            pH, pL = mul64(qhat, v1n)
            if pH > rhat or (pH == rhat and pL > u2): qhat = (qhat - 1) & M64
        b = 0
        pH1, pL1 = mul64(qhat, v0); u1, b = sub(u1, pL1, b)
        carry = pH1; pH1, pL1 = mul64(qhat, v1n); s2 = (pL1 + carry) & M64; c2 = 1 if s2 < pL1 else 0
        carry = pH1 + c2; u2, b = sub(u2, s2, b)
        pH1, pL1 = mul64(qhat, v2n); s2 = (pL1 + carry) & M64; c2 = 1 if s2 < pL1 else 0
        carry = (pH1 + c2) & M64; u3, b = sub(u3, s2, b)
        u4, b = sub(u4, carry, b)
        if b:
            stats['d192AddBack1'] += 1; w = [u1, u2, u3, u4]; addback3(w, v0, v1n, v2n); u1, u2, u3, u4 = w; qhat = (qhat - 1) & M64
        q1 = qhat
    if u3 == v2n:
        qhat1 = M64; s3 = (u2 + v2n) & M64; rcarry1 = 1 if s3 < u2 else 0; rhat1 = s3
    else:
        qhat1, rhat1 = dr(u2, u3, v2n, x86, rec); rcarry1 = 0
    if rcarry1 == 0:
        pH, pL = mul64(qhat1, v1n)
        if pH > rhat1 or (pH == rhat1 and pL > u1):
            qhat1 = (qhat1 - 1) & M64; s4 = (rhat1 + v2n) & M64
            if s4 < rhat1: rcarry1 = 1
            rhat1 = s4
    if rcarry1 == 0:
        pH, pL = mul64(qhat1, v1n)
        if pH > rhat1 or (pH == rhat1 and pL > u1): qhat1 = (qhat1 - 1) & M64
    b = 0
    pH4, pL4 = mul64(qhat1, v0); s6 = pL4; c3 = 1 if s6 < pL4 else 0; carry1 = pH4 + c3; u0, b = sub(u0, s6, b)
    pH4, pL4 = mul64(qhat1, v1n); s6 = (pL4 + carry1) & M64; c3 = 1 if s6 < pL4 else 0; carry1 = pH4 + c3; u1, b = sub(u1, s6, b)
    pH4, pL4 = mul64(qhat1, v2n); s6 = (pL4 + carry1) & M64; c3 = 1 if s6 < pL4 else 0; carry1 = (pH4 + c3) & M64; u2, b = sub(u2, s6, b)
    u3, b = sub(u3, carry1, b)
    if b:
        stats['d192AddBack0'] += 1; w = [u0, u1, u2, u3]; addback3(w, v0, v1n, v2n); u0, u1, u2, u3 = w; qhat1 = (qhat1 - 1) & M64
    q = qhat1 | (q1 << 64)
    remN = u0 | (u1 << 64) | (u2 << 128)
    return q, remN >> sh  # ShiftRightSmall on a value whose top limb is zero

# ---------------- DivideBy128BitsX86Base ----------------
def div128x86(x, y):
    y0, y1, y2, y3 = L(y); assert y1 and not (y2 | y3)
    sh = lzc(y1)
    if sh: rs = 64 - sh; v0 = (y0 << sh) & M64; v1n = ((y1 << sh) | (y0 >> rs)) & M64
    else: v0, v1n = y0, y1
    u0, u1, u2, u3 = L(x)
    if sh:
        rs = 64 - sh; u4 = u3 >> rs; u3 = ((u3 << sh) | (u2 >> rs)) & M64; u2 = ((u2 << sh) | (u1 >> rs)) & M64
        u1 = ((u1 << sh) | (u0 >> rs)) & M64; u0 = (u0 << sh) & M64
    else: u4 = 0
    q = [0, 0, 0, 0]
    if v0 == 0:
        stats['v0zero'] += 1
        r = u4
        q[2], r = hwdiv(u3, r, v1n); q[1], r = hwdiv(u2, r, v1n); q[0], r = hwdiv(u1, r, v1n)
        if sh == 0: rem = u0 | (r << 64)
        else: rs = 64 - sh; rem = (((u0 >> sh) | (r << rs)) & M64) | ((r >> sh) << 64)
        return q[0] | (q[1] << 64) | (q[2] << 128), rem
    def step(hiL, midL, lowL, guard_eq):
        if guard_eq and hiL == v1n:
            qhat = M64; rhat = (midL + v1n) & M64; rcarry = rhat < midL
        else:
            qhat, rhat = hwdiv(midL, hiL, v1n); rcarry = False
        hi, lo = mul64(qhat, v0)
        if not rcarry and (hi > rhat or (hi == rhat and lo > lowL)):
            qhat = (qhat - 1) & M64; lo2 = (lo - v0) & M64; hi = (hi - (1 if lo < v0 else 0)) & M64; lo = lo2
            rhat = (rhat + v1n) & M64; rcarry = rhat < v1n
            if not rcarry and (hi > rhat or (hi == rhat and lo > lowL)) and PLANT != 5:
                stats['d128SecondCorrection'] += 1; qhat = (qhat - 1) & M64; lo2 = (lo - v0) & M64; hi = (hi - (1 if lo < v0 else 0)) & M64; lo = lo2
                rhat = (rhat + v1n) & M64
        borrow = 1 if lowL < lo else 0
        return qhat, (lowL - lo) & M64, (rhat - hi - borrow) & M64
    if u4 == 0 and u3 < v1n: q[2] = 0
    else:
        assert u4 < v1n
        q[2], u2, u3 = step(u4, u3, u2, False)
    if u3 == 0 and u2 < v1n: q[1] = 0
    else: q[1], u1, u2 = step(u3, u2, u1, True)
    q[0], u0, u1 = step(u2, u1, u0, True)
    # remainder unnormalise (lines 4152 onward: the shift != 0 arm mirrors the v0 == 0 arm)
    if sh == 0: rem = u0 | (u1 << 64)
    else: rs = 64 - sh; rem = (((u0 >> sh) | (u1 << rs)) & M64) | ((u1 >> sh) << 64)
    return q[0] | (q[1] << 64) | (q[2] << 128), rem

stats = {k: 0 for k in ('skipTaken', 'v0zero', 'knuthCorrect', 'knuthFullSubMul', 'knuthFullCorrect', 'r192InlineAddBack', 'r192FullSubMul', 'r192FullAddBack', 'd192AddBack1', 'd192AddBack0', 'd128SecondCorrection')}

def main():
    out = sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
    rnd = random.Random(33)
    Q96, Q128 = 1 << 96, 1 << 128
    MINP, MAXP = 4295128739, 1461446703485210103287273052203988822378723970342
    def word():
        k = rnd.random()
        if k < 0.2: return rnd.choice([0, 1, 2, M64, 1 << 64, Q96 - 1, Q96, Q128 - 1, Q128, (1 << 160) - 1, 1 << 160, MINP, MAXP,
                                        (1 << 255), (1 << 256) - 1, (1 << 192) - 1, 1 << 192]) ^ (rnd.getrandbits(2) if rnd.random() < 0.3 else 0)
        if k < 0.55: return rnd.getrandbits(rnd.randint(1, 256))
        if k < 0.7: return (((1 << 256) - 1) >> rnd.randint(0, 200)) ^ (1 << rnd.randint(0, 255)) & ((1 << 256) - 1)
        if k < 0.85: return (rnd.randint(MINP, MAXP) << rnd.choice([0, 32, 64, 96])) & ((1 << 256) - 1)  # sqrtPrice and shifted forms
        return rnd.getrandbits(256)
    def mod192():
        k = rnd.random()
        if k < 0.25: return Q128 + rnd.choice([0, 0, 1, rnd.getrandbits(64)])  # Q128 and neighbours (mulmod by 2^128 is 129-bit)
        if k < 0.5: return rnd.randint(MINP, MAXP) if rnd.random() < 0.8 else MAXP  # sqrt prices as denominators
        if k < 0.6: return (1 << 192) - 1 - rnd.getrandbits(rnd.randint(0, 40))
        if k < 0.7: return (1 << 128) | rnd.getrandbits(rnd.randint(1, 63))
        return rnd.getrandbits(rnd.randint(129, 192)) | (1 << 128)
    def mod128():
        k = rnd.random()
        if k < 0.3: return Q96 + rnd.choice([0, 0, 1, rnd.getrandbits(32)])
        if k < 0.45: return Q128 - 1 - rnd.getrandbits(rnd.randint(0, 40))
        if k < 0.55: return (1 << 64) | rnd.getrandbits(rnd.randint(1, 63))
        if k < 0.65: return rnd.getrandbits(rnd.randint(65, 128)) << 0 & ~M64 | 0  # low limb zero: v0 == 0 fast path
        return rnd.getrandbits(rnd.randint(65, 128)) | (1 << 64)
    res = {}; bad = []
    def chk(name, got, want, inp):
        st = res.setdefault(name, [0, 0]); st[0] += 1
        if got != want:
            st[1] += 1
            if len(bad) < 40: bad.append({'fn': name, 'in': [hex(v) for v in inp], 'got': str(got), 'want': str(want)})
    for it in range(N):
        # MulModBy128Bits: reached from MulModBy65To128Bits when at most one operand is wider than 128 bits
        m = mod128()
        if m >> 128 or not (m >> 64): m = (1 << 64) | (m & M64) | 1
        x, y = word(), word()
        if rnd.random() < 0.6: y &= (1 << 128) - 1
        if rnd.random() < 0.3: x &= (1 << 128) - 1
        if rnd.random() < 0.02: y = 1
        if not (((x >> 128) != 0) and ((y >> 128) != 0)) and x and y and x != 1 and y != 1:
            for x86 in (True, False):
                chk('MulModBy128Bits' + ('/x86' if x86 else '/recip'), mulmod_by128(x, y, m & M64, m >> 64, x86), (x * y) % m, [x, y, m])
        # Remainder512By192Bits: reached from MultiplyModWideCore with m.u3 == 0, m.u2 != 0 and a nonzero high half
        d = mod192(); x, y = word(), word()
        if rnd.random() < 0.5: x |= 1 << 255
        p = x * y
        if p >> 256 and d >> 128 and not (d >> 192):
            for x86 in (True, False):
                chk('Remainder512By192Bits' + ('/x86' if x86 else '/recip'), rem512by192(p & ((1 << 256) - 1), p >> 256, d, x86), p % d, [x, y, d])
        # DivideBy192Bits: DIV and MOD with a 129..192 bit non power of two divisor and x > y
        d = mod192(); x = word()
        if rnd.random() < 0.4: x = ((rnd.randint(MINP, MAXP) << 96) | rnd.getrandbits(96)) & ((1 << 256) - 1)
        if x > d and d & (d - 1):
            for x86 in (True, False):
                chk('DivideBy192Bits' + ('/x86' if x86 else '/recip'), div192(x, d, x86), (x // d, x % d), [x, d])
        # DivideBy128BitsX86Base: DIV and MOD with a 65..128 bit non power of two divisor and x > y
        d = mod128()
        if d >> 128 or not (d >> 64): d = (1 << 64) | (d & M64) | 1
        x = word()
        if x > d and d & (d - 1):
            chk('DivideBy128BitsX86Base', div128x86(x, d), (x // d, x % d), [x, d])
    # hard cases: x = q*d + r with r small and the divisor's low limbs near all ones, so the estimate from the top
    # limbs overshoots and the correction and add-back branches run
    for it in range(N // 2):
        for bits, lo_bits, name in ((192, 128, '192'), (128, 64, '128')):
            top = rnd.getrandbits(bits - lo_bits) | (1 << (bits - lo_bits - 1 - rnd.randint(0, 8)))
            d = (top << lo_bits) | ((1 << lo_bits) - 1 - rnd.getrandbits(rnd.randint(0, 20)))
            q = rnd.getrandbits(rnd.randint(1, 256 - d.bit_length() + 1)); r = rnd.getrandbits(rnd.randint(0, 8))
            x = q * d + r
            if x >> 256 or x <= d or not (d & (d - 1)): continue
            if name == '192':
                for x86 in (True, False): chk('DivideBy192Bits' + ('/x86' if x86 else '/recip'), div192(x, d, x86), (x // d, x % d), [x, d])
                q2 = rnd.getrandbits(rnd.randint(257, 448)); p = q2 * d + r
                if p >> 256 and not (p >> 512):
                    for x86 in (True, False): chk('Remainder512By192Bits' + ('/x86' if x86 else '/recip'), rem512by192(p & ((1 << 256) - 1), p >> 256, d, x86), p % d, [p, d])
            else:
                chk('DivideBy128BitsX86Base', div128x86(x, d), (x // d, x % d), [x, d])
                q2 = rnd.getrandbits(rnd.randint(1, 256)); p = q2 * d + r
                if not (p >> 256):
                    for x86 in (True, False): chk('MulModBy128Bits' + ('/x86' if x86 else '/recip'), mulmod_by128(p, 3, d & M64, d >> 64, x86), (p * 3) % d, [p, 3, d])
    # boundary set: every pair of edge words against every edge modulus
    E = [0, 1, M64, 1 << 64, (1 << 128) - 1, 1 << 128, (1 << 192) - 1, 1 << 192, (1 << 255), (1 << 256) - 1, MAXP, MAXP << 96, MAXP << 64, Q96, Q96 - 1]
    D192 = [Q128 + 1, Q128 + M64, (1 << 192) - 1, MAXP, (1 << 191) + 1, (1 << 191) - 1, (1 << 128) | (1 << 127)]
    D128 = [Q96 + 1, Q96 - 1, (1 << 128) - 1, (1 << 64) + 1, (1 << 127) + 1, ((1 << 127) - 1) & ~M64 | (1 << 64), 3 << 96]
    for a in E:
        for b in E:
            for dd in D192:
                p = a * b
                if p >> 256:
                    for x86 in (True, False): chk('Remainder512By192Bits' + ('/x86' if x86 else '/recip'), rem512by192(p & ((1 << 256) - 1), p >> 256, dd, x86), p % dd, [a, b, dd])
                if a > dd and dd & (dd - 1):
                    for x86 in (True, False): chk('DivideBy192Bits' + ('/x86' if x86 else '/recip'), div192(a, dd, x86), (a // dd, a % dd), [a, dd])
            for dd in D128:
                if a and b and a != 1 and b != 1 and not ((a >> 128) and (b >> 128)):
                    for x86 in (True, False): chk('MulModBy128Bits' + ('/x86' if x86 else '/recip'), mulmod_by128(a, b, dd & M64, dd >> 64, x86), (a * b) % dd, [a, b, dd])
                if a > dd and dd & (dd - 1): chk('DivideBy128BitsX86Base', div128x86(a, dd), (a // dd, a % dd), [a, dd])
    tot = sum(v[0] for v in res.values()); mis = sum(v[1] for v in res.values())
    o = {'plant': PLANT, 'cases': tot, 'mismatches': mis, 'perFunction': res, 'skipTaken512By192': stats['skipTaken'],
         'branches': stats, 'firstMismatches': bad[:20]}
    json.dump(o, open(out, 'w'), indent=1)
    print(json.dumps({k: o[k] for k in ('plant', 'cases', 'mismatches', 'perFunction', 'branches')}))

if __name__ == '__main__': main()
