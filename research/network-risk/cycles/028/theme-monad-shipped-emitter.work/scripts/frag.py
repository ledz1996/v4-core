"""Cycle 28, Task 2 (first piece). Run the compile-time arithmetic of the literal arms of Monad's shipped emitter
(monad 0.16.7, gcc 15.2.0 build) in the x86 model of cycle 27 (x86emu.py), from the package's own disassembly text,
and compare with the v0.16.7 source rules evaluated with Python integers. Nothing from the package is executed:
x86emu interprets objdump text. Only arithmetic fragments are lifted; the instruction ranges are listed in FRAGS.
Operand set: every PUSH literal of the deployed PoolManager runtime, 2^k, 2^k - 1, 2^k + 1, -2^k for k < 256, words
with one zero limb, and random words (seed 2828). Planted faults: one instruction of each fragment is changed in the
text and the run must report mismatches.
usage: python3 -I frag.py <fn dir> <x86emu dir> <PoolManager.json> <out.json>"""
import sys, os, json, random, re
FN, EMU, PMJ, OUTF = sys.argv[1:5]
sys.path.insert(0, EMU)
import x86emu
from x86emu import CPU, Prog, Stop
M = (1 << 256) - 1; M64 = (1 << 64) - 1

class C(CPU):
    def i_popcnt(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(self.opnd(o[1]), b)
        c = bin(x).count('1'); self.cf = self.of = self.sf = 0; self.zf = int(x == 0); self.put(d, c)

def load(addr):
    t = open(os.path.join(FN, '%016x.s' % addr)).read()
    # drop the symbol annotation after each operand (template names hold '>' that the cycle 27 parser cannot skip)
    return '\n'.join(re.sub(r'\s+<.*$', '', l) if l.startswith(' ') else l for l in t.splitlines()) + '\n'
TXT = {a: load(a) for a in (0x3a5eb0, 0x383b60, 0x37e260)}
def prog(fn, fault=None):
    t = TXT[fn]
    if fault:
        old, new = fault
        assert t.count(old) == 1, (old, t.count(old)); t = t.replace(old, new)
    return Prog(t)
RBP = 0x7ffff0100000; RSP = 0x7ffff0080000
def limbs(v): return [(v >> (64 * i)) & M64 for i in range(4)]
def word(c, a): return sum(c.read(a + 8 * i, 8) << (64 * i) for i in range(4))
def run(c, start, stops, maxsteps=20000):
    pc = start; n = 0
    while pc not in stops:
        pc = c.step(pc); n += 1
        if n > maxsteps: raise Stop('steps')
    return stops[pc]
def fresh(p):
    c = C(p); c.r['rbp'] = RBP; c.r['rsp'] = RSP; return c

# ---- modop_optimized<&monad::mulmod, 1, 0, &Emitter::mul_mod2> (emitter.cpp:7774-7864 at v0.16.7)
def modop(m, p):
    c = fresh(p)
    for i, l in enumerate(limbs(m)): c.write(RBP - 0x90 + 8 * i, 8, l)
    # 3a5f8f..3a5fe2: m == 0 || m == 1 (emitter.cpp:7785)
    t = run(c, 0x3a5f8f, {0x3a5fe8: 'trivial', 0x3a6090: 'nontrivial'})
    out = {'trivial': t == 'trivial'}
    if t == 'trivial': return out
    # 3a6100..3a6131: popcount(m) != 1 (emitter.cpp:7833); r14, r15 and the two frame slots still hold m
    t = run(c, 0x3a6100, {0x3a6137: 'no', 0x3a6280: 'pow2'})
    out['pow2'] = t == 'pow2'
    if t != 'pow2': return out
    # 3a633b..3a63ce: exp = bit_width(m) - 1, passed in rcx to mul_mod2 (emitter.cpp:7857)
    run(c, 0x3a633b, {0x3a63d1: 'call'}); out['exp'] = c.r['rcx']
    # 3a6490..3a64f7 and 3a65aa..3a6611: the mask m - 1 for the b == 1 and a == 1 arms (emitter.cpp:7846, 7851)
    for start, stop, key in ((0x3a6490, 0x3a64fc, 'maskB'), (0x3a65aa, 0x3a6616, 'maskA')):
        c2 = fresh(p); c2.r['r14'] = limbs(m)[0]; c2.r['r15'] = limbs(m)[3]
        c2.write(RBP - 0xf8, 8, limbs(m)[1]); c2.write(RBP - 0xf0, 8, limbs(m)[2])
        run(c2, start, {stop: 'end'}); out[key] = word(c2, RBP - 0x70)
    return out
def modop_ref(m):
    if m in (0, 1): return {'trivial': True}
    o = {'trivial': False, 'pow2': bin(m).count('1') == 1}
    if o['pow2']: o.update(exp=m.bit_length() - 1, maskB=m - 1, maskA=m - 1)
    return o

# ---- mul_mod2 (emitter.cpp:8171-8262): mask = (1 << exp) - 1, last_ix = (exp - 1) >> 6, inline decision, has_zero
ELEM = 0x7ffff0200000
def mulmod2(exp, blit, bval, p):
    c = fresh(p); c.r['rbx'] = exp; c.r['rsi'] = int(blit); c.r['r13'] = ELEM
    for i, l in enumerate(limbs(bval)): c.write(ELEM + 0x58 + 8 * i, 8, l)
    c.write(ELEM + 0x78, 1, int(blit))
    t = run(c, 0x383c70, {0x383fec: 'inline', 0x384498: 'inline', 0x383cf4: 'runtime', 0x3841ab: 'runtime'})
    lastix = c.read(RSP + 0x50, 8)
    if t == 'inline' and not blit and exp >= 64 and exp < 128: lastix = None  # gcc does not store last_ix on this path
    return {'path': t, 'mask': word(c, RSP + 0x100), 'lastix': lastix}
def mulmod2_ref(exp, blit, bval):
    mask = (1 << exp) - 1; lix = (exp - 1) >> 6
    if blit:
        b = bval & mask; hz = any(((b >> (64 * i)) & M64) == 0 for i in range(lix + 1))
        path = 'inline' if (lix <= 1 or hz) else 'runtime'
    else:
        path = 'inline' if lix <= 1 else 'runtime'
    return {'path': path, 'mask': mask, 'lastix': None if (path == 'inline' and not blit and 64 <= exp < 128) else lix}

# ---- mul_optimized (emitter.cpp:7163-7223): a == 0, a_shift = -a if negative, popcount(a_shift) == 1, zero limb test,
# countr_zero(a_shift) (37e7fb..37e830), sign compare a_shift[3] != a[3] (37e897)
def mulopt(a, p):
    c = fresh(p); L = limbs(a)
    c.r['r8'], c.r['rsi'], c.r['rcx'], c.r['r14'] = L; c.r['rdx'], c.r['r9'], c.r['r13'], c.r['r15'] = L
    c.y[0] = a
    t = run(c, 0x37e340, {0x37e738: 'zero', 0x37e7b8: 'pow2', 0x37e900: 'general', 0x37e3d6: 'inline'})
    out = {'path': t}
    if t == 'pow2':
        ash = word(c, RSP + 0xc0); out['ashift'] = ash; out['negate'] = c.r['r15'] != c.r['r13']
        run(c, 0x37e7fb, {0x37e830: 'end'}); out['ctz'] = c.r['rdx'] & 0xffffffff
    return out
def mulopt_ref(a):
    if a == 0: return {'path': 'zero'}
    ash = (-a) & M if a >> 255 else a
    if bin(ash).count('1') == 1:
        return {'path': 'pow2', 'ashift': ash, 'negate': (ash >> 192) != (a >> 192), 'ctz': (ash & -ash).bit_length() - 1}
    if 0 in limbs(a): return {'path': 'inline'}
    return {'path': 'general'}

# operand set
code = bytes.fromhex(json.load(open(PMJ))['runtime'].removeprefix('0x'))
pmlits = set(); pc = 0
while pc < len(code):
    op = code[pc]
    if 0x60 <= op <= 0x7f:
        n = op - 0x5f; pmlits.add(int.from_bytes(code[pc + 1:pc + 1 + n], 'big')); pc += 1 + n
    else: pc += 1
rnd = random.Random(2828)
words = set(pmlits)
for k in range(256):
    words |= {1 << k, (1 << k) - 1, ((1 << k) + 1) & M, (-(1 << k)) & M, (-(1 << k) + 1) & M}
for _ in range(3000):
    w = rnd.getrandbits(256)
    words.add(w)
    z = limbs(w); z[rnd.randrange(4)] = 0; words.add(sum(l << (64 * i) for i, l in enumerate(z)))
    words.add(1 << rnd.randrange(256) | 1 << rnd.randrange(256))
words = sorted(words)

def campaign(fault_modop=None, fault_mm2=None, fault_mul=None, limit=None):
    pa, pb, pc_ = prog(0x3a5eb0, fault_modop), prog(0x383b60, fault_mm2), prog(0x37e260, fault_mul)
    bad = []; n = 0
    ws = words if limit is None else words[:limit] + [w for w in words if w in pmlits]
    for w in ws:
        for name, f, r in (('modop', lambda: modop(w, pa), lambda: modop_ref(w)), ('mulopt', lambda: mulopt(w, pc_), lambda: mulopt_ref(w))):
            n += 1
            try: got = f()
            except Stop as e: got = {'stop': str(e)}
            want = r()
            if got != want: bad.append({'frag': name, 'in': hex(w), 'got': {k: (hex(v) if isinstance(v, int) and not isinstance(v, bool) else v) for k, v in got.items()}, 'want': {k: (hex(v) if isinstance(v, int) and not isinstance(v, bool) else v) for k, v in want.items()}})
    bvals = [0, 1, M, 1 << 64, 1 << 128, (1 << 64) - 1, (1 << 128) | 1] + [w for w in words[::37]]
    for exp in range(1, 256):
        for blit in (False, True):
            for bv in (bvals if blit else [0]):
                n += 1
                try: got = mulmod2(exp, blit, bv, pb)
                except Stop as e: got = {'stop': str(e)}
                want = mulmod2_ref(exp, blit, bv)
                if got != want: bad.append({'frag': 'mul_mod2', 'exp': exp, 'blit': blit, 'b': hex(bv), 'got': {k: (hex(v) if isinstance(v, int) else v) for k, v in got.items()}, 'want': {k: (hex(v) if isinstance(v, int) else v) for k, v in want.items()}})
    return n, bad

res = {'seed': 2828, 'operandWords': len(words), 'poolManagerLiterals': len(pmlits),
       'lifted': {
           'modop_optimized<mulmod> 0x3a5eb0': ['3a5f8f-3a5fe2 m==0||m==1', '3a6100-3a6131 popcount(m)==1', '3a633b-3a63ce exp=bit_width(m)-1 (lzcnt chain)', '3a6490-3a64f7 mask m-1 (b==1 arm)', '3a65aa-3a6611 mask m-1 (a==1 arm)'],
           'mul_mod2 0x383b60': ['383c70-383cee, 383f98-383fe6, 384110-38419d, 384410-384437, 384480-38448d, 3842f3-3842fa: mask (1<<exp)-1, last_ix, has_zero loop, inline or runtime decision'],
           'mul_optimized 0x37e260': ['37e340-37e3d0 a==0, sign test, popcount, zero-limb test', '37e528-37e57e negation -a', '37e7fb-37e830 countr_zero loop', '37e897 a_shift[3] != a[3] (read as r15 != r13)']}}
n, bad = campaign()
res['clean'] = {'cases': n, 'mismatches': len(bad), 'records': bad}
print('clean', n, len(bad))
plants = [
    ('modop popcount compare', dict(fault_modop=('3a612d:\tcmp    rax,0x1', '3a612d:\tcmp    rax,0x2'))),
    ('modop exp lzcnt offset', dict(fault_modop=('3a63b0:\tadd    rcx,0x40', '3a63b0:\tadd    rcx,0x41'))),
    ('modop mask borrow', dict(fault_modop=('3a64ad:\tsete   dl', '3a64ad:\tsetne  dl'))),
    ('mul_mod2 last_ix shift', dict(fault_mm2=('384142:\tshr    rax,0x6', '384142:\tshr    rax,0x7'))),
    ('mul_mod2 has_zero', dict(fault_mm2=('384189:\tsete   cl', '384189:\tsetne  cl'))),
    ('mul_optimized negation', dict(fault_mul=('37e566:\tneg    r13', '37e566:\tnot    r13'))),
    ('mul_optimized tzcnt step', dict(fault_mul=('37e822:\tcmp    ecx,0x40', '37e822:\tcmp    ecx,0x3f'))),
]
res['plants'] = []
for name, kw in plants:
    n2, b2 = campaign(limit=400, **kw)
    res['plants'].append({'plant': name, 'cases': n2, 'mismatches': len(b2), 'first': b2[:2]})
    print('plant', name, n2, len(b2))
json.dump(res, open(OUTF, 'w'), indent=1)
