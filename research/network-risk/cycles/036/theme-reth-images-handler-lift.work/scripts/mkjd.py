"""Write the jd.py configuration of one binary's legacy jump analysis (revm-bytecode analyze_legacy): lift the function
and its direct internal callees (extract3.py with every rip-slot call stopped), classify each rip-relative slot the
function calls (dynamic memcpy/memset/memmove; a static allocator entry recognised by its text: malloc-like
'cmp rdi,0x1000', realloc-like 'mov r9,rdi | cmp rsi,0x1000'; the Rust alloc shims; panic and error paths) and
take the output layout from a probe run of a 3-byte program that is checked against nothing else.
Read only. usage: python3 -I mkjd.py <name> <bin> <hex fn>"""
import bisect, json, re, subprocess, sys
name, binf, fa = sys.argv[1:4]
W = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/'
fdef, relf = W + 'build/%s.fde' % name, W + 'build/%s.rel' % name
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdef)); s = [a for a, b in f]
rel = {int(a, 16): int(b, 16) for a, b in (l.split() for l in open(relf))}
dyn = {}
for l in subprocess.run(['readelf', '-rW', binf], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 5 and ('GLOB_DAT' in l or 'JUMP_SLO' in l): dyn[int(p[0], 16)] = p[4].split('@')[0]
def rng(a):
    k = bisect.bisect_right(s, a) - 1
    return f[k] if f[k][0] <= a < f[k][1] else None
def dis(a, b):
    return subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % a,
                           '--stop-address=%#x' % b, binf], capture_output=True, text=True).stdout
def head(t, n=60):
    r = rng(t)
    return [x.split('\t')[-1].strip() for x in dis(t, min(r[1], t + n)).splitlines() if re.match(r'^ *[0-9a-f]+:', x)], r[1] - r[0]
def classify(slot):
    if slot in dyn:
        nm = dyn[slot]
        return {'malloc': 'alloc', 'free': 'dealloc', 'realloc': 'realloc', 'memcpy': 'memcpy', 'memmove': 'memmove',
                'memset': 'memset'}.get(nm, 'panic')
    t = rel.get(slot)
    if t is None or rng(t) is None: return 'panic'
    h, size = head(t)
    j = ' | '.join(h)
    if size <= 8 and h[-1] == 'ret': return 'drop'          # __rust_no_alloc_shim_is_unstable: no effect
    if j.startswith('cmp    rdi,0x1000') : return 'alloc'   # static allocator malloc(size)
    if j.startswith('mov    r9,rdi | cmp    rsi,0x1000'): return 'realloc'
    if 'malloc@' in j or (size < 120 and 'cmp    rsi,0x11' in j): return 'alloc'   # __rust_alloc(size, align<=16)
    if 'free@' in j: return 'dealloc'
    return None  # follow as code
lo, hi = rng(int(fa, 16))
slots = {}
for l in dis(lo, hi).splitlines():
    m = re.search(r'(?:call|jmp)\s+QWORD PTR \[rip[+-]0x[0-9a-f]+\]\s+#\s*([0-9a-f]+)', l)
    if m: slots[int(m.group(1), 16)] = classify(int(m.group(1), 16))
got = {hex(k): v for k, v in slots.items() if v}
follow = [hex(rel[k]) for k, v in slots.items() if v is None]
# lift the function plus followed slot targets; every slot classified above is a stop
stops = ['stop=%#x' % rel[k] for k, v in slots.items() if v and k in rel]
asm, aj = W + 'build/%s-jd.s' % name, W + 'build/%s-jd.json' % name
r = subprocess.run(['python3', '-I', W + 'scripts/extract3.py', binf, fdef, relf, asm, aj, fa] + follow + stops,
                   capture_output=True, text=True)
ex = json.load(open(aj))
# second-level slots of followed code (Bytes::from and similar): classify too
for sl in ex['slots']:
    k = int(sl, 16)
    if hex(k) not in got:
        c = classify(k)
        if c: got[hex(k)] = c
cfg = {'bin': binf, 'arch': 'x86', 'asm': asm, 'fn': fa, 'got': got, 'externs': {}, 'out': 'probe', 'faults': {},
       'followed': follow, 'functions': len(ex['functions'])}
json.dump(cfg, open(W + 'build/%s.jd.json' % name, 'w'), indent=1)
print(name, len(ex['functions']), 'functions', got, 'followed', follow)
