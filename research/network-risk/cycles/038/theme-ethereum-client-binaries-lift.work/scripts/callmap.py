"""Maps the call targets of a disassembly listing to function names from the pclntab listing. usage: callmap.py fns.txt listing.s"""
import sys, re, bisect
F = []
for l in open(sys.argv[1]):
    p = l.split()
    F.append((int(p[-4], 16), int(p[-3], 16), ' '.join(p[:-4])))
F.sort(); S = [f[0] for f in F]
def name(a):
    i = bisect.bisect_right(S, a) - 1
    return F[i][2] + ('' if F[i][0] == a else '+%#x' % (a - F[i][0])) if i >= 0 and a < F[i][1] else '?'
from collections import Counter
c = Counter()
for l in open(sys.argv[2]):
    m = re.search(r'\t(call|bl)\s+(0x)?([0-9a-f]+)\b', l)
    if m: c[name(int(m.group(3), 16))] += 1
for n, k in c.most_common(): print(k, n)
