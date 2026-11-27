"""Print the .eh_frame FDE range holding each address. usage: fde.py <fde list> <hex>..."""
import bisect, sys
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(sys.argv[1]))
s = [a for a, b in f]
for x in sys.argv[2:]:
    a = int(x, 16); k = bisect.bisect_right(s, a) - 1
    print(x, hex(f[k][0]), hex(f[k][1]), f[k][1] - f[k][0], 'inside' if f[k][0] <= a < f[k][1] else 'OUTSIDE')
