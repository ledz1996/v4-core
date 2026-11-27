"""Prints the .eh_frame range that holds each address. usage: python3 -I fde.py <fde list> <hex>..."""
import sys, bisect
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(sys.argv[1]))
s = [a for a, b in f]
for x in sys.argv[2:]:
    a = int(x, 16); k = bisect.bisect_right(s, a) - 1; lo, hi = f[k]
    print(x, hex(lo), hex(hi), hi - lo, 'inside' if lo <= a < hi else 'OUTSIDE')
