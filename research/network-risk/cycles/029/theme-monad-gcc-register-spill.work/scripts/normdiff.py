"""Compare two objdump function listings after removing addresses, so that two template instances can be compared.
Rip-relative displacements are resolved to absolute targets (they differ only by the distance between the functions).
usage: python3 -I normdiff.py a.s b.s"""
import sys, re
def norm(p):
    L = re.sub(r"\(monad_revision\)1[01]", "(monad_revision)R", open(p).read()).splitlines()[1:]
    base = None; out = []
    for l in L:
        m = re.match(r'\s*([0-9a-f]+):\t(.*)', l)
        if not m: continue
        a = int(m.group(1), 16); t = m.group(2)
        if base is None: base = a
        mm = re.search(r'# ([0-9a-f]+) <', t)
        t = re.sub(r'#.*', '', t)
        if mm: t = re.sub(r'rip\+0x[0-9a-f]+', 'abs:' + mm.group(1), t)
        t = re.sub(r'\b([0-9a-f]{5,}) <([^>+]*)(\+0x([0-9a-f]+))?>', lambda q: ('L+%x' % (int(q.group(1), 16) - base)) if q.group(3) else q.group(2), t)
        out.append(t.strip())
    return out
a, b = norm(sys.argv[1]), norm(sys.argv[2])
n = 0
for i, (x, y) in enumerate(zip(a, b)):
    if x != y: n += 1; print(i, '|', x, '|', y)
print('len', len(a), len(b), 'differ', n)
