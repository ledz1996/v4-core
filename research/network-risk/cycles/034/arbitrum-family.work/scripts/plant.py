"""Planted fault: a copy of the v1.3.2 transcription that skips the add-back step. Counts the
vectors of knuth132.py whose answer would then differ from Python integers, so a node with
that fault would be reported."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); import knuth132 as K
from evm import MASK
orig = K.knuth
def faulty(u, d, F):
    dh, dl = d[-1], d[-2]; rc = K.recip(dh); q = [0] * (len(u) - len(d)); M64 = K.M64
    for j in range(len(u) - len(d) - 1, -1, -1):
        u2, u1, u0 = u[j + len(d)], u[j + len(d) - 1], u[j + len(d) - 2]
        if u2 >= dh: qh = M64
        else:
            qh, rh = K.by2by1(u2, u1, dh, rc, F); p = qh * dl
            if (p >> 64) > rh or ((p >> 64) == rh and (p & M64) > u0): qh -= 1
        borrow = 0
        for i in range(len(d)):
            s = u[j + i] - borrow; c1 = 1 if s < 0 else 0; s &= M64
            pr = d[i] * qh; t = s - (pr & M64); c2 = 1 if t < 0 else 0
            u[j + i] = t & M64; borrow = (pr >> 64) + c1 + c2
        u[j + len(d)] = (u2 - borrow) & M64
        q[j] = qh
    return q
V, _ = K.vectors()
K.knuth = faulty
def sgn(x): return x >> 255
caught = 0; n = 0
for op, a, b, c in V:
    if op in ('DIV', 'MOD'): q, r, _ = K.udivrem(a, 4, b); got = q if op == 'DIV' else r; want = a // b if op == 'DIV' else a % b
    elif op in ('SDIV', 'SMOD'):
        A = K.neg(a) if sgn(a) else a; Bv = K.neg(b) if sgn(b) else b
        q, r, _ = K.udivrem(A, 4, Bv); tq, tr = divmod(A, Bv); got, want = (q, tq) if op == 'SDIV' else (r, tr)
    elif op == 'MULMOD': _, got, _ = K.udivrem(a * b, 8, c); want = a * b % c
    else: _, got, _ = K.udivrem(a + b, 5, c); want = (a + b) % c
    n += 1; caught += (got & MASK) != (want & MASK)
print(json.dumps({'vectors': n, 'wouldMismatch': caught}))
