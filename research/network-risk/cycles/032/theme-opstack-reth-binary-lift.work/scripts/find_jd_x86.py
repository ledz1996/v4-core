"""Find candidate jump destination analysis loops in an x86-64 binary: a compare with 0x5b near an add of -0x60 (0xa0)
on a byte register and a compare with 0x20. Prints the FDE functions holding the hits."""
import re, sys, bisect
sys.path.insert(0, __import__('os').path.dirname(__file__))
from image import image
img, segs = image(sys.argv[1])
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(sys.argv[2])); s = [a for a, b in f]
text = [(va, va + fs) for va, off, fs, ms in segs][1]
lo, hi = text
data = img[lo:hi]
cmp5b = [m.start() for m in re.finditer(rb'(\x3c\x5b|\x80[\xf8-\xff]\x5b|\x41\x80[\xf8-\xff]\x5b)', data)]
adda0 = re.compile(rb'(\x04\xa0|\x80[\xc0-\xc7]\xa0|\x41\x80[\xc0-\xc7]\xa0|\x2c\x60|\x80[\xe8-\xef]\x60|\x41\x80[\xe8-\xef]\x60)')
hits = {}
for p in cmp5b:
    w = data[max(0, p - 48):p + 48]
    if adda0.search(w) and (b'\x20' in w):
        a = lo + p; k = bisect.bisect_right(s, a) - 1
        if f[k][0] <= a < f[k][1]: hits.setdefault(f[k], []).append(a)
for (a, b), l in sorted(hits.items()):
    print(hex(a), hex(b), b - a, [hex(x) for x in l[:4]])
