"""Cycle 31: compare asmjit listings line for line. The one '.db' line (read-only data) holds the addresses of runtime
routines, which ASLR moves between runs; bytes that differ between two runs of the same unchanged binary (ref, ref2)
are masked. usage: asmcmp.py ref ref2 other..."""
import sys
def load(p):
    L = open(p).read().splitlines(); db = [i for i, l in enumerate(L) if l.startswith('.db ')]
    assert len(db) == 1, (p, len(db))
    b = [int(x, 16) for x in L[db[0]][4:].split(', ')]
    return L[:db[0]] + L[db[0]+1:], b
r, rb = load(sys.argv[1]); r2, rb2 = load(sys.argv[2])
assert r == r2 and len(rb) == len(rb2)
mask0 = {i for i in range(len(rb)) if rb[i] != rb2[i]}
words = {i // 8 for i in mask0}
mask = {i for i in range(len(rb)) if i // 8 in words}  # whole 8-byte pointer words
print('ref lines %d, rodata bytes %d, ASLR-varying pointer words masked %d (%s)' % (len(r), len(rb), len(words), sorted(words)))
for p in sys.argv[3:]:
    o, ob = load(p)
    nd = sum(1 for a, b in zip(r, o) if a != b) + abs(len(r) - len(o))
    bd = sum(1 for i in range(min(len(rb), len(ob))) if i not in mask and rb[i] != ob[i]) + abs(len(rb) - len(ob))
    print('%s: lines %d, differing lines %d, differing unmasked rodata bytes %d' % (p, len(o), nd, bd))
