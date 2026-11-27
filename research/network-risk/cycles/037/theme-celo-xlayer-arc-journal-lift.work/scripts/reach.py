"""Static call reach from given functions of an x86-64 ELF (reads only, objdump text). Follows direct call/jmp and
calls through R_X86_64_RELATIVE GOT words. Prints each reached function with its symbol if any.
usage: python3 -I reach.py <bin> <fde> <rel|-> <nm|-> <depth> <hex>..."""
import bisect, re, subprocess, sys
binf, fdes, relf, nmf, depth = sys.argv[1:6]; depth = int(depth)
f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes)); s = [a for a, b in f]
rel = {}
if relf != '-':
    for l in open(relf):
        p = l.split()
        if len(p) == 2: rel[int(p[0], 16)] = int(p[1], 16)
else:
    for l in subprocess.run(['readelf', '-rW', binf], capture_output=True, text=True).stdout.splitlines():
        m = re.match(r'^([0-9a-f]+)\s+[0-9a-f]+\s+R_X86_64_RELATIVE\s+([0-9a-f]+)', l)
        if m: rel[int(m.group(1), 16)] = int(m.group(2), 16)
nm = {}
if nmf != '-':
    for l in open(nmf):
        p = l.rstrip('\n').split(' ', 2)
        if len(p) == 3 and re.match(r'^[0-9a-f]+$', p[0]): nm.setdefault(int(p[0], 16), p[2])
def fn(a):
    k = bisect.bisect_right(s, a) - 1
    return f[k] if k >= 0 and f[k][0] <= a < f[k][1] else (a, a + 1)
cache = {}
def callees(lo, hi):
    if lo in cache: return cache[lo]
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        m = re.search(r'\s(call|jmp)\s+([0-9a-f]+)\s', l + ' ')
        if m:
            t = int(m.group(2), 16)
            if not (lo <= t < hi): r.append(t)
            continue
        m = re.search(r'\s(call|jmp)\s+QWORD PTR \[rip\+0x[0-9a-f]+\]\s+# ([0-9a-f]+)', l)
        if m:
            g = int(m.group(2), 16)
            if g in rel: r.append(rel[g])
            else: r.append(('got', g))
    cache[lo] = r; return r
seen = set()
def walk(a, d, ind):
    if isinstance(a, tuple): print(' ' * ind + 'GOT %x' % a[1]); return
    lo, hi = fn(a)
    tag = ' *' if lo in seen else ''
    print(' ' * ind + '%x (%d) %s%s' % (lo, hi - lo, nm.get(lo, '?')[:170], tag))
    if lo in seen or d == 0: return
    seen.add(lo)
    for c in callees(lo, hi): walk(c, d - 1, ind + 2)
for x in sys.argv[6:]: walk(int(x, 16), depth, 0)
