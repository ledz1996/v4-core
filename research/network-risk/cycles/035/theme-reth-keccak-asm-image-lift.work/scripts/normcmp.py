"""Compare two disassembled functions instruction by instruction with addresses and rip displacements removed.
usage: python3 -I normcmp.py <a.s> <b.s>"""
import re, sys
def norm(f):
    out = []
    for l in open(f):
        m = re.match(r'^\s*[0-9a-f]+:\s+(.*)$', l)
        if not m: continue
        t = re.sub(r'<[^>]*>', '', m.group(1)); t = re.sub(r'#.*', '', t)
        t = re.sub(r'\b[0-9a-f]{6,}\b', 'ADDR', t); t = re.sub(r'rip[+-]0x[0-9a-f]+', 'rip+D', t)
        out.append(' '.join(t.split()))
    return out
a, b = norm(sys.argv[1]), norm(sys.argv[2])
diff = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
print(len(a), len(b), 'differing lines', len(diff)); [print(d) for d in diff[:10]]
