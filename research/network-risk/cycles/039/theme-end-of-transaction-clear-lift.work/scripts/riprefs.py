"""Cycle 39: every RIP-relative ff 15 / ff 25 / mov reference in .text to a given address (binary read as data),
with the FDE function holding it. usage: python3 -I riprefs.py <bin> <fde> <target hex>"""
import bisect, re, struct, subprocess, sys
binf, fde, T = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
b = open(binf, 'rb').read()
for l in subprocess.run(['readelf', '-SW', binf], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fde)); S = [a for a, _ in F]
for i in range(len(seg) - 4):
    pass
import numpy as np
a = np.frombuffer(seg, dtype=np.uint8)
d = (a[:-3].astype(np.int64) | (a[1:-2].astype(np.int64) << 8) | (a[2:-1].astype(np.int64) << 16) | (a[3:].astype(np.int64) << 24))
d = np.where(d >= 1 << 31, d - (1 << 32), d)
pos = np.arange(len(d))
for k in np.nonzero(VA + pos + 4 + d == T)[0]:
    k = int(k); x = VA + k
    j = bisect.bisect_right(S, x) - 1
    print('%#x' % (x - 2), seg[k - 3:k].hex(), 'fn', '%#x..%#x' % F[j] if j >= 0 and F[j][0] <= x < F[j][1] else None)
