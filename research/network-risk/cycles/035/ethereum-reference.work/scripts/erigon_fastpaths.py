"""Cycle 35 ethereum-reference. Vectors aimed at the fast paths erigon main adds to its handlers: DIV by 2^n (log2Exact),
EXP with base 2^256-1, with an odd base and an exponent of 2^64 or more (expOdd), and the uint64 product loop, and MULMOD
with a cached reciprocal (same modulus on consecutive lines, zero operands on a cache hit, FullMath.mulDiv's pair
mulmod(a, b, not(0)) then mulmod(a, b, denominator)). Oracle: Python integers. Seed 35_2026_11_27.
Usage: python3 erigon_fastpaths.py <harness> <out.json>"""
import sys, json, random, subprocess
M = (1 << 256) - 1
R = random.Random(35_2026_11_27)
def rw(): 
    k = R.choice([8, 64, 96, 128, 160, 192, 255, 256]); return R.getrandbits(k)
def ref(op, a, b, c):
    if op == 'DIV': return a // b if b else 0
    if op == 'EXP': return pow(a, b, 1 << 256)
    if op == 'MULMOD': return (a * b) % c if c else 0
V = []
edges = [0, 1, 2, 3, M, M - 1, 1 << 255, (1 << 255) - 1, (1 << 128) - 1, 1 << 128, (1 << 64) - 1, 1 << 64, (1 << 192) - 1, 1 << 192]
for n in range(256):
    for d in (1 << n, (1 << n) + 1, (1 << n) - 1 if n else 0, (1 << n) | 1, (1 << n) | (1 << 255) if n < 255 else 3 << 254):
        d &= M
        for a in edges + [rw() for _ in range(12)]:
            V.append(('DIV', a & M, d, 0))
# EXP: base all ones, odd bases with big exponents, small fast path, even bases
for _ in range(60000):
    k = R.random()
    if k < 0.15: base = M
    elif k < 0.6: base = rw() | 1
    elif k < 0.8: base = R.getrandbits(R.randint(1, 64)) | R.randint(0, 1)
    else: base = rw()
    j = R.random()
    if j < 0.4: e = (1 << 64) + R.getrandbits(R.choice([1, 8, 64, 130, 192, 256]))
    elif j < 0.5: e = R.choice([1 << 64, (1 << 64) + 1, (1 << 64) + 2, (1 << 64) + 3, M, M - 1, 1 << 255, 1 << 66, (1 << 62) * 4 + 1])
    elif j < 0.8: e = R.randint(0, 70)
    else: e = R.getrandbits(64)
    V.append(('EXP', base & M, e & M, 0))
for b in [M, M - 2, 3, 5, (1 << 255) + 1, (1 << 64) + 1, (1 << 128) + 1, (1 << 192) + 1]:
    for e in [(1 << 64) + i for i in range(-4, 70)] + [M - i for i in range(8)]:
        V.append(('EXP', b, e & M, 0))
# MULMOD sequences: runs with one modulus, so the cache hits
for _ in range(20000):
    m = R.choice([M, M - 1, 1 << 192, (1 << 192) + 1, R.getrandbits(256) | (1 << 192), (1 << 255) | R.getrandbits(255)]) & M
    for _ in range(R.randint(1, 6)):
        t = R.random()
        a = 0 if t < 0.1 else (m - 1 if t < 0.2 else rw())
        b = 0 if 0.1 <= t < 0.15 else (m + 1 if 0.3 < t < 0.35 else rw())
        V.append(('MULMOD', a & M, b & M, m))
for _ in range(20000):  # FullMath.mulDiv pair
    a, b = rw(), rw(); d = R.getrandbits(256) | (1 << R.choice([192, 200, 255]))
    V.append(('MULMOD', a, b, M)); V.append(('MULMOD', a, b, d & M)); V.append(('MULMOD', a, b, M))
inp = ''.join('%s 0x%x 0x%x 0x%x\n' % v for v in V)
out = subprocess.run([sys.argv[1]], input=inp.encode(), capture_output=True, check=True).stdout.decode().split()
bad = [(v, o) for v, o in zip(V, out) if int(o, 16) != ref(*v)]
by = {}
for v in V: by[v[0]] = by.get(v[0], 0) + 1
r = {'seed': 35_2026_11_27, 'vectors': len(V), 'byOp': by, 'returned': len(out), 'mismatches': len(bad), 'records': [[v[0], hex(v[1]), hex(v[2]), hex(v[3]), o] for v, o in bad[:50]]}
json.dump(r, open(sys.argv[2], 'w'), indent=1); print({k: r[k] for k in ('vectors', 'byOp', 'returned', 'mismatches')})
