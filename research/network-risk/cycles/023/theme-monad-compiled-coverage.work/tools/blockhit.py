# blockhit.py file.cov idx... : whether the first native leader of each IR block index was hit, and leaders hit/total in it
import sys, collections
f = sys.argv[1]; want = [int(x) for x in sys.argv[2:]]
B = {}; L = collections.defaultdict(list)
for l in open(f):
    t = l.split()
    if t[0] == 'B': B[int(t[1])] = int(t[2])
    elif t[0] == 'L': L[int(t[2])].append((int(t[1], 16), int(t[4])))
for i in want:
    xs = sorted(L[i]); print(i, 'evm', B[i], 'entered', xs[0][1] if xs else None, 'leaders', sum(h for _, h in xs), '/', len(xs))
