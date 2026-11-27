"""Find byte patterns in an ELF file's .text and map hits to FDE function ranges (reads only).
usage: python3 -I bytefind.py <bin> <fde> <hexpattern>[,<hexpattern2> within 64 bytes]..."""
import bisect, re, subprocess, sys
binf, fdes = sys.argv[1], sys.argv[2]
b = open(binf, 'rb').read()
for l in subprocess.run(['readelf', '-SW', binf], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes)); s = [a for a, _ in f]
def fn(a):
    k = bisect.bisect_right(s, a) - 1
    return f[k] if k >= 0 and f[k][0] <= a < f[k][1] else None
for pat in sys.argv[3:]:
    parts = [bytes.fromhex(p) for p in pat.split(',')]
    seg = b[OFF:OFF + SZ]; hits = set(); i = seg.find(parts[0])
    while i >= 0:
        ok = all(seg.find(p, max(0, i - 64), i + 64 + len(p)) >= 0 for p in parts[1:])
        if ok:
            r = fn(VA + i); hits.add(r)
        i = seg.find(parts[0], i + 1)
    print(pat, ' '.join('%x-%x(%d)' % (r[0], r[1], r[1] - r[0]) for r in sorted(h for h in hits if h)))
