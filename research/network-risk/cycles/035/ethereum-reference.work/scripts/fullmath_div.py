"""Cycle 35 ethereum-reference. The three DIVs of FullMath.mulDiv by twos = denominator & (0 - denominator)
(src/libraries/FullMath.sol:62, :67, :73), run through the erigon-main harness, whose opDiv takes the log2Exact
shortcut for every power of two. Random 512 bit products and denominators with 0 to 255 trailing zero bits.
Oracle: Python integers. Seed 35_2026_11_28. Usage: python3 fullmath_div.py <harness> <out.json>"""
import sys, json, random, subprocess
M = (1 << 256) - 1; R = random.Random(35_2026_11_28)
V = []
for _ in range(40000):
    tz = R.randint(0, 255)
    d = ((R.getrandbits(256 - tz) | 1) << tz) & M
    if d == 0: d = 1 << tz
    twos = d & (-d % (1 << 256))
    p0 = R.getrandbits(256)
    V += [('DIV', d, twos, 0), ('DIV', p0, twos, 0), ('DIV', (0 - twos) % (1 << 256), twos, 0)]
inp = ''.join('%s 0x%x 0x%x 0x%x\n' % v for v in V)
out = subprocess.run([sys.argv[1]], input=inp.encode(), capture_output=True, check=True).stdout.decode().split()
bad = [(v, o) for v, o in zip(V, out) if int(o, 16) != v[1] // v[2]]
r = {'seed': 35_2026_11_28, 'vectors': len(V), 'returned': len(out), 'mismatches': len(bad), 'records': [[hex(v[1]), hex(v[2]), o] for v, o in bad[:20]]}
json.dump(r, open(sys.argv[2], 'w'), indent=1); print({k: r[k] for k in ('vectors', 'returned', 'mismatches')})
