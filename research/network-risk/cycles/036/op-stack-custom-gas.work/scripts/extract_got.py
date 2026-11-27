"""Disassemble the instruction handlers of a binary with symbols and every function they reach by direct call,
tail jump or call through a relocated GOT slot (the slot read from the relocation list). Targets whose symbol names a
halt, a panic or a libc copy routine are listed as externs instead of followed. Reads only.
usage: python3 -I extract_got.py <bin> <fdes> <rel> <out.s> <out.json> <hex start>..."""
import bisect, json, re, subprocess, sys
binf, fdes, relf, out_s, out_j = sys.argv[1:6]
starts = [int(x, 16) for x in sys.argv[6:]]
f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes) if '..' in l)
s = [a for a, b in f]
rel = {}
for l in open(relf):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
glob = {}
for l in subprocess.run(['readelf', '-rW', binf], capture_output=True, text=True).stdout.splitlines():
    m = re.match(r'^([0-9a-f]+)\s+\S+\s+R_X86_64_GLOB_DAT\s+\S+\s+(\S+)', l)
    if m: glob[int(m.group(1), 16)] = m.group(2)
DIRECT = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp|j[a-z]+)\s+([0-9a-f]+) <([^>]*)>')
GOTC = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp)\s+QWORD PTR \[rip\+0x[0-9a-f]+\]\s+# ([0-9a-f]+)')
def kind(name):
    n = name.lower()
    for k in ('alloc_zeroed', 'realloc', 'dealloc'):
        if k in n: return k
    if '__rust_alloc' in n or 'rust_alloc' in n: return 'alloc'
    for k in ('memcpy', 'memmove', 'memset', 'bcmp'):
        if k in n: return k
    if 'halt' in n or 'panic' in n or 'abort' in n or 'unwrap_failed' in n or 'slice_' in n: return 'panic'
    return None
todo = list(starts); done = {}; externs = {}; got = {}
names = {}
while todo:
    a = todo.pop()
    k = bisect.bisect_right(s, a) - 1
    lo, hi = f[k]
    if lo in done: continue
    if not (lo <= a < hi):
        externs[hex(a)] = 'panic'; continue  # PLT stub (unwinder) or outside every FDE
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout.splitlines()
    body = [l for l in out if re.match(r'^ *[0-9a-f]+:', l)]
    for l in out:
        m = re.match(r'^([0-9a-f]+) <(.*)>:$', l)
        if m: names[int(m.group(1), 16)] = m.group(2)
    for l in body:
        c = DIRECT.match(l)
        if c:
            t = int(c.group(3), 16)
            if not (lo <= t < hi):
                nm = c.group(4).split('+')[0]
                kd = kind(nm)
                if kd: externs[hex(t)] = kd
                else: todo.append(t)
            continue
        g = GOTC.match(l)
        if g:
            slot = int(g.group(3), 16)
            if slot in glob:
                kd = kind(glob[slot]); got[hex(slot)] = kd or 'unknown:' + glob[slot]; continue
            t = rel.get(slot)
            if t is None: got[hex(slot)] = 'unresolved'; continue
            sym = subprocess.run(['objdump', '-d', '--start-address=%#x' % t, '--stop-address=%#x' % (t + 1), binf],
                                 capture_output=True, text=True).stdout
            m = re.search(r'^[0-9a-f]+ <([^>]*)>:', sym, re.M)
            nm = m.group(1) if m else ''
            kd = kind(nm)
            if kd: got[hex(slot)] = kd
            else: todo.append(t)
    done[lo] = (hi, body)
json.dump({'functions': {hex(a): [hex(h), h - a, names.get(a, '')] for a, (h, b) in sorted(done.items())},
           'externs': externs, 'got': got}, open(out_j, 'w'), indent=1)
open(out_s, 'w').write('\n'.join(l for a in sorted(done) for l in done[a][1]) + '\n')
print(len(done), 'functions', sum(len(b) for h, b in done.values()), 'lines; externs', externs, 'got', got)
