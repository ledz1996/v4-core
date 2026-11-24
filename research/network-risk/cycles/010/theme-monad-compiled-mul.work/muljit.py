"""Instruction level transcription of the multiplication code that Monad's x86 compiler
emits (category-labs/monad v0.16.5, category/vm/compiler/ir/x86/emitter.cpp and
category/vm/runtime/math.S), run on a small model of the x86 registers, memory and the
carry flag.

What is transcribed, with the line ranges of emitter.cpp at v0.16.5:
  mulx, gpr_mul_by_gpq, gpr_mul_by_int32_via_imul, gpr_mul_by_uint64_via_shl,
  gpr_mul_by_uint64, gpr_mul_by_rax_or_uint64          6262-6379
  mul_with_bit_size_by_rax, mul_with_bit_size_and_has_32_bit_by_rax   6381-6463
  MulEmitter (init_mul_dst, mul_sequence, update_dst, compose, emit_loop, emit) 6465-6716
  mul_with_bit_size (register choice, rdx preservation, mask, zeroing)  6720-6981
  mul_optimized                                          6983-7043
  modop_optimized for MULMOD and mul_mod2                7590-7684, 7986-8084
  exp_optimized, the variable exponent with a power of two base        8221-8363
  monad_vm_runtime_mul and monad_vm_runtime_mul_192      math.S
Register allocation is not transcribed as a whole. The caller of a test picks which of the
three 256 bit general register sets ({r12..r15}, {r8..r11}, {rcx,rsi,rdx,rdi}) hold the
operands and which are free, and the transcribed functions then make the choices the C++
makes (which set becomes dst, tmp and spill, when rdx is saved, which limbs are temps).
"""
import random

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1
U256 = 1 << 256
SETS = [['r12', 'r13', 'r14', 'r15'], ['r8', 'r9', 'r10', 'r11'], ['rcx', 'rsi', 'rdx', 'rdi']]
RDX_SET, RDX_IX = 2, 2
COV = {}
def cov(k): COV[k] = COV.get(k, 0) + 1


def limbs(x): return [(x >> (64 * i)) & M64 for i in range(4)]
def join(ls): return sum(v << (64 * i) for i, v in enumerate(ls))
def sx32(i): i &= M32; return (i | (M64 ^ M32)) if i >> 31 else i
def popcount(x): return bin(x).count('1')


class Mem:
    __slots__ = ('addr',)
    def __init__(self, addr): self.addr = addr
    def add(self, k): return Mem(self.addr + k)


class R32:
    __slots__ = ('r',)
    def __init__(self, r): self.r = r


class CPU:
    def __init__(self):
        self.reg = {r: random.getrandbits(64) for r in
                    ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']}
        self.mem = {}
        self.cf = random.getrandbits(1)
        self.stk = []
        self.trace = None

    def rd(self, o, w=64):
        if isinstance(o, str): v = self.reg[o]
        elif isinstance(o, R32): return self.reg[o.r] & M32
        elif isinstance(o, Mem): v = self.mem.get(o.addr, 0)
        else: v = o & M64
        return v & (M32 if w == 32 else M64)

    def wr(self, o, v, w=64):
        if isinstance(o, R32): self.reg[o.r] = v & M32  # 32 bit writes clear the upper half
        elif isinstance(o, str):
            self.reg[o] = (v & M32) if w == 32 else (v & M64)
        else: self.mem[o.addr] = v & M64

    def t(self, *a):
        if self.trace is not None: self.trace.append(a)

    # instructions
    def mov(self, d, s):
        w = 32 if isinstance(d, R32) else 64
        if isinstance(s, int) and not isinstance(d, R32) and isinstance(d, Mem):
            s = sx32(s)  # mov m64, imm32 sign extends
        self.t('mov', d, s); self.wr(d, self.rd(s, w), w)

    def imul2(self, d, s):
        w = 32 if isinstance(d, R32) else 64
        a = self.rd(d, w); b = self.rd(s, w); p = a * b
        self.t('imul', d, s); self.wr(d, p, w); self.cf = random.getrandbits(1)  # CF/OF from signed overflow; modelled as scrambled

    def imul3(self, d, s, imm):
        w = 32 if isinstance(d, R32) else 64
        a = self.rd(s, w); b = (imm & M32) if w == 32 else sx32(imm)
        self.t('imul3', d, s, imm); self.wr(d, a * b, w); self.cf = random.getrandbits(1)

    def shl(self, d, k):
        w = 32 if isinstance(d, R32) else 64
        a = self.rd(d, w)
        self.t('shl', d, k); self.wr(d, a << k, w); self.cf = random.getrandbits(1)

    def xor_self(self, d):
        self.t('xor', d); self.wr(d, 0, 32 if isinstance(d, R32) else 64); self.cf = 0

    def add(self, d, s):
        w = 32 if isinstance(d, R32) else 64; m = M32 if w == 32 else M64
        r = self.rd(d, w) + self.rd(s, w)
        self.t('add', d, s); self.wr(d, r, w); self.cf = int(r > m)

    def adc(self, d, s):
        w = 32 if isinstance(d, R32) else 64; m = M32 if w == 32 else M64
        r = self.rd(d, w) + self.rd(s, w) + self.cf
        self.t('adc', d, s); self.wr(d, r, w); self.cf = int(r > m)

    def mulx(self, hi, lo, s):
        p = self.reg['rdx'] * self.rd(s)
        self.t('mulx', hi, lo, s)
        self.wr(lo, p & M64); self.wr(hi, p >> 64)  # Intel SDM: if hi == lo, hi wins

    def and_imm(self, d, imm):
        if isinstance(d, R32): v = self.rd(d, 32) & (imm & M32); self.wr(d, v, 32)
        else: v = self.rd(d) & sx32(imm); self.wr(d, v)
        self.t('and', d, imm); self.cf = 0

    def and_reg(self, d, s):
        self.t('and', d, s); self.wr(d, self.rd(d) & self.rd(s)); self.cf = 0

    def push(self, r): self.t('push', r); self.stk.append(self.reg[r])
    def pop(self, r): self.t('pop', r); self.reg[r] = self.stk.pop()


def r32(o):
    return R32(o) if isinstance(o, str) else o  # memory operands keep their address; width comes from the register


class Emitter:
    """The parts of monad::vm::compiler::native::Emitter that emit multiplication."""

    def __init__(self, cpu):
        self.c = cpu
        self.gpq = [list(s) for s in SETS]   # gpq256_regs_, may be remapped temporarily

    # --- emitter.cpp 6262-6379 ---
    def mulx_(self, d1, d2, left, right):
        self.c.mov('rdx', left); self.c.mulx(d1, d2, right)

    def gpr_mul_by_gpq(self, is32, dst, left, right):
        self.c.mov(dst, right)
        if is32: self.c.imul2(R32(dst), r32(left))
        else: self.c.imul2(dst, left)

    def gpr_mul_by_int32_via_imul(self, is32, dst, left, right):
        assert right not in (0, 1)
        if is32: self.c.imul3(R32(dst), r32(left), right)
        else: self.c.imul3(dst, left, right)

    def gpr_mul_by_uint64_via_shl(self, is32, dst, left, right):
        assert popcount(right) == 1
        if is32:
            assert right <= M32
            if isinstance(left, str):
                if dst != left or right == 1: self.c.mov(R32(dst), R32(left))
            else: self.c.mov(R32(dst), left)
            if right > 1: self.c.shl(R32(dst), right.bit_length() - 1)
        else:
            if isinstance(left, str):
                if dst != left: self.c.mov(dst, left)
            else: self.c.mov(dst, left)
            if right > 1: self.c.shl(dst, right.bit_length() - 1)

    @staticmethod
    def bounded(x):  # is_uint64_bounded<int32_t>
        i = x - (1 << 64) if x >> 63 else x
        return -(1 << 31) <= i <= (1 << 31) - 1

    def gpr_mul_by_uint64(self, is32, dst, left, pre):
        right = pre & M32 if is32 else pre
        if right == 0: self.c.xor_self(R32(dst))
        elif popcount(right) == 1: self.gpr_mul_by_uint64_via_shl(is32, dst, left, right)
        else:
            assert is32 or self.bounded(right)
            r = right & M32  # memcpy of the low 4 bytes into int32
            self.gpr_mul_by_int32_via_imul(is32, dst, left, r)

    def gpr_mul_by_rax_or_uint64(self, is32, dst, left, i):
        if is32:
            if i is not None:
                self.gpr_mul_by_uint64(True, dst, left, i); return
        elif i is not None and (self.bounded(i) or popcount(i) == 1):
            self.gpr_mul_by_uint64(False, dst, left, i); return
        self.gpr_mul_by_gpq(is32, dst, left, 'rax')

    # --- 6381-6463 ---
    def mul_with_bit_size_by_rax(self, bit_size, dst, left, value_of_rax):
        h = (bit_size & 63) and (bit_size & 63) <= 32
        self.mul_wbs_has32_by_rax(bool(h), bit_size, dst, left, value_of_rax)

    def mul_wbs_has32_by_rax(self, has32, bit_size, dst, left, value_of_rax):
        right = 'rax'
        last_ix = -(-bit_size // 64) - 1
        c = self.c
        def next_pair(i):
            d1 = 'rax' if i == last_ix - 1 else dst[i + 1]
            d2 = dst[0] if i == 0 else 'rdx'
            return d1, d2
        def post_add(i):
            if last_ix == 1:
                if has32: c.add(R32(dst[1]), R32('rax'))
                else: c.add(dst[1], 'rax')
            elif i > 0:
                if i == 1: c.add(dst[1], 'rdx')
                else: c.adc(dst[i], 'rdx')
                if i == last_ix - 1:
                    if has32: c.adc(R32(dst[last_ix]), R32('rax'))
                    else: c.adc(dst[last_ix], 'rax')
        if isinstance(left, list):
            self.gpr_mul_by_rax_or_uint64(has32, dst[last_ix], left[last_ix], value_of_rax)
            for i in range(last_ix):
                d1, d2 = next_pair(i); self.mulx_(d1, d2, left[i], right); post_add(i)
        else:
            mem = left.add(last_ix * 8)
            self.gpr_mul_by_rax_or_uint64(has32, dst[last_ix], mem, value_of_rax)
            mem = mem.add(-last_ix * 8)
            for i in range(last_ix):
                d1, d2 = next_pair(i); self.mulx_(d1, d2, mem, right); post_add(i); mem = mem.add(8)


class MulEmitter:
    """emitter.cpp 6465-6716. right is an int (uint256_t literal), a Mem, or a list (Gpq256)."""

    def __init__(self, bit_size, em, left, right, dst, tmp):
        self.bs = bit_size; self.em = em; self.left = left; self.right = right
        self.dst = dst; self.tmp = tmp; self.init = False

    def rw(self, i):
        return limbs(self.right)[i]

    def init_mul_dst(self, sub, md):
        N = -(-sub // 64)
        if self.init:
            for i in range(N): md[i] = self.tmp[i]
        else:
            c = -(-self.bs // 64); n = 0
            for i in range(c - N, c): md[n] = self.dst[i]; n += 1

    def mul_sequence(self, has32, sub, md):
        em = self.em; c = em.c
        wc = -(-self.bs // 64); N = -(-sub // 64)
        lit = isinstance(self.right, int)
        if lit and self.rw(wc - N) == 1:
            cov('literal-word-one')
            if isinstance(self.left, list):
                i = 0
                for i in range(N - 1): c.mov(md[i], self.left[i])
                i = N - 1
                if has32: c.mov(R32(md[i]), R32(self.left[i]))
                else: c.mov(md[i], self.left[i])
            else:
                lm = self.left; i = 0
                for i in range(N - 1): c.mov(md[i], lm); lm = lm.add(8)
                i = N - 1
                if has32: c.mov(R32(md[i]), lm)
                else: c.mov(md[i], lm)
        elif N > 1:
            if lit:
                x = self.rw(wc - N); c.mov('rax', x); known = x
            elif isinstance(self.right, list):
                c.mov('rax', self.right[wc - N]); known = None
            else:
                c.mov('rax', self.right.add((wc - N) * 8)); known = None
            em.mul_with_bit_size_by_rax(sub, md, self.left, known)
        else:
            L = self.left[0] if isinstance(self.left, list) else self.left
            if lit:
                x = self.rw(wc - N)
                if has32: em.gpr_mul_by_uint64(True, md[0], L, x)
                elif em.bounded(x) or popcount(x) == 1: em.gpr_mul_by_uint64(False, md[0], L, x)
                else: c.mov(md[0], x); c.imul2(md[0], L)
            elif isinstance(self.right, list):
                if has32: c.mov(R32(md[0]), R32(self.right[wc - N])); c.imul2(R32(md[0]), r32(L))
                else: c.mov(md[0], self.right[wc - N]); c.imul2(md[0], L)
            else:
                rm = self.right.add((wc - N) * 8)
                if has32: c.mov(R32(md[0]), rm); c.imul2(R32(md[0]), r32(L))
                else: c.mov(md[0], rm); c.imul2(md[0], L)

    def update_dst(self, has32, sub, md):
        c = self.em.c
        if self.init:
            wc = -(-self.bs // 64); i = wc - (-(-sub // 64)); j = 0
            if has32:
                if i == wc - 1: c.add(R32(self.dst[i]), R32(md[j]))
                else: c.add(self.dst[i], md[j])
                i += 1; j += 1
                while i < wc:
                    if i == wc - 1: c.adc(R32(self.dst[i]), R32(md[j]))
                    else: c.adc(self.dst[i], md[j])
                    i += 1; j += 1
            else:
                c.add(self.dst[i], md[j]); i += 1; j += 1
                while i < wc: c.adc(self.dst[i], md[j]); i += 1; j += 1
        else:
            self.init = True

    def compose(self, has32, sub, md):
        i = -(-self.bs // 64) - (-(-sub // 64))
        if not isinstance(self.right, int) or self.rw(i) != 0:
            self.init_mul_dst(sub, md); self.mul_sequence(has32, sub, md); self.update_dst(has32, sub, md)
        elif not self.init:
            self.em.c.xor_self(R32(self.dst[i]))

    def emit(self):
        h = bool((self.bs & 63) and (self.bs & 63) <= 32)
        md = [None] * 4; sub = self.bs
        while sub > 64: self.compose(h, sub, md); sub -= 64
        self.compose(h, sub, md)


class Alloc:
    """The register file of the virtual stack, reduced to what mul_with_bit_size asks of it.
    occupied: set index -> 'left' | 'right' | 'live' (another element on the EVM stack) | None.
    order: the order in which alloc_general_reg hands out free sets (a test parameter)."""

    def __init__(self, occupied, order):
        self.occ = dict(occupied); self.order = list(order); self.spilled = []

    def free(self):
        return [s for s in self.order if self.occ.get(s) is None]

    def has_free(self): return bool(self.free())

    def alloc(self, cpu, em):
        f = self.free()
        if f:
            s = f[0]
        else:
            # Stack::alloc_general_reg evicts an unreserved element; its value goes to memory
            cand = [s for s in self.order if self.occ.get(s) == 'live']
            assert cand, 'no register can be freed'
            s = cand[0]; self.spilled.append(s)
        self.occ[s] = 'reserved'
        return s


def mul_with_bit_size(cpu, em, al, bit_size, left, right, live_sets, left_mem_addr=0x1000):
    """emitter.cpp 6720-6981.  left: ('reg', set) | ('mem', addr) | ('avx', value).
    right: int literal | ('reg', set) | ('mem', addr).  live_sets: sets whose values must
    survive (other stack elements and the operands that are still live).
    Returns the set index holding the result, or ('lit', 0)."""
    c = cpu
    wc = -(-bit_size // 64)
    rlit = isinstance(right, int)
    assert not (not rlit and right[0] == 'reg' and wc > 2)
    req = 0; needs_mulx = True
    for i in range(wc):
        if not rlit or limbs(right)[i] != 0:
            if req == 0: req = wc; needs_mulx = i != wc - 1
            else: req += wc - i; break
    if req == 0: return ('lit', 0)
    assert wc <= req < 8
    # left placement
    if req > wc:
        if left[0] != 'reg':
            s = al.alloc(c, em)
            v = read_mem(c, left[1]) if left[0] == 'mem' else left[1]
            for i, r in enumerate(em.gpq[s]): c.reg[r] = (v >> (64 * i)) & M64
            al.occ[s] = 'left'; left = ('reg', s)
    else:
        if left[0] == 'avx':
            v = left[1]
            for i in range(4): c.mem[left_mem_addr + 8 * i] = (v >> (64 * i)) & M64
            left = ('mem', left_mem_addr)
    dst = al.alloc(c, em)
    tmp = dst
    if req > 4: tmp = al.alloc(c, em)
    spill_gpq = None
    if needs_mulx and al.has_free():
        s = al.alloc(c, em); spill_gpq = em.gpq[s][RDX_IX]
    pd = pl = pr = ps = False
    rgpq = None
    if not rlit and right[0] == 'reg':
        rgpq = list(em.gpq[right[1]])  # RightMulArg is a copy taken at the call
    if needs_mulx:
        if em.gpq[dst][RDX_IX] == 'rdx':
            assert dst == RDX_SET; pd = True
        if pd:
            if tmp != dst:
                cov('dst-rdx-swapped-with-tmp'); tmp, dst = dst, tmp; pd = False
            else:
                if spill_gpq: cov('dst-rdx-spill'); em.gpq[dst][RDX_IX] = spill_gpq
                else: cov('dst-rdx-rbx'); c.push('rbx'); em.gpq[dst][RDX_IX] = 'rbx'
        else:
            if left[0] == 'reg':
                lg = em.gpq[left[1]]
                if lg[RDX_IX] == 'rdx':
                    if tmp != dst: spill_gpq = em.gpq[tmp][RDX_IX]
                    pl = True
                    cov('left-rdx-' + ('spill' if spill_gpq else 'rbx'))
                    if spill_gpq: c.mov(spill_gpq, 'rdx'); lg[RDX_IX] = spill_gpq
                    else: c.push('rbx'); c.mov('rbx', 'rdx'); lg[RDX_IX] = 'rbx'
            if rgpq is not None and wc > RDX_IX:
                if rgpq[RDX_IX] == 'rdx':
                    assert tmp == dst
                    pr = not pl
                    if pr: c.push('rbx'); c.mov('rbx', 'rdx')
                    rgpq[RDX_IX] = spill_gpq if spill_gpq else 'rbx'
            if not pl and not pr and (RDX_SET in live_sets or al.occ.get(RDX_SET) in ('live', 'right')):
                ps = True; cov('stack-rdx-' + ('spill' if spill_gpq else 'push'))
                if spill_gpq: c.mov(spill_gpq, 'rdx')
                else: c.push('rdx')
    dg = em.gpq[dst]
    left_op = list(em.gpq[left[1]]) if left[0] == 'reg' else Mem(left[1])
    emit_tmp = [None] * 3
    if tmp != dst:
        tg = em.gpq[tmp]; n = 0; i = 0
        while n < wc - 1:
            if i != RDX_IX: emit_tmp[n] = tg[i]; n += 1
            i += 1
    else:
        n = wc; i = 0
        while n < 4 and i < wc - 1:
            emit_tmp[i] = dg[n]; n += 1; i += 1
    rarg = right if rlit else (rgpq if right[0] == 'reg' else Mem(right[1]))
    cov('bits%d-%s-%s-tmp%s' % (bit_size, 'lit' if rlit else right[0], 'reg' if isinstance(left_op, list) else 'mem', 'sep' if tmp != dst else 'dst'))
    MulEmitter(bit_size, em, left_op, rarg, list(dg), emit_tmp).emit()
    if bit_size & 31:
        mask = (1 << (bit_size & 63)) - 1
        if mask.bit_length() <= 32: c.and_imm(R32(dg[wc - 1]), mask)
        else: c.mov('rax', mask); c.and_reg(dg[wc - 1], 'rax')
    for i in range(wc, 4): c.xor_self(R32(dg[i]))
    assert pd + pl + pr + ps <= 1
    if ps:
        if spill_gpq: c.mov('rdx', spill_gpq)
        else: c.pop('rdx')
    elif pd:
        if spill_gpq: c.mov('rdx', spill_gpq); dg[RDX_IX] = 'rdx'
        else: c.mov('rdx', 'rbx'); dg[RDX_IX] = 'rdx'; c.pop('rbx')
    elif pl:
        lg = em.gpq[left[1]]
        if spill_gpq: c.mov('rdx', spill_gpq); lg[RDX_IX] = 'rdx'
        else: c.mov('rdx', 'rbx'); lg[RDX_IX] = 'rdx'; c.pop('rbx')
    elif pr:
        if spill_gpq: c.mov('rdx', spill_gpq)
        else: c.mov('rdx', 'rbx'); c.pop('rbx')
    return dst


def read_set(cpu, s): return join([cpu.reg[r] for r in SETS[s]])
def put_set(cpu, s, v):
    for i, r in enumerate(SETS[s]): cpu.reg[r] = (v >> (64 * i)) & M64
def put_mem(cpu, addr, v):
    for i in range(4): cpu.mem[addr + 8 * i] = (v >> (64 * i)) & M64
def read_mem(cpu, addr): return join([cpu.mem.get(addr + 8 * i, 0) for i in range(4)])


# --- math.S ---
def runtime_mul(cpu, rdi, rsi, rdx_):
    """monad_vm_runtime_mul, instruction by instruction. rdi, rsi, rdx_ are memory addresses."""
    c = cpu; c.reg['rdi'] = rdi; c.reg['rsi'] = rsi; c.reg['rdx'] = rdx_
    m = lambda base, off: Mem(c.reg[base] + off)
    c.push('r13'); c.push('r12')
    c.mov('r8', m('rdx', 0)); c.mov('r9', m('rdx', 8)); c.mov('r10', m('rdx', 16))
    c.mov('rax', m('rsi', 0)); c.mov('r13', 'rax'); c.imul2('r13', m('rdx', 24))
    c.mov('rdx', 'r8'); c.mulx('r11', 'rcx', 'rax')
    c.mov('rdx', 'r9'); c.mulx('r12', 'rdx', 'rax'); c.add('r11', 'rdx')
    c.mov('rdx', 'r10'); c.mulx('rax', 'rdx', 'rax'); c.adc('r12', 'rdx'); c.adc('r13', 'rax')
    c.mov(m('rdi', 0), 'rcx')
    c.mov('rax', m('rsi', 8)); c.imul2('r10', 'rax')
    c.mov('rdx', 'r8'); c.mulx('rcx', 'rdx', 'rax'); c.add('r12', 'rcx'); c.adc('r13', 'r10')
    c.add('r11', 'rdx'); c.mov('rdx', 'r9'); c.mulx('rax', 'rdx', 'rax'); c.adc('r12', 'rdx'); c.adc('r13', 'rax')
    c.mov('rax', m('rsi', 16)); c.imul2('r9', 'rax')
    c.mov('rdx', 'r8'); c.mulx('rax', 'rdx', 'rax'); c.add('r13', 'rax'); c.add('r12', 'rdx'); c.adc('r13', 'r9')
    c.imul2('r8', m('rsi', 24)); c.add('r13', 'r8')
    c.mov(m('rdi', 8), 'r11'); c.mov(m('rdi', 16), 'r12'); c.mov(m('rdi', 24), 'r13')
    c.pop('r12'); c.pop('r13')


def runtime_mul_192(cpu, rdi, rsi, rdx_):
    c = cpu; c.reg['rdi'] = rdi; c.reg['rsi'] = rsi; c.reg['rdx'] = rdx_
    m = lambda base, off: Mem(c.reg[base] + off)
    c.mov('r8', m('rdx', 0)); c.mov('r9', m('rdx', 8)); c.mov('r10', m('rdx', 16))
    c.mov('rax', m('rsi', 0)); c.mov('rdx', 'r8'); c.mulx('r11', 'rcx', 'rax'); c.mov(m('rdi', 0), 'rcx')
    c.mov('rdx', 'r9'); c.mulx('rcx', 'rdx', 'rax'); c.add('r11', 'rdx')
    c.mov('rdx', 'r10'); c.mulx('rax', 'rdx', 'rax'); c.adc('rcx', 'rdx')
    c.mov('rax', m('rsi', 8)); c.mov('rdx', 'r8'); c.mulx('r10', 'rdx', 'rax'); c.add('rcx', 'r10')
    c.add('r11', 'rdx'); c.mov('rdx', 'r9'); c.mulx('rax', 'rdx', 'rax'); c.adc('rcx', 'rdx')
    c.mov('rax', m('rsi', 16)); c.mov('rdx', 'r8'); c.imul2('rdx', 'rax'); c.add('rcx', 'rdx')
    c.mov(m('rdi', 8), 'r11'); c.mov(m('rdi', 16), 'rcx')
