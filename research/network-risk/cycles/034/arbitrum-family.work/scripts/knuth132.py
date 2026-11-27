"""Vectors aimed at the branches of holiman/uint256 v1.3.2 division that the PoolManager's
DIV, SDIV, MOD, SMOD, MULMOD (modulus below 2^192) and ADDMOD (overflowing sum, modulus
below 2^192) reach: udivrem, udivremKnuth and udivrem2by1
(cycles/010/theme-go-miscompile.work/dl/u256-v1.3.2/uint256.go:481-581, div.go:19-37).
The transcription below follows the Go text line by line and records which branch each
input takes: 'ovf' (u2 >= dh, qhat = 2^64-1), 'corr' (qhat-- after the 3-by-2 test),
'addback' (u2 < borrow), 'r_gt_ql' and 'r_ge_d' (udivrem2by1 adjustments), 'by1' (one limb
divisor). A vector is kept when it takes a rare branch. The answer the dispatcher returns
is compared with Python integers, not with this transcription.
Usage: python3 knuth132.py <out.json> [chainId ...]
"""
import sys, json, random, os, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../tools/opdiff'))
from evm import *
from battery import dispatcher, run
B = 1 << 64; M64 = B - 1

def limbs(x, n): return [(x >> (64 * i)) & M64 for i in range(n)]
def lz(x): return 64 - x.bit_length()
def recip(d): return ((((~d) & M64) << 64) | M64) // d
def by2by1(uh, ul, d, rc, F):
    p = rc * uh; qh, ql = p >> 64, p & M64
    s = ql + ul; ql = s & M64; c = s >> 64
    qh = (qh + uh + c) & M64; qh = (qh + 1) & M64
    r = (ul - qh * d) & M64
    if r > ql: qh = (qh - 1) & M64; r = (r + d) & M64; F.add('r_gt_ql')
    if r >= d: qh = (qh + 1) & M64; r -= d; F.add('r_ge_d')
    return qh, r
def knuth(u, d, F):
    dh, dl = d[-1], d[-2]; rc = recip(dh); q = [0] * (len(u) - len(d))
    for j in range(len(u) - len(d) - 1, -1, -1):
        u2, u1, u0 = u[j + len(d)], u[j + len(d) - 1], u[j + len(d) - 2]
        if u2 >= dh: qh = M64; F.add('ovf')
        else:
            qh, rh = by2by1(u2, u1, dh, rc, F); p = qh * dl
            if (p >> 64) > rh or ((p >> 64) == rh and (p & M64) > u0): qh -= 1; F.add('corr')
        borrow = 0
        for i in range(len(d)):
            s = (u[j + i] - borrow); c1 = 1 if s < 0 else 0; s &= M64
            pr = d[i] * qh; t = s - (pr & M64); c2 = 1 if t < 0 else 0
            u[j + i] = t & M64; borrow = (pr >> 64) + c1 + c2
        u[j + len(d)] = (u2 - borrow) & M64
        if u2 < borrow:
            qh = (qh - 1) & M64; c = 0; F.add('addback')
            for i in range(len(d)):
                s = u[j + i] + d[i] + c; u[j + i] = s & M64; c = s >> 64
            u[j + len(d)] = (u[j + len(d)] + c) & M64
        q[j] = qh
    return q
def udivrem(uval, ulen, dval):
    """returns (quot, rem, flags) following udivrem of v1.3.2"""
    F = set(); u = limbs(uval, ulen); d = limbs(dval, 4)
    dLen = max(i + 1 for i in range(4) if d[i])
    sh = lz(d[dLen - 1])
    dn = [0] * dLen
    for i in range(dLen - 1, 0, -1): dn[i] = ((d[i] << sh) & M64) | ((d[i - 1] >> (64 - sh)) if sh else 0)
    dn[0] = (d[0] << sh) & M64
    uLen = max([i + 1 for i in range(ulen) if u[i]] or [0])
    if uLen < dLen: return 0, uval, F
    un = [0] * (uLen + 1)
    un[uLen] = (u[uLen - 1] >> (64 - sh)) if sh else 0
    for i in range(uLen - 1, 0, -1): un[i] = ((u[i] << sh) & M64) | ((u[i - 1] >> (64 - sh)) if sh else 0)
    un[0] = (u[0] << sh) & M64
    if dLen == 1:
        F.add('by1'); rc = recip(dn[0]); r = un[-1]; q = [0] * (len(un) - 1)
        for j in range(len(un) - 2, -1, -1): q[j], r = by2by1(r, un[j], dn[0], rc, F)
        return sum(x << (64 * i) for i, x in enumerate(q)), r >> sh, F
    q = knuth(un, dn, F)
    rem = [0] * dLen
    for i in range(dLen - 1): rem[i] = (un[i] >> sh) | ((un[i + 1] << (64 - sh)) & M64 if sh else 0)
    rem[dLen - 1] = un[dLen - 1] >> sh
    return sum(x << (64 * i) for i, x in enumerate(q)), sum(x << (64 * i) for i, x in enumerate(rem)), F

def self_check(rnd, n=20000):
    for _ in range(n):
        ul = rnd.choice((4, 5, 8)); u = rnd.getrandbits(64 * ul); d = rnd.getrandbits(rnd.choice((64, 128, 192, 256))) or 1
        q, r, _ = udivrem(u, ul, d)
        if u >= d: assert (q, r) == divmod(u, d), (hex(u), hex(d))

def neg(x): return (-x) & MASK
def structured(rnd, bits):
    x = 0
    for i in range(bits // 64):
        x |= rnd.choice((0, 1, M64, M64 - 1, 1 << 63, (1 << 63) - 1, rnd.getrandbits(64), rnd.getrandbits(64))) << (64 * i)
    return x

def vectors(seed=34_42161):
    rnd = random.Random(seed); self_check(rnd); V = []; tally = {}
    def keep(op, a, b, c, F):
        rare = F & {'addback', 'ovf', 'r_gt_ql', 'r_ge_d', 'corr'}
        if not rare: return False
        k = op + ':' + '+'.join(sorted(rare)); tally[k] = tally.get(k, 0) + 1
        V.append((op, a, b, c)); return True
    # 1. DIV, MOD, SDIV, SMOD with a constructed add-back: u = Q*d - eps, d of 2 or 3 limbs
    want = {'DIV': 0, 'MOD': 0, 'SDIV': 0, 'SMOD': 0}
    tries = 0
    while min(want.values()) < 1500 and tries < 400000:
        tries += 1
        dbits = rnd.choice((128, 192)) - rnd.randrange(0, 64)
        d = structured(rnd, 192) if rnd.random() < 0.3 else rnd.getrandbits(dbits)
        d &= (1 << dbits) - 1; d |= 1 << (dbits - 1)
        if rnd.random() < 0.5: d |= M64  # large low limb makes the truncated estimate high
        qmax = (MASK // d)
        Q = rnd.randrange(1, qmax + 1) if rnd.random() < 0.5 else qmax - rnd.getrandbits(8) % qmax
        eps = rnd.choice((1, 2, rnd.getrandbits(16) + 1, rnd.getrandbits(64) + 1))
        u = Q * d - eps
        if u <= d or u > MASK or u < B: continue
        _, _, F = udivrem(u, 4, d)
        op = rnd.choice(list(want))
        if op in ('SDIV', 'SMOD'):
            if u >> 255 or d >> 255: continue
            a = neg(u) if rnd.random() < 0.5 else u; b = neg(d) if rnd.random() < 0.5 else d
        else: a, b = u, d
        if want[op] < 1500 and keep(op, a, b, 0, F): want[op] += 1
    # 2. MULMOD with modulus below 2^192 over an 8 limb product: structured search
    n = 0; tries = 0
    while n < 4000 and tries < 300000:
        tries += 1
        a = structured(rnd, 256) if rnd.random() < 0.6 else rnd.getrandbits(256)
        b = structured(rnd, 256) if rnd.random() < 0.6 else rnd.getrandbits(256)
        mb = rnd.choice((64, 128, 192)) - rnd.randrange(0, 64)
        m = (structured(rnd, 192) & ((1 << mb) - 1)) | (1 << (mb - 1))
        if rnd.random() < 0.3: m |= M64
        if not a or not b: continue
        P = a * b
        if P >> 256 == 0: continue
        _, r, F = udivrem(P, 8, m)
        assert r == P % m
        if keep('MULMOD', a, b, m, F): n += 1
    # 3. MULMOD aimed at the last quotient digit: P = Q*m - eps with a small cofactor
    n2 = 0; tries = 0
    while n2 < 3000 and tries < 300000:
        tries += 1
        mb = rnd.choice((128, 192)) - rnd.randrange(0, 64)
        m = rnd.getrandbits(mb) | (1 << (mb - 1)) | (M64 if rnd.random() < 0.6 else 0)
        a = rnd.getrandbits(256) | (1 << 255)
        T = rnd.getrandbits(510) | (1 << 509)
        T = T - T % m + m - rnd.choice((1, 2, 3))  # T = k*m - small
        b = T // a
        if b > MASK or b == 0: continue
        P = a * b
        _, r, F = udivrem(P, 8, m)
        if keep('MULMOD', a, b, m, F): n2 += 1
    # 4. ADDMOD with an overflowing sum and a modulus below 2^192 (5 limb udivrem)
    n3 = 0; tries = 0
    while n3 < 2000 and tries < 300000:
        tries += 1
        mb = rnd.choice((64, 128, 192)) - rnd.randrange(0, 64)
        m = (structured(rnd, 192) & ((1 << mb) - 1)) | (1 << (mb - 1))
        a = MASK - rnd.getrandbits(rnd.choice((8, 64, 200))); b = MASK - rnd.getrandbits(rnd.choice((8, 64, 255)))
        S = a + b
        if S >> 256 == 0: continue
        _, r, F = udivrem(S, 5, m)
        assert r == S % m
        if keep('ADDMOD', a, b, m, F): n3 += 1
    return V, tally

if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = dispatcher(); V, tally = vectors()
    print(len(V), 'vectors', json.dumps(tally), flush=True)
    nets = [n for n in networks() if not only or n[0] in only]
    def work(n):
        cid, name, url = n
        done, bad, errors = run(url, code, V)
        if errors and done < len(V):
            retry = [t for i, _ in errors for t in V[i:i + 600]]
            d2, b2, e2 = run(url, code, retry, size=150); done += d2; bad += b2; errors = e2
        return {'chainId': cid, 'name': name, 'rpc': url, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:10]}
    res = []
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(work, nets):
            print(f"{r['chainId']:>8} {r['name']:16} ran {r['ran']}/{r['vectors']} mismatches {r['mismatchCount']} errors {len(r['errors'])}", flush=True); res.append(r)
    json.dump({'vectors': len(V), 'branchTally': tally, 'results': res}, open(out, 'w'), indent=1)
