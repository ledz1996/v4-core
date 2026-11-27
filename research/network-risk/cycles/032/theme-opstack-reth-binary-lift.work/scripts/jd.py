"""Run the shipped legacy jump destination analysis (revm-bytecode analyze_legacy) of an op-reth or base binary
in the x86-64 or AArch64 model, and compare the bitmap and the padded code with the specification and with the
crate source (dl/src/crates/revm-bytecode-*/src/legacy/analysis.rs). Nothing from the binary runs on the CPU.
usage: python3 -I jd.py <config.json> <out.json> [fault]     seed 3203 for generated programs"""
import json, os, random, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from image import image
CFG = json.load(open(sys.argv[1])); OUT = sys.argv[2]; FAULT = sys.argv[3] if len(sys.argv) > 3 else 'none'
IMG, SEGS = image(CFG['bin']); X86 = CFG['arch'] == 'x86'
HEAP, INP, OUTS, VT, SP = 0x60000000, 0x5f000000, 0x5f100000, 0x5f200000, 0x7ff000000000
if X86:
    from x86emu2 import CPU2 as _C, Prog, Stop, rewrite_rip
    class CPU(_C):
        def _rt(self, o):
            if re.match(r'^[a-z][a-z0-9]*$', o[0]):
                v = self.getr(o[0])[0]
                if v in self.externs: return self.externs[v]
                raise Stop('indirect to %x' % v)
        def i_call(self, o, pc, n):
            f = self._rt(o)
            if f: f(self); return n
            return super().i_call(o, pc, n)
        def i_jmp(self, o, pc, n):
            f = self._rt(o)
            if f: f(self); return self.i_ret([], pc, n)
            return super().i_jmp(o, pc, n)
    prog = Prog(rewrite_rip(open(CFG['asm']).read()))
else:
    from a64emu import Prog, Mem, CPU as _A, Stop
    class A64(_A):
        def i_blr(self, o):
            t = self.rr(o[0])
            if t in self.externs: self.externs[t](self); return None
            self.x[30] = self._pc_next; return t
        def i_br(self, o):
            t = self.rr(o[0])
            if t in self.externs: self.externs[t](self); return self.x[30]
            return t
    prog = Prog([open(CFG['asm']).read()])
faults = {}
if FAULT != 'none':
    for a, rep in CFG['faults'][FAULT]:
        faults[int(a, 16)] = rep if X86 else (lambda cpu, mn, ops, rep=rep: (rep[0], rep[1]))
class St: pass
def mk_externs(st):
    def A(cpu, i): return cpu.r[['rdi', 'rsi', 'rdx'][i]] if X86 else cpu.x[i]
    def R(cpu, v):
        if X86: cpu.r['rax'] = v
        else: cpu.x[0] = v
    def rd(cpu, a, n): return cpu.read(a, n) if X86 else cpu.m.read(a, n)
    def wr(cpu, a, n, v): return cpu.write(a, n, v) if X86 else cpu.m.write(a, n, v)
    def alloc(cpu, zero=False):
        n = A(cpu, 0); a = st.heap; st.heap += (n + 63) & ~31; st.allocs.append((a, n))
        if not X86:
            st.mem.add(a, max(n, 1))
        else:
            for i in range(n): cpu.write(a + i, 1, 0xcd if not zero else 0)
        R(cpu, a)
    def alloc_zeroed(cpu): alloc(cpu, True)
    def dealloc(cpu): st.frees.append(A(cpu, 0))
    def memcpy(cpu):
        d, s, n = A(cpu, 0), A(cpu, 1), A(cpu, 2)
        data = [rd(cpu, s + i, 1) for i in range(n)]
        for i, v in enumerate(data): wr(cpu, d + i, 1, v)
        R(cpu, d)
    def memset(cpu):
        d, v, n = A(cpu, 0), A(cpu, 1) & 0xff, A(cpu, 2)
        for i in range(n): wr(cpu, d + i, 1, v)
        R(cpu, d)
    def drop(cpu): st.drops += 1
    def panic(cpu): raise Stop('panic')
    return {'alloc': alloc, 'alloc_zeroed': alloc_zeroed, 'dealloc': dealloc, 'memcpy': memcpy, 'memmove': memcpy,
            'memset': memset, 'drop': drop, 'panic': panic}
FN = int(CFG['fn'], 16)
_b = bytearray(IMG)
for i, slot in enumerate(sorted(int(k, 16) for k in CFG.get('got', {}))):
    _b[slot:slot + 8] = (0xfeed0000 + 16 * i).to_bytes(8, 'little')
IMG2 = bytes(_b); del _b

def run(code):
    st = St(); st.heap = HEAP; st.allocs = []; st.frees = []; st.drops = 0
    K = mk_externs(st)
    ext = {int(k, 16): K[v] for k, v in CFG.get('externs', {}).items()}
    got = {int(k, 16): K[v] for k, v in CFG.get('got', {}).items()}
    for i, (slot, fn) in enumerate(sorted(got.items())):
        ext[0xfeed0000 + 16 * i] = fn
    ext[0xfeedf000] = K['drop']
    img = IMG2
    if X86:
        cpu = CPU(prog, img, len(img), externs=ext, got=got, faults=faults); w = cpu.write; r = cpu.read
    else:
        mem = Mem(img, 0, len(img)); st.mem = mem
        mem.add(INP, 0x40 + len(code) + 64); mem.add(OUTS, 0x100); mem.add(VT, 0x100); mem.add(SP - 0x40000, 0x40000)
        cpu = A64(prog, mem, externs=ext, faults=faults); cpu.x[31] = SP; w = mem.write; r = mem.read
    for i in range(8): w(VT + 8 * i, 8, 0xfeedf000)
    data = INP + 0x40
    for i, b in enumerate(code): w(data + i, 1, b)
    w(INP, 8, VT); w(INP + 8, 8, data); w(INP + 16, 8, len(code)); w(INP + 24, 8, 0)
    if X86: cpu.call(FN, [OUTS, INP])
    else:
        # this build passes the result pointer in x0 and the input in x1 (read from the prologue at the fn address)
        cpu.call(FN, [OUTS, INP])
    lay = CFG['out']
    bm = r(OUTS + int(lay['bitmap'], 16), 8); bits = r(OUTS + int(lay['bits'], 16), 8)
    cp = r(OUTS + int(lay['code_ptr'], 16), 8); cl = r(OUTS + int(lay['code_len'], 16), 8)
    valid = [i for i in range(bits) if (r(bm + i // 8, 1) >> (i % 8)) & 1]
    padded = bytes(r(cp + i, 1) for i in range(cl))
    return valid, bits, padded, cpu.steps

def spec(code):
    v = []; i = 0
    while i < len(code):
        b = code[i]
        if b == 0x5b: v.append(i)
        i += (b - 0x5e) if 0x60 <= b <= 0x7f else 1
    return v
def crate_pad(code):
    it = 0; prev = last = 0; n = len(code)
    while it < n:
        prev = last; last = code[it]
        if last == 0x5b: it += 1
        elif (last - 0x60) & 0xff < 32: it += (last - 0x60) + 2
        else: it += 1
    pad = it - n
    dsx = lambda o: ((o - 0xe6) & 0xff) < 3
    pad += dsx(prev) if last == 0 else 1 + dsx(last)
    return bytes(code) + bytes(pad)

def programs():
    pm = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
    if os.environ.get('SMALLFIRST'): yield 'small', bytes([0x60,1,0x5b,0x00])
    yield 'poolmanager', pm
    rnd = random.Random(3203)
    for k in range(int(os.environ.get('NPREFIX', '60'))):
        yield 'pm-prefix', pm[:rnd.randrange(1, len(pm))]
    for n in range(1, 33):
        yield 'trailing-push%d' % n, bytes([0x5b, 0x5f + n]) + bytes([0x5b] * rnd.randrange(0, n))
    for op in (0x00, 0x5b, 0xe6, 0xe7, 0xe8, 0xe9, 0xe5, 0x60):
        yield 'last-%02x' % op, bytes([0x5b, 0x01, op])
        yield 'prev-%02x-stop' % op, bytes([0x5b, op, 0x00])
    yield 'empty', b''
    for k in range(int(os.environ.get('NRAND', '400'))):
        n = rnd.randrange(1, 300)
        pool = [0x5b] * 6 + list(range(0x5f, 0x80)) + [0, 0x56, 0x57, 0xe6, 0xe7, 0xe8, 0xfe, 0xff, 0x80, 0x9f]
        yield 'random', bytes(rnd.choice(pool) if rnd.random() < .7 else rnd.randrange(256) for _ in range(n))

res = {'config': sys.argv[1], 'fault': FAULT, 'seed': 3203, 'cases': 0, 'mismatches': 0, 'errors': 0, 'records': [], 'steps': 0}
for tag, code in programs():
    res['cases'] += 1
    try:
        valid, bits, padded, steps = run(code); res['steps'] += steps
    except Stop as e:
        res['errors'] += 1; res['records'].append({'tag': tag, 'code': code.hex(), 'error': str(e)}); continue
    sv = spec(code); cp = crate_pad(code)
    ok = valid == sv and bits == len(code) and padded == cp
    if tag == 'poolmanager':
        inpush = sum(1 for i, b in enumerate(code) if b == 0x5b) - len(sv)
        res['poolmanager'] = {'len': len(code), 'accepted': len(valid), 'specAccepted': len(sv), 'jumpdestBytesInPushData': inpush,
                              'paddedLen': len(padded), 'crateLen': len(cp), 'equal': ok}
    if not ok:
        res['mismatches'] += 1
        res['records'].append({'tag': tag, 'code': code.hex(), 'model': valid, 'spec': sv, 'bits': bits,
                               'padded': padded.hex(), 'crate': cp.hex()})
    if FAULT != 'none' and res['mismatches'] + res['errors'] >= 5: break
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], res.get('poolmanager'))
