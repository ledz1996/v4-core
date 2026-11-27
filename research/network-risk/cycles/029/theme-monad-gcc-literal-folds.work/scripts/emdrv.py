"""Cycle 29. Drive functions of Monad's shipped emitter (monad 0.16.7, gcc 15.2.0 build) in the x86 model of cycle 27
(x86emu.py). Nothing from the package is executed on the CPU: x86emu interprets objdump text, and constant data that
the code loads with rip-relative addressing is read as bytes from the ELF file's PT_LOAD segments.

Calls out of the lifted function go to Python stubs (allocation, reference counting, the deferred comparison) and every
call into asmjit's BaseEmitter::_emitI is recorded with the instruction id and the operands as asmjit stores them
(16-byte Operand_: signature, id, two data words). The recorded list is the emitted sequence.
"""
import sys, os, re, struct
EMU = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/scripts'
sys.path.insert(0, EMU)
import x86emu
from x86emu import CPU, Prog, Stop
import json
M64 = (1 << 64) - 1
BIN = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/dl/p167/data/usr/local/bin/monad'
IDN = json.load(open('/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/out/asmjit-instid-e8c8e2e4.json'))
FN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'fn')


class Img:
    def __init__(self, path):
        self.f = open(path, 'rb')
        h = self.f.read(64)
        assert h[:4] == b'\x7fELF'
        phoff, = struct.unpack_from('<Q', h, 0x20); phentsize, phnum = struct.unpack_from('<HH', h, 0x36)
        self.segs = []
        for i in range(phnum):
            self.f.seek(phoff + i * phentsize); p = self.f.read(56)
            typ, flags, off, va, pa, fsz, msz, al = struct.unpack('<IIQQQQQQ', p)
            if typ == 1: self.segs.append((va, va + fsz, off))
        self.cache = {}
    def byte(self, a):
        for va, end, off in self.segs:
            if va <= a < end:
                pg = (a - va) >> 12
                key = (va, pg)
                if key not in self.cache:
                    self.f.seek(off + (pg << 12)); self.cache[key] = self.f.read(4096)
                return self.cache[key][(a - va) & 4095]
        return None
IMG = Img(BIN)

GP = ['rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi'] + ['r%d' % i for i in range(8, 16)]
def gpname(i, size):
    n = GP[i]
    if size == 8: return n
    if size == 4:
        return {'rax': 'eax', 'rcx': 'ecx', 'rdx': 'edx', 'rbx': 'ebx', 'rsp': 'esp', 'rbp': 'ebp', 'rsi': 'esi', 'rdi': 'edi'}.get(n, n + 'd')
    if size == 2:
        return {'rax': 'ax', 'rcx': 'cx', 'rdx': 'dx', 'rbx': 'bx', 'rsp': 'sp', 'rbp': 'bp', 'rsi': 'si', 'rdi': 'di'}.get(n, n + 'w')
    if size == 1:
        return {'rax': 'al', 'rcx': 'cl', 'rdx': 'dl', 'rbx': 'bl', 'rsi': 'sil', 'rdi': 'dil', 'rbp': 'bpl', 'rsp': 'spl'}.get(n, n + 'b')
    raise Stop('gp size %d' % size)


class C(CPU):
    def __init__(self, prog, externs=None):
        super().__init__(prog, externs); self._nxt = 0
    def read(self, a, n):
        v = 0
        for i in range(n):
            b = self.mem.get(a + i)
            if b is None:
                b = IMG.byte(a + i)
                if b is None: b = 0
            v |= b << (8 * i)
        return v
    def step(self, pc):
        self._nxt = self.p.nxt[pc] if pc in self.p.nxt else 0
        return super().step(pc)
    def ea(self, s):
        if 'rip' in s:
            m = re.match(r'^\[rip([+-]0x[0-9a-f]+)\]$', s.strip())
            if not m: raise Stop('rip form ' + s)
            return (self._nxt + int(m.group(1), 16)) & M64
        return super().ea(s)
    def i_jmp(self, o, pc, n):
        t = int(o[0], 16)
        if t in self.externs:          # a tail call into a stubbed routine: run the stub, then return
            self.externs[t](self)
            return self.i_ret(o, pc, n)
        return t
    # instructions the cycle 27 model lacks
    def i_movabs(self, o, pc, n): self.i_mov(o, pc, n)
    def i_xchg(self, o, pc, n):
        if o == ['ax', 'ax']: return
        raise Stop('xchg')
    def i_movsx(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = s[2]; v = self.get(s, b)
        if v >> (b - 1): v -= 1 << b
        self.put(d, v & ((1 << d[2]) - 1))
    def i_vmovd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); self.put(d, self.get(s) & 0xffffffff)
    def i_vpunpcklqdq(self, o, pc, n):
        d = self.opnd(o[0]); a = self.get(self.opnd(o[1])); b = self.get(self.opnd(o[2]))
        self.put(d, (a & M64) | ((b & M64) << 64))
    def _lanes(self, v, w, k): return [(v >> (w * i)) & ((1 << w) - 1) for i in range(k)]
    def _pack(self, ls, w): return sum(x << (w * i) for i, x in enumerate(ls))
    def _vw(self, d): return 256 if d[0] == 'r' and d[1].startswith('y') else 128
    def i_vpaddd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1])), 32, W // 32); b = self._lanes(self.get(self.opnd(o[2]), W), 32, W // 32)
        self.put(d, self._pack([(x + y) & 0xffffffff for x, y in zip(a, b)], 32))
    def i_vpinsrd(self, o, pc, n):
        d = self.opnd(o[0]); s1 = self.get(self.opnd(o[1])) & ((1 << 128) - 1)
        v = self.get(self.opnd(o[2]), 32) & 0xffffffff; k = int(o[3], 0) & 3
        s1 &= ~(0xffffffff << (32 * k)) & ((1 << 128) - 1)
        self.put(d, s1 | (v << (32 * k)))
    def _shq(self, o, left, arith=False):
        d = self.opnd(o[0]); W = self._vw(d); src = self.get(self.opnd(o[1]), W)
        c = self.opnd(o[2]); cnt = c[1] if c[0] == 'i' else (self.get(c) & M64)
        out = []
        for x in self._lanes(src, 64, W // 64):
            if left: out.append((x << cnt) & M64 if cnt < 64 else 0)
            elif not arith: out.append(x >> cnt if cnt < 64 else 0)
            else:
                sx = x - (1 << 64) if x >> 63 else x; out.append((sx >> min(cnt, 63)) & M64)
        self.put(d, self._pack(out, 64))
    def i_vpsllq(self, o, pc, n): self._shq(o, True)
    def i_vpsrlq(self, o, pc, n): self._shq(o, False)
    def i_cdqe(self, o, pc, n):
        v = self.r['rax'] & 0xffffffff; self.r['rax'] = (v - (1 << 32) if v >> 31 else v) & M64
    def i_popcnt(self, o, pc, n):
        d = self.opnd(o[0]); x = self.get(self.opnd(o[1]), d[2])
        self.cf = self.of = self.sf = 0; self.zf = int(x == 0); self.put(d, bin(x).count('1'))
    def i_vpshufb(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 8, W // 8); b = self._lanes(self.get(self.opnd(o[2]), W), 8, W // 8)
        out = []
        for i in range(W // 8):
            lane = (i // 16) * 16; ctl = b[i]
            out.append(0 if ctl & 0x80 else a[lane + (ctl & 15)])
        self.put(d, self._pack(out, 8))
    def i_vperm2i128(self, o, pc, n):
        d = self.opnd(o[0]); a = self._lanes(self.get(self.opnd(o[1]), 256), 128, 2); b = self._lanes(self.get(self.opnd(o[2]), 256), 128, 2)
        im = int(o[3], 0); src = a + b
        lo = 0 if im & 0x08 else src[im & 3]; hi = 0 if im & 0x80 else src[(im >> 4) & 3]
        self.put(d, lo | (hi << 128))
    def i_vpsraw(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 16, W // 16); c = self.opnd(o[2])
        cnt = c[1] if c[0] == 'i' else self.get(c) & M64; cnt = min(cnt, 15)
        self.put(d, self._pack([((x - (1 << 16) if x >> 15 else x) >> cnt) & 0xffff for x in a], 16))
    def i_vpblendvb(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d)
        a = self._lanes(self.get(self.opnd(o[1]), W), 8, W // 8); b = self._lanes(self.get(self.opnd(o[2]), W), 8, W // 8); m = self._lanes(self.get(self.opnd(o[3]), W), 8, W // 8)
        self.put(d, self._pack([y if k & 0x80 else x for x, y, k in zip(a, b, m)], 8))
    def i_vpsrld(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 32, W // 32); c = self.opnd(o[2])
        cnt = c[1] if c[0] == 'i' else self.get(c) & M64
        self.put(d, self._pack([x >> cnt if cnt < 32 else 0 for x in a], 32))
    def i_vpermps(self, o, pc, n):
        d = self.opnd(o[0]); idx = self._lanes(self.get(self.opnd(o[1]), 256), 32, 8); src = self._lanes(self.get(self.opnd(o[2]), 256), 32, 8)
        self.put(d, self._pack([src[i & 7] for i in idx], 32))
    def i_vpcmpeqd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 32, W // 32); b = self._lanes(self.get(self.opnd(o[2]), W), 32, W // 32)
        self.put(d, self._pack([0xffffffff if x == y else 0 for x, y in zip(a, b)], 32))
    def i_vpinsrb(self, o, pc, n):
        d = self.opnd(o[0]); s1 = self.get(self.opnd(o[1])) & ((1 << 128) - 1); v = self.get(self.opnd(o[2])) & 0xff; k = int(o[3], 0) & 15
        self.put(d, (s1 & ~(0xff << (8 * k))) | (v << (8 * k)))
    def i_vpsubusw(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 16, W // 16); b = self._lanes(self.get(self.opnd(o[2]), W), 16, W // 16)
        self.put(d, self._pack([max(x - y, 0) for x, y in zip(a, b)], 16))
    def i_vpbroadcastq(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); x = self.get(self.opnd(o[1])) & M64
        self.put(d, self._pack([x] * (W // 64), 64))
    def i_vpextrd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.get(self.opnd(o[1])); k = int(o[2], 0) & 3
        self.put(d, (s >> (32 * k)) & 0xffffffff)
    def i_vpermq(self, o, pc, n):
        d = self.opnd(o[0]); a = self._lanes(self.get(self.opnd(o[1]), 256), 64, 4); im = int(o[2], 0)
        self.put(d, self._pack([a[(im >> (2 * i)) & 3] for i in range(4)], 64))
    def i_vblendps(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._lanes(self.get(self.opnd(o[1]), W), 32, W // 32); b = self._lanes(self.get(self.opnd(o[2]), W), 32, W // 32)
        im = int(o[3], 0)
        self.put(d, self._pack([b[i] if (im >> i) & 1 else a[i] for i in range(W // 32)], 32))
    def i_vpcmpgtq(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d)
        sg = lambda x: x - (1 << 64) if x >> 63 else x
        a = self._lanes(self.get(self.opnd(o[1]), W), 64, W // 64); b = self._lanes(self.get(self.opnd(o[2]), W), 64, W // 64)
        self.put(d, self._pack([M64 if sg(x) > sg(y) else 0 for x, y in zip(a, b)], 64))


def load_fn(addr, fault=None):
    t = open(os.path.join(FN, '%016x.s' % addr)).read()
    t = '\n'.join(re.sub(r'\s+<.*$', '', l) if l.startswith(' ') else l for l in t.splitlines()) + '\n'
    if fault:
        old, new = fault
        assert t.count(old) == 1, (old, t.count(old)); t = t.replace(old, new)
    return t


# ---------------- emitter state model ----------------
E = 0x500000000            # Emitter object
GPQT = E + 0x3e4           # gpq256_regs_ (3 x 4 x Operand_ of 16 bytes)
GPQREGS = [['r12', 'r13', 'r14', 'r15'], ['r8', 'r9', 'r10', 'r11'], ['rcx', 'rsi', 'rdx', 'rdi']]
HEAP = 0x600000000
ROD = 0x700000000       # where the stubs of RoData::add* place the emitter's constants for the sequence runs
SIG_GPQ = 0x08000039


def opdecode(c, p):
    sig = c.read(p, 4); idv = c.read(p + 4, 4); d0 = c.read(p + 8, 4); d1 = c.read(p + 12, 4)
    t = sig & 7; size = (sig >> 24) & 0xff
    if t == 1:
        grp = (sig >> 8) & 0xf
        if grp == 0: return ('gp', gpname(idv, size))
        return ('vec', idv, size, grp, sig)
    if t == 2:
        bt = (sig >> 3) & 0x1f; it = (sig >> 8) & 0x1f
        off = d1 if d1 < 1 << 31 else d1 - (1 << 32)
        if bt == 1: base = 'ROD'            # RegType::kLabelTag: the emitter's read-only data label
        elif bt: base = GP[idv]
        else: base = None
        index = GP[d0] if it else None
        return ('mem', base, index, off, size, sig)
    if t == 4:  # asmjit OperandType::kImm; the 64-bit value is stored in the two data words
        return ('imm', d0 | (d1 << 32))
    return ('raw', hex(sig), idv, d0, d1)


PCACHE = {}
SCACHE = {}


class Drv:
    def __init__(self, fns, entry, policy=None, faults=None):
        key = (tuple(fns), tuple(sorted((faults or {}).items())))
        if key not in PCACHE:
            PCACHE[key] = Prog(''.join(load_fn(a, (faults or {}).get(a)) for a in fns))
        self.p = PCACHE[key]; self.entry = entry
        self.policy = policy or {}
        self.emitted = []; self.events = []
        ext = {0x36b800: self.s_nop, 0x3ab4b0: self.s_dtor, 0x3ad360: self.s_alloc_literal,
               0x36b020: self.s_alloc_or_release, 0x36ae40: self.s_alloc_general, 0x63c6e0: self.s_emit2,
               0x63c710: self.s_emit3, 0x63c6a0: self.s_emit1, 0x63c740: self.s_emit4, 0x39acd0: self.s_avx('SHL'),
               0x39bf90: self.s_avx('SHR'), 0x39e1d0: self.s_avx('SAR'), 0x6b580: self.s_fail,
               0x375c50: self.s_add32, 0x3810b0: self.s_add4, 0x3a3ea0: self.s_add8, 0x373800: self.s_add96,
               0x131ad0: self.s_assert, 0x3a3860: self.s_add16, 0x6c480: self.s_memset_chk, 0x39a300: self.s_alloc_or_release,
               0x39a5c0: self.s_alloc_or_release_avx, 0x3977a0: self.s_nop2, 0x3977d0: self.s_nop2,
               0x3abb50: self.s_pop, 0x3abc30: self.s_push, 0x3694d0: self.s_release, 0x3ad410: self.s_push_literal}
        ext.update(self.policy.get('extra', {}))
        self.c = C(self.p, ext)
        for r in range(3):
            for l in range(4):
                a = GPQT + 64 * r + 16 * l
                self.c.write(a, 4, SIG_GPQ); self.c.write(a + 4, 4, GP.index(GPQREGS[r][l])); self.c.write(a + 8, 8, 0)
        self.heap = HEAP
        self.popq = []; self.pushed = []; self.lits = []; self.rodmem = {}; self.rodoff = 0; self.add96 = []
    def table(self):
        return [[opdecode(self.c, GPQT + 64 * r + 16 * l)[1] for l in range(4)] for r in range(3)]
    def elem(self, gen=None, avx=None, stack=None, lit=None):
        a = self.heap; self.heap += 0x100
        c = self.c
        c.write(a, 8, 10)
        if stack is not None: c.write(a + 0x48, 4, stack); c.write(a + 0x50, 1, 1)
        if avx is not None: c.write(a + 0x54, 1, avx); c.write(a + 0x55, 1, 1)
        if gen is not None: c.write(a + 0x56, 1, gen); c.write(a + 0x57, 1, 1)
        if lit is not None:
            for i in range(4): c.write(a + 0x58 + 8 * i, 8, (lit >> (64 * i)) & M64)
            c.write(a + 0x78, 1, 1)
        return a
    # stubs
    def s_pop(self, c):
        el = self.popq.pop(0); c.write(c.r['rdi'], 8, el); c.r['rax'] = c.r['rdi']; self.events.append('pop')
    def s_push(self, c):
        el = c.read(c.r['rsi'], 8); self.pushed.append(el); self.events.append(('push', hex(el)))
    def s_push_literal(self, c):
        lit = sum(c.read(c.r['rsi'] + 8 * i, 8) << (64 * i) for i in range(4))
        self.events.append(('push_literal', lit)); self.pushed.append(('lit', lit))
    def s_release(self, c): self.events.append('release')
    def _rod(self, c, data, size, align=32, line=None):
        off = self.rodoff
        if line is not None:
            if (off & 63) != line: off += 32
        else: off = (off + align - 1) // align * align
        for i, b in enumerate(data): self.rodmem[off + i] = b
        self.rodoff = off + len(data)
        r = c.r['rdi']
        c.write(r, 4, 0x0000000a | (size << 24)); c.write(r + 4, 4, 0x77); c.write(r + 8, 4, 0); c.write(r + 12, 4, off & 0xffffffff)
        c.r['rax'] = r
        return off
    def s_add32(self, c):
        x = sum(c.read(c.r['rdx'] + 8 * i, 8) << (64 * i) for i in range(4))
        self.events.append(('rodata.add32', hex(x))); self._rod(c, x.to_bytes(32, 'little'), 8)
    def s_add4(self, c):
        x = c.r['rdx'] & 0xffffffff; self.events.append(('rodata.add4', x)); self._rod(c, x.to_bytes(4, 'little'), 4, 4)
    def s_add8(self, c):
        x = c.read(c.r['rdx'], 8); self.events.append(('rodata.add8', hex(x))); self._rod(c, x.to_bytes(8, 'little'), 8, 8)
    def s_add96(self, c):
        w = [sum(c.read(c.r[r] + 8 * i, 8) << (64 * i) for i in range(4)) for r in ('rdx', 'rcx', 'r8')]
        line = c.r['r9'] & 0xffffffff
        self.events.append(('rodata.add96', [hex(x) for x in w], line))
        self.add96.append((w, line))
        self._rod(c, b''.join(x.to_bytes(32, 'little') for x in w), 8, line=line)
    def s_assert(self, c): raise Stop('monad_assertion_failed')
    def s_add16(self, c):
        x = c.read(c.r['rdx'], 16); self.events.append(('rodata.add16', hex(x))); self._rod(c, x.to_bytes(16, 'little'), 16, 16)
    def s_memset_chk(self, c):
        # glibc __memset_chk(dst, c, len, dstlen): a library routine, modelled by its specification
        dst, ch, ln, dl = c.r['rdi'], c.r['rsi'] & 0xff, c.r['rdx'], c.r['rcx']
        if ln > dl: raise Stop('memset_chk overflow')
        for i in range(ln): c.mem[dst + i] = ch
        c.r['rax'] = dst; self.events.append(('memset', ch, ln))
    def s_alloc_or_release_avx(self, c):
        v = c.read(c.r['rdx'], 8)
        if self.policy.get('reuse') and c.read(v + 0x55, 1):
            el = v; c.write(c.r['rdx'], 8, 0)
        else:
            el = self.elem(avx=self.policy.get('avxdst', 12))
        self.events.append(('alloc_or_release_avx', el == v)); self._pair(c, el)
    def s_fail(self, c): raise Stop('stack_chk_fail')
    def s_nop(self, c): self.events.append('discharge_deferred_comparison')
    def s_nop2(self, c): self.events.append('reserv_dtor')
    def s_dtor(self, c): self.events.append('dtor')
    def s_alloc_literal(self, c):
        lit = sum(c.read(c.r['rsp'] + 8 * i, 8) << (64 * i) for i in range(4))
        self.events.append(('alloc_literal', lit)); self.lits.append(lit); c.write(c.r['rdi'], 8, 0xdead1000); c.r['rax'] = c.r['rdi']
    def _pair(self, c, el):
        c.write(c.r['rdi'], 8, el); c.write(c.r['rdi'] + 8, 8, el); c.write(el, 8, c.read(el, 8) + 1); c.r['rax'] = c.r['rdi']
    def s_alloc_or_release(self, c):
        v = c.read(c.r['rdx'], 8)
        if self.policy.get('reuse') and c.read(v + 0x57, 1):
            el = v; c.write(c.r['rdx'], 8, 0)
        else:
            el = self.elem(gen=self.policy.get('dst', 0))
        self.events.append(('alloc_or_release', el == v)); self._pair(c, el)
    def s_alloc_general(self, c):
        el = self.elem(gen=self.policy.get('dst', 0)); self.events.append('alloc_general_reg'); self._pair(c, el)
    def s_avx(self, kind):
        def f(c):
            self.events.append(('shift_avx_reg_by_literal', kind, c.r['rdx'] & 0xffffffff)); c.write(c.r['rdi'], 8, 0xdead2000); c.r['rax'] = c.r['rdi']
        return f
    def _emit(self, c, ops):
        iid = c.r['rsi'] & 0xffffffff
        self.emitted.append((IDN.get(hex(iid), hex(iid)).lower(), [opdecode(c, c.r[r]) for r in ops]))
    def s_emit1(self, c): self._emit(c, ['rdx'])
    def s_emit2(self, c): self._emit(c, ['rdx', 'rcx'])
    def s_emit3(self, c): self._emit(c, ['rdx', 'rcx', 'r8'])
    def s_emit4(self, c): self._emit(c, ['rdx', 'rcx', 'r8', 'r9'])
    def run(self, args, maxsteps=200000):
        return self.c.call(self.entry, args, maxsteps=maxsteps)


def optext(op):
    if op[0] == 'gp': return op[1]
    if op[0] == 'imm': return hex(op[1])
    if op[0] == 'mem':
        kw = {1: 'BYTE', 2: 'WORD', 4: 'DWORD', 8: 'QWORD', 16: 'XMMWORD', 32: 'YMMWORD'}.get(op[4], 'QWORD')
        off = op[3]
        if op[1] == 'ROD': b = '0x%x' % (ROD + off); tail = ''
        else: b = op[1]; tail = '%s0x%x' % ('-' if off < 0 else '+', abs(off))
        if op[2]: b += '+%s*1' % op[2]
        return '%s PTR [%s%s]' % (kw, b, tail)
    if op[0] == 'vec':
        return ('xmm%d' if op[2] == 16 else 'ymm%d') % op[1]
    raise Stop('optext %r' % (op,))


def seqtext(seq, base=0x1000):
    out = []
    for i, (mn, ops) in enumerate(seq):
        if mn.startswith('v') and mn not in ('vmovd', 'vmovq') and ops and ops[0][0] == 'vec':
            # asmjit encodes a vector memory operand by the register width; the Mem size field (qword_ptr) is not used
            w = ops[0][2]
            ops = [(o[0], o[1], o[2], o[3], w, o[5]) if o[0] == 'mem' else o for o in ops]
        ts = [optext(o) for o in ops]
        if mn == 'lea': ts = [re.sub(r'^\w+ PTR ', '', t) for t in ts]   # objdump prints the lea source without a size
        out.append('  %x:\t%s %s' % (base + 4 * i, mn.rstrip('_'), ','.join(ts)))
    out.append('  %x:\tret' % (base + 4 * len(seq)))
    return '\n'.join(out) + '\n'
