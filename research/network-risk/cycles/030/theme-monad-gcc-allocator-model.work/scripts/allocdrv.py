"""Cycle 30. Run the register bookkeeping of Monad's shipped emitter (monad 0.16.7, gcc 15.2.0 build) in the
cycle 27 x86 model (x86emu.py), together with the non-literal general register shift arms that call it.

Nothing from the package is executed on the CPU. x86emu interprets objdump text of the package; constant data is
read as bytes from the ELF file. The Stack object (Emitter+0x270) is laid out as the gcc code reads it:
  +0x00 free_rc_objects_  +0x0c min_delta_  +0x20 available_stack_offsets_ (std::set<int>, header +0x28, count +0x48)
  +0x50 free_avx_regs_ (vector begin/end/cap)  +0x70 free_general_regs_ (vector begin/end/cap, min-heap of bytes)
  +0x90 avx_reg_stack_elems_[16]  +0x110 general_reg_stack_elems_[3]  +0x128 deferred_comparison_
and every RcObject<StackElem> block as:
  +0x00 refcount  +0x08 StackElem (stack_ ref)  +0x18 stack_indices_ header (count +0x38)  +0x40 avx reserve count
  +0x44 general reserve count  +0x48 StackOffset (engaged +0x50)  +0x54 avx reg (engaged +0x55)
  +0x56 general reg (engaged +0x57)  +0x58 literal (engaged +0x78)
These offsets are the ones the lifted functions read and write (Stack::alloc_general_reg 0x3ad770 initialises
exactly these fields; spill_general_reg 0x3ac870 scores +0x48/+0x70/+0x4d of StackElem).

Lifted from the package (run, not stubbed): the shift functions, test_high_bits192, mov_stack_elem_low64_to_gpq,
volatile_gpq_index, GeneralReg operator==, is_general_reg_on_stack, alloc_or_release_general_reg<>,
Emitter::alloc_general_reg (which emits the spill stores), Stack::alloc_general_reg, Stack::insert_general_reg,
StackElem::insert_general_reg (heap pop), Stack::spill_general_reg() and (StackElem*), StackElem::free_general_reg
(heap push), find_available_stack_offset, insert_stack_offset with the set erase, ~StackElem, free_stack_offset,
free_avx_reg, Stack::release_general_reg and the set insert-position search.
Stubbed by specification: asmjit _emitI (recorded), RoData::add8/add32 (recorded, placed in a model rodata area),
operator new (bump allocator), operator delete (no-op), memcpy, and the three libstdc++ red-black tree routines
(_Rb_tree_increment, _Rb_tree_insert_and_rebalance, _Rb_tree_rebalance_for_erase), whose tree is rebuilt as a
balanced binary search tree over the same nodes; the gcc code itself only walks links and keys.
"""
import sys, os, re, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/theme-monad-gcc-literal-folds.work/scripts')
import emdrv
from emdrv import C, IMG, opdecode, optext, seqtext, GP, GPQREGS, IDN, SIG_GPQ, Stop, Prog, x86emu
M64 = (1 << 64) - 1
FN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'fn')

E = 0x500000000
S = E + 0x270
GPQT = E + 0x3e4
ROD = 0x700000000
HEAP0 = 0x600000000

LIFT = [0x36bc90, 0x39dcb0, 0x3a8180, 0x3aa760, 0x3adf20, 0x36b020, 0x36ae40, 0x3ad770, 0x3ad250, 0x3aac30,
        0x3ac870, 0x3ac7f0, 0x3ab0c0, 0x3ac500, 0x3aa9c0, 0x3aa530, 0x3aa360, 0x3ab4b0, 0x3ab350, 0x3aae30, 0x3adc00,
        0x3aa180]
SHIFT = {'SHL': 0x38e8c0, 'SHR': 0x38c8d0, 'SAR': 0x389c90}


def load_fn(addr, fault=None):
    t = open(os.path.join(FN, '%016x.s' % addr)).read()
    t = '\n'.join(re.sub(r'\s+<.*$', '', l) if l.startswith(' ') else l for l in t.splitlines()) + '\n'
    for old, new in (fault or []):
        assert t.count(old) == 1, (hex(addr), old, t.count(old)); t = t.replace(old, new)
    return t


PC = {}


def prog(fns, faults):
    key = (tuple(fns), repr(sorted(faults.items())))
    if key not in PC:
        PC[key] = Prog(''.join(load_fn(a, faults.get(a)) for a in fns))
    return PC[key]


class Model:
    """One Emitter + Stack state in model memory, with the gcc functions loaded."""
    def __init__(self, entry_fns, faults=None):
        self.faults = faults or {}
        fns = list(entry_fns) + [a for a in LIFT if a not in entry_fns]
        ext = {0x63c6a0: self.e1, 0x63c6e0: self.e2, 0x63c710: self.e3, 0x63c740: self.e4,
               0x3a3ea0: self.add8, 0x375c50: self.add32, 0x6b2e0: self.new, 0x6b1f0: self.delete, 0x6b150: self.memcpy,
               0x131ad0: self.assert_, 0x6b580: self.chk, 0x6c390: self.rb_inc, 0x6c0f0: self.rb_erase,
               0x6c580: self.rb_insert, 0x6b900: self.rb_dec, 0x6b5e0: self.memset}
        self.c = C(prog(fns, self.faults), ext)
        self.heap = HEAP0
        self.emitted = []; self.events = []; self.rod = {}; self.rodoff = 0; self.rodconst = []
        c = self.c
        for r in range(3):
            for l in range(4):
                a = GPQT + 64 * r + 16 * l
                c.write(a, 4, SIG_GPQ); c.write(a + 4, 4, GP.index(GPQREGS[r][l])); c.write(a + 8, 8, 0)
        for off in range(0, 0x140, 8): c.write(S + off, 8, 0)
        self.hdr_init(S + 0x28)
    # ---------- allocation and library stubs ----------
    def alloc(self, n):
        a = self.heap; self.heap += (n + 15) // 16 * 16 + 16
        for i in range(n): self.c.mem[a + i] = 0
        return a
    def new(self, c): c.r['rax'] = self.alloc(c.r['rdi']); self.events.append(('new', c.r['rdi']))
    def delete(self, c): self.events.append(('delete',))
    def memcpy(self, c):
        d, s, n = c.r['rdi'], c.r['rsi'], c.r['rdx']
        for i in range(n): c.mem[d + i] = c.read(s + i, 1)
        c.r['rax'] = d
    def memset(self, c):
        for i in range(c.r['rdx']): c.mem[c.r['rdi'] + i] = c.r['rsi'] & 0xff
        c.r['rax'] = c.r['rdi']
    def assert_(self, c): raise Stop('monad_assertion_failed line %d' % (c.r['rcx'] & 0xffffffff))
    def chk(self, c): raise Stop('stack_chk_fail')
    # red-black tree routines of libstdc++, by specification. Node: +0 color, +8 parent, +0x10 left, +0x18 right, +0x20 key
    def hdr_init(self, h):
        c = self.c; c.write(h, 4, 0); c.write(h + 8, 8, 0); c.write(h + 0x10, 8, h); c.write(h + 0x18, 8, h); c.write(h + 0x20, 8, 0)
    def nodes(self, h):
        out = []
        def walk(n):
            if not n: return
            walk(self.c.read(n + 0x10, 8)); out.append(n); walk(self.c.read(n + 0x18, 8))
        walk(self.c.read(h + 8, 8))
        return out
    def rebuild(self, h, ns):
        c = self.c
        ns = sorted(ns, key=lambda n: self.key(n))
        def build(lo, hi, parent):
            if lo >= hi: return 0
            mid = (lo + hi) // 2; n = ns[mid]
            c.write(n, 4, 1); c.write(n + 8, 8, parent)
            c.write(n + 0x10, 8, build(lo, mid, n)); c.write(n + 0x18, 8, build(mid + 1, hi, n))
            return n
        root = build(0, len(ns), h)
        c.write(h + 8, 8, root)
        c.write(h + 0x10, 8, ns[0] if ns else h); c.write(h + 0x18, 8, ns[-1] if ns else h)
    def key(self, n):
        k = self.c.read(n + 0x20, 4); return k - (1 << 32) if k >> 31 else k
    def keys(self, h): return [self.key(n) for n in self.nodes(h)]
    def rb_inc(self, c):
        x = c.r['rdi']; rd = lambda a: c.read(a, 8)
        if rd(x + 0x18):
            x = rd(x + 0x18)
            while rd(x + 0x10): x = rd(x + 0x10)
        else:
            y = rd(x + 8)
            while x == rd(y + 0x18): x = y; y = rd(y + 8)
            if rd(x + 0x18) != y: x = y
        c.r['rax'] = x
    def rb_dec(self, c):
        x = c.r['rdi']; rd = lambda a: c.read(a, 8)
        if c.read(x, 4) == 0 and rd(rd(x + 8) + 8) == x:
            x = rd(x + 0x18)
        elif rd(x + 0x10):
            y = rd(x + 0x10)
            while rd(y + 0x18): y = rd(y + 0x18)
            x = y
        else:
            y = rd(x + 8)
            while x == rd(y + 0x10): x = y; y = rd(y + 8)
            x = y
        c.r['rax'] = x
    def rb_erase(self, c):
        z, h = c.r['rdi'], c.r['rsi']
        ns = [n for n in self.nodes(h) if n != z]; self.rebuild(h, ns); c.r['rax'] = z
        self.events.append(('rb_erase', self.key(z)))
    def rb_insert(self, c):
        x, h = c.r['rsi'], c.r['rcx']
        ns = self.nodes(h) + [x]; self.rebuild(h, ns); self.events.append(('rb_insert', self.key(x)))
    # ---------- emitter output ----------
    def _emit(self, c, ops):
        iid = c.r['rsi'] & 0xffffffff
        self.emitted.append((IDN.get(hex(iid), hex(iid)).lower(), [opdecode(c, c.r[r]) for r in ops]))
    def e1(self, c): self._emit(c, ['rdx'])
    def e2(self, c): self._emit(c, ['rdx', 'rcx'])
    def e3(self, c): self._emit(c, ['rdx', 'rcx', 'r8'])
    def e4(self, c): self._emit(c, ['rdx', 'rcx', 'r8', 'r9'])
    rod_collide = False
    def _rodata(self, c, data, size, align):
        off = (self.rodoff + align - 1) // align * align
        if self.rod_collide and self.rodconst and len(self.rodconst) > 1:
            # planted fault: a later constant is handed the label of the first one (a deduplication map that
            # treats two different constants as equal); the first constant's bytes stay at that label
            r = c.r['rdi']
            c.write(r, 4, 0x0000000a | (size << 24)); c.write(r + 4, 4, 0x77); c.write(r + 8, 4, 0); c.write(r + 12, 4, 0)
            c.r['rax'] = r; return
        for i, b in enumerate(data): self.rod[off + i] = b
        self.rodoff = off + len(data)
        r = c.r['rdi']
        c.write(r, 4, 0x0000000a | (size << 24)); c.write(r + 4, 4, 0x77); c.write(r + 8, 4, 0); c.write(r + 12, 4, off)
        c.r['rax'] = r
    def add8(self, c):
        x = c.read(c.r['rdx'], 8); self.rodconst.append(('add8', x)); self._rodata(c, x.to_bytes(8, 'little'), 8, 8)
    def add32(self, c):
        x = sum(c.read(c.r['rdx'] + 8 * i, 8) << (64 * i) for i in range(4))
        self.rodconst.append(('add32', x)); self._rodata(c, x.to_bytes(32, 'little'), 8, 32)
    # ---------- building a Stack state ----------
    def set_free_general(self, regs):
        import heapq
        h = list(regs); heapq.heapify(h)
        v = self.alloc(8)
        for i, x in enumerate(h): self.c.write(v + i, 1, x)
        self.c.write(S + 0x70, 8, v); self.c.write(S + 0x78, 8, v + len(h)); self.c.write(S + 0x80, 8, v + 3)
    def set_free_avx(self, regs):
        import heapq
        h = list(regs); heapq.heapify(h)
        v = self.alloc(16)
        for i, x in enumerate(h): self.c.write(v + i, 1, x)
        self.c.write(S + 0x50, 8, v); self.c.write(S + 0x58, 8, v + len(h)); self.c.write(S + 0x60, 8, v + 16)
    def set_available(self, offs):
        ns = []
        for k in offs:
            n = self.alloc(0x28); self.c.write(n + 0x20, 4, k & 0xffffffff); ns.append(n)
        self.rebuild(S + 0x28, ns); self.c.write(S + 0x48, 8, len(ns))
    def elem(self, refs, gen=None, avx=None, stack=None, lit=None, indices=(), resv=0):
        c = self.c; b = self.alloc(0x88)
        c.write(b, 8, refs); c.write(b + 8, 8, S)
        self.hdr_init(b + 0x18)
        ns = []
        for k in indices:
            n = self.alloc(0x28); c.write(n + 0x20, 4, k & 0xffffffff); ns.append(n)
        self.rebuild(b + 0x18, ns); c.write(b + 0x38, 8, len(ns))
        c.write(b + 0x44, 4, resv)
        if stack is not None: c.write(b + 0x48, 4, stack); c.write(b + 0x50, 1, 1)
        if avx is not None:
            c.write(b + 0x54, 1, avx); c.write(b + 0x55, 1, 1); c.write(S + 0x90 + 8 * avx, 8, b + 8)
        if gen is not None:
            c.write(b + 0x56, 1, gen); c.write(b + 0x57, 1, 1); c.write(S + 0x110 + 8 * gen, 8, b + 8)
        if lit is not None:
            for i in range(4): c.write(b + 0x58 + 8 * i, 8, (lit >> (64 * i)) & M64)
            c.write(b + 0x78, 1, 1)
        return b
    # ---------- reading a Stack state ----------
    def loc(self, b):
        c = self.c
        d = {'refs': c.read(b, 8), 'onstack': c.read(b + 0x38, 8)}
        if c.read(b + 0x57, 1): d['gen'] = c.read(b + 0x56, 1)
        if c.read(b + 0x55, 1): d['avx'] = c.read(b + 0x54, 1)
        if c.read(b + 0x50, 1):
            v = c.read(b + 0x48, 4); d['stack'] = v - (1 << 32) if v >> 31 else v
        if c.read(b + 0x78, 1): d['lit'] = sum(c.read(b + 0x58 + 8 * i, 8) << (64 * i) for i in range(4))
        return d
    def permute_rows(self, rnd):
        """Give each row of gpq256_regs_ a random limb order, as earlier blocks can leave it (the clang listing shows
        row 0 as r15, r12, r13, r14 at 0x53a0). The rcx row keeps rcx somewhere in it."""
        for r in range(3):
            regs = list(GPQREGS[r]); rnd.shuffle(regs)
            for l in range(4): self.c.write(GPQT + 64 * r + 16 * l + 4, 4, GP.index(regs[l]))
    def table(self):
        return [[GP[self.c.read(GPQT + 64 * r + 16 * l + 4, 4)] for l in range(4)] for r in range(3)]
    def table_sigs(self):
        return [[self.c.read(GPQT + 64 * r + 16 * l, 16) for l in range(4)] for r in range(3)]
    def free_general(self):
        b, e = self.c.read(S + 0x70, 8), self.c.read(S + 0x78, 8)
        return [self.c.read(a, 1) for a in range(b, e)]
    def gen_table(self): return [self.c.read(S + 0x110 + 8 * i, 8) for i in range(3)]
    def invariants(self, live):
        """The Stack's own bookkeeping must be consistent after the call."""
        bad = []
        fr = self.free_general(); tab = self.gen_table()
        if len(set(fr)) != len(fr): bad.append('free list has a duplicate %r' % fr)
        for r in range(3):
            if tab[r] and r in fr: bad.append('row %d both held and free' % r)
            if not tab[r] and r not in fr: bad.append('row %d neither held nor free' % r)
            if tab[r]:
                d = self.loc(tab[r] - 8)
                if d.get('gen') != r: bad.append('row %d points to an element whose gen is %r' % (r, d.get('gen')))
        # min-heap property of std::priority_queue<.., std::greater<>>
        for i in range(len(fr)):
            for j in (2 * i + 1, 2 * i + 2):
                if j < len(fr) and fr[i] > fr[j]: bad.append('heap order %r' % fr)
        used = set()
        for b in live:
            d = self.loc(b)
            if 'stack' in d:
                if d['stack'] in used: bad.append('two live elements share stack offset %d' % d['stack'])
                used.add(d['stack'])
                if d['stack'] in self.keys(S + 0x28): bad.append('offset %d both used and available' % d['stack'])
        return bad


class SeqCPU(C):
    """C (cycle 29 model) plus the AVX2 dword instructions the non-literal AVX shift arms emit."""
    def _l32(self, o, W): return self._lanes(self.get(self.opnd(o), W), 32, W // 32)
    def i_vpbroadcastd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); x = self.get(self.opnd(o[1])) & 0xffffffff
        self.put(d, self._pack([x] * (W // 32), 32))
    def i_vpmovzxbd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); b = self._lanes(self.get(self.opnd(o[1])), 8, W // 32)
        self.put(d, self._pack(b, 32))
    def i_vpmovsxbd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); b = self._lanes(self.get(self.opnd(o[1])), 8, W // 32)
        self.put(d, self._pack([(x - 256 if x >> 7 else x) & 0xffffffff for x in b], 32))
    def i_vpsubd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._l32(o[1], W); b = self._l32(o[2], W)
        self.put(d, self._pack([(x - y) & 0xffffffff for x, y in zip(a, b)], 32))
    def i_vpsrad(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._l32(o[1], W); c = self.opnd(o[2])
        cnt = c[1] if c[0] == 'i' else self.get(c) & M64; cnt = min(cnt, 31)
        self.put(d, self._pack([((x - (1 << 32) if x >> 31 else x) >> cnt) & 0xffffffff for x in a], 32))
    def i_vpslld(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self._l32(o[1], W); c = self.opnd(o[2])
        cnt = c[1] if c[0] == 'i' else self.get(c) & M64
        self.put(d, self._pack([(x << cnt) & 0xffffffff if cnt < 32 else 0 for x in a], 32))
    def i_vpermd(self, o, pc, n):
        d = self.opnd(o[0]); idx = self._l32(o[1], 256); src = self._l32(o[2], 256)
        self.put(d, self._pack([src[i & 7] for i in idx], 32))
    def i_vpandn(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self.get(self.opnd(o[1]), W); b = self.get(self.opnd(o[2]), W)
        self.put(d, ~a & b & ((1 << W) - 1))
    def i_vpcmpgtd(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); sg = lambda x: x - (1 << 32) if x >> 31 else x
        a = self._l32(o[1], W); b = self._l32(o[2], W)
        self.put(d, self._pack([0xffffffff if sg(x) > sg(y) else 0 for x, y in zip(a, b)], 32))


TAB = [list(r) for r in GPQREGS]     # the register table the next run_seq/word_at use (set from the model)


def gp_of(r):
    return TAB[r]


def seqtext(seq, base=0x1000):
    """emdrv.seqtext, and also for a vector store (memory first, register second): asmjit encodes the memory
    operand of a VEX move by the register width, so the store is 16 or 32 bytes, not the Mem size field."""
    fixed = []
    for mn, ops in seq:
        if mn.startswith('v') and mn not in ('vmovd', 'vmovq') and ops and ops[0][0] == 'mem' and len(ops) > 1 and ops[1][0] == 'vec':
            w = ops[1][2]; ops = [(o[0], o[1], o[2], o[3], w, o[5]) if o[0] == 'mem' else o for o in ops]
        fixed.append((mn, ops))
    return emdrv.seqtext(fixed, base)


def run_seq(m, seq, init, rnd, rbp=0x7fff00000000, rbx=0x7ffe00000000):
    """Run an emitted sequence. init: list of (word, location dict). Returns the CPU."""
    text = seqtext(seq)
    if text not in emdrv.SCACHE: emdrv.SCACHE[text] = Prog(text)
    c = SeqCPU(emdrv.SCACHE[text])
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in m.rod.items(): c.write(ROD + a, 1, b)
    c.r['rbp'] = rbp; c.r['rbx'] = rbx
    for w, d in init:
        L = [(w >> (64 * i)) & M64 for i in range(4)]
        if 'gen' in d:
            for i in range(4): c.r[gp_of(d['gen'])[i]] = L[i]
        if 'avx' in d: c.y[d['avx']] = w
        if 'stack' in d:
            for i in range(4): c.write(rbp + 32 * d['stack'] + 8 * i, 8, L[i])
    rsp0 = None
    c.call(0x1000, [])
    if c.r['rbx'] != rbx: raise Stop('reg_context not restored')
    if c.r['rbp'] != rbp: raise Stop('rbp changed')
    if c.r['rsp'] != 0x7ffff0000000: raise Stop('rsp not balanced')
    return c


def word_at(c, d, rbp=0x7fff00000000):
    out = {}
    if 'gen' in d: out['gen'] = sum(c.r[gp_of(d['gen'])[i]] << (64 * i) for i in range(4))
    if 'avx' in d: out['avx'] = c.y[d['avx']]
    if 'stack' in d: out['stack'] = sum(c.read(rbp + 32 * d['stack'] + 8 * i, 8) << (64 * i) for i in range(4))
    return out
