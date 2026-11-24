"""Instruction level transcription of the code Monad's x86 compiler (category-labs/monad v0.16.5)
emits for the settlement opcodes that it does not hand to a shared runtime helper, run on a
byte addressed model of x86 registers, memory and the flags they use.

Transcribed, with the file and lines of v0.16.5 that were read:
  Emitter::calldataload                     compiler/ir/x86/emitter.cpp 3155-3258
  Emitter::is_bounded_by_bits<32>           emitter.cpp (template, the four operand locations)
  monad_vm_runtime_load_bounded_le_raw      runtime/transmute.S 22-118
  Emitter::bswap_to_ymm                     emitter.cpp 2238-2262
  Emitter::read_context_address (CALLER)    emitter.cpp 3816-3835
  Emitter::read_context_word (CALLVALUE)    emitter.cpp 3862-3865 -> read_mem_be 2269-2281,
                                            mov_mem_be_to_general_reg, mov_mem_be_to_avx_reg
  Emitter::read_context_uint32_to_word      emitter.cpp 3876-3892 (RETURNDATASIZE, CALLDATASIZE)
  RuntimeImpl::pass / call_impl / mov_arg   emitter.cpp 443-590 (argument and result slots of
                                            every runtime helper call: KECCAK256, TLOAD, TSTORE,
                                            CALLDATACOPY, RETURNDATACOPY, MCOPY, CALL, STATICCALL)
The general register sets are {r12..r15}, {r8..r11}, {rcx,rsi,rdx,rdi} (emitter.cpp 608);
reg_context is rbx (emitter.cpp 77).
"""
import random

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1
U = 1 << 256
SETS = [['r12', 'r13', 'r14', 'r15'], ['r8', 'r9', 'r10', 'r11'], ['rcx', 'rsi', 'rdx', 'rdi']]
VOLATILE = 2
COV = {}
def cov(k): COV[k] = COV.get(k, 0) + 1
def s64(v): v &= M64; return v - (1 << 64) if v >> 63 else v


class CPU:
    """Registers hold unsigned 64 bit values, ymm registers 256 bit integers (lane 0 lowest),
    memory is a dict of bytes. Unwritten memory reads as a fixed pseudo random byte so that a
    read outside the intended buffer changes the result."""
    def __init__(self, rng):
        self.rng = rng
        self.r = {k: rng.getrandbits(64) for k in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp',
                                                     'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']}
        self.y = {i: rng.getrandbits(256) for i in range(16)}
        self.mem = {}
        self.zf = rng.getrandbits(1); self.sf = 0; self.of = 0; self.cf = 0
        self.oob = set()  # addresses read that were never written

    def rb(self, a):
        if a not in self.mem:
            self.oob.add(a)
            return (a * 0x9E3779B1 >> 7) & 0xff
        return self.mem[a]

    def ld(self, a, n): return sum(self.rb(a + i) << (8 * i) for i in range(n))
    def st(self, a, v, n):
        for i in range(n): self.mem[a + i] = (v >> (8 * i)) & 0xff
    def put(self, a, bs):
        for i, b in enumerate(bs): self.mem[a + i] = b

    # flag setting arithmetic on 64 bit values
    def sub(self, d, v):
        a = self.r[d]; res = (a - v) & M64
        self.cf = int(a < (v & M64)); self.zf = int(res == 0); self.sf = res >> 63
        self.of = int(((a ^ v) & (a ^ res)) >> 63 & 1); self.r[d] = res
    def cmp(self, d, v):
        a = self.r[d]; res = (a - (v & M64)) & M64
        self.cf = int(a < (v & M64)); self.zf = int(res == 0); self.sf = res >> 63
        self.of = int(((a ^ v) & (a ^ res)) >> 63 & 1)
    def jl(self): return self.sf != self.of
    def jg(self): return self.zf == 0 and self.sf == self.of
    def je(self): return self.zf == 1
    def logic(self, res):
        self.zf = int(res == 0); self.sf = res >> 63 & 1; self.cf = 0; self.of = 0


def bswap256(v): return int.from_bytes(v.to_bytes(32, 'little'), 'big')


def vpermq(v, imm):
    q = [(v >> (64 * i)) & M64 for i in range(4)]
    return sum(q[(imm >> (2 * i)) & 3] << (64 * i) for i in range(4))


def vpshufb(v, ctl):
    b = v.to_bytes(32, 'little'); c = ctl.to_bytes(32, 'little'); out = bytearray(32)
    for lane in (0, 16):
        for i in range(16):
            k = c[lane + i]
            out[lane + i] = 0 if k & 0x80 else b[lane + (k & 15)]
    return int.from_bytes(out, 'little')


BSWAP_CTL = sum(x << (64 * i) for i, x in enumerate([0x0001020304050607, 0x08090a0b0c0d0e0f,
                                                      0x0001020304050607, 0x08090a0b0c0d0e0f]))


def bswap_to_ymm(src):
    """emitter.cpp 2238-2262: vpermq dst, src, 27 then vpshufb with the rodata table."""
    return vpshufb(vpermq(src, 27), BSWAP_CTL)


def load_bounded_le_raw(cpu):
    """transmute.S 22-118. In: rdi pointer, rsi signed size (<= 32). Out: ymm15.
    VEX encoded 128 bit writes clear bits 128..255 of the ymm register."""
    rdi, rsi = cpu.r['rdi'], s64(cpu.r['rsi'])
    if rsi > 16:
        cov('lb.g16')
        x14 = cpu.ld(rdi, 16)                                      # vmovups xmm14,[rdi]
        rdx = cpu.ld(rdi + rsi - 16, 8)                            # mov rdx,[rdi+rsi-16]
        rd2 = cpu.ld(rdi + rsi - 8, 8)                             # mov rdi,[rdi+rsi-8]
        rcx = 0                                                    # xor ecx,ecx
        if rsi < 25:                                               # cmp rsi,25 ; cmovb x2 (unsigned below)
            rdx = rd2; rd2 = rcx
        ecx = ((32 - rsi) & M32) << 3 & M32                        # mov ecx,32; sub ecx,esi; shl ecx,3
        cl = ecx & 63                                              # shrd r64 masks the count to 6 bits
        if cl: rdx = ((rdx >> cl) | (rd2 << (64 - cl))) & M64      # shrd rdx,rdi,cl
        rd2 = rd2 >> (ecx & 63)                                    # shrx rdi,rdi,rcx (count mod 64)
        x15 = rdx | (rd2 << 64)                                    # vmovq ; vpinsrq
        cpu.y[15] = x14 | (x15 << 128)                             # vinserti128 ymm15,ymm14,xmm15,1
        cpu.y[14] = x14
    elif rsi > 8:
        cov('lb.g8')
        lo = cpu.ld(rdi, 8)
        rdx = cpu.ld(rdi + rsi - 8, 8)
        ecx = ((16 - rsi) << 3) & M32
        rdx = rdx >> (ecx & 63)
        cpu.y[15] = lo | (rdx << 64)
    elif rsi > 4:
        cov('lb.g4')
        lo = cpu.ld(rdi, 4)
        edx = cpu.ld(rdi + rsi - 4, 4)
        ecx = ((8 - rsi) << 3) & M32
        edx = edx >> (ecx & 31)                                    # shrx r32 masks the count to 5 bits
        cpu.y[15] = lo | (edx << 32)
    elif rsi > 2:
        cov('lb.g2')
        edx = cpu.ld(rdi, 2)
        edi = cpu.ld(rdi + rsi - 2, 2)
        ecx = ((4 - rsi) << 3) & M32
        edi = (edi >> (ecx & 31)) << 16 & M32
        cpu.y[15] = edx | edi
    elif rsi == 2:
        cov('lb.e2'); cpu.y[15] = cpu.ld(rdi, 2)
    elif rsi == 1:
        cov('lb.e1'); cpu.y[15] = cpu.ld(rdi, 1)
    else:
        cov('lb.le0'); cpu.y[15] = 0


CTX = 0x7000_0000                 # rbx
OFF_INPUT_DATA, OFF_INPUT_SIZE = 0x40, 0x48
OFF_SENDER, OFF_VALUE, OFF_RDSIZE = 0x100, 0x140, 0x180
STACK = 0x5000_0000               # rbp, the EVM stack slots, 32 bytes each
RODATA = 0x6000_0000


def is_bounded32(cpu, loc, val, live):
    """Emitter::is_bounded_by_bits<32>. Returns ('skip',) or ('lit', v) or ('reg', name)."""
    mask = M64 ^ M32
    if loc == 'lit':
        cov('ib.lit')
        if val >= 1 << 32: return ('skip',)
        return ('lit', val)
    if loc == 'gpr':
        g = SETS[live[1]]
        for i in range(4): cpu.r[g[i]] = (val >> (64 * i)) & M64
        if live[0]:
            cov('ib.gpr.live')
            rax = cpu.r[g[0]] & mask
            rax |= cpu.r[g[1]]; rax |= cpu.r[g[2]]; rax |= cpu.r[g[3]]
            cpu.r['rax'] = rax; cpu.logic(rax)
            if not cpu.zf: return ('skip',)
            return ('reg', g[0])
        cov('ib.gpr.dead')
        cpu.r['rax'] = cpu.r[g[0]]
        cpu.r[g[0]] &= mask
        cpu.r[g[3]] |= cpu.r[g[2]]
        cpu.r[g[1]] |= cpu.r[g[0]]
        cpu.r[g[3]] |= cpu.r[g[1]]; cpu.logic(cpu.r[g[3]])
        if not cpu.zf: return ('skip',)
        return ('reg', 'rax')
    if loc == 'avx':
        cov('ib.avx')
        ymask = (U - 1) ^ M32
        cpu.y[live[1]] = val
        cpu.zf = int((val & ymask) == 0)                          # vptest y, mask
        if not cpu.zf: return ('skip',)
        cpu.r['rax'] = val & M32                                   # vmovd eax, xmm (zero extends)
        return ('reg', 'rax')
    cov('ib.stack')
    a = STACK + 32 * live[1]; cpu.st(a, val, 32)
    rax = cpu.ld(a + 8, 8) | cpu.ld(a + 16, 8) | cpu.ld(a + 24, 8); cpu.logic(rax)
    if not cpu.zf: return ('skip',)
    rax = cpu.ld(a, 8); cpu.r['rax'] = rax
    if rax & mask: return ('skip',)                                # test [mask], rax
    return ('reg', 'rax')


def calldataload(cpu, calldata, offset, loc, live, data_addr=0x1000_0000):
    """Emitter::calldataload, emitter.cpp 3155-3258, then the handler bound in finish_contract
    (emitter.cpp 640-644) and the bswap. Returns the 256 bit word pushed."""
    cpu.put(data_addr, calldata)
    cpu.r['rbx'] = CTX
    cpu.st(CTX + OFF_INPUT_DATA, data_addr, 8); cpu.st(CTX + OFF_INPUT_SIZE, len(calldata), 4)
    result = 0                                                     # vpxor result,result,result
    op = is_bounded32(cpu, loc, offset, live)
    if op[0] == 'skip':
        cov('cdl.skip'); return result
    cpu.r['rdi'] = cpu.ld(CTX + OFF_INPUT_DATA, 8)
    cpu.r['rsi'] = cpu.ld(CTX + OFF_INPUT_SIZE, 4)                 # mov esi, dword: zero extends
    if op[0] == 'lit':
        lit = op[1]
        if lit <= 0x7fffffff:
            if lit != 0:
                cov('cdl.lit.imm')
                cpu.r['rdi'] = (cpu.r['rdi'] + lit) & M64; cpu.sub('rsi', lit)
            else:
                cov('cdl.lit.zero')
        else:
            cov('cdl.lit.rodata')
            cpu.r['rax'] = lit
            cpu.r['rdi'] = (cpu.r['rdi'] + lit) & M64; cpu.sub('rsi', lit)
    else:
        cov('cdl.reg')
        r = cpu.r[op[1]]
        cpu.r['rdi'] = (cpu.r['rdi'] + r) & M64; cpu.sub('rsi', r)
    cpu.cmp('rsi', 32)
    if cpu.jl():
        cov('cdl.bounded')
        load_bounded_le_raw(cpu)
    else:
        cov('cdl.full')
        cpu.y[15] = cpu.ld(cpu.r['rdi'], 32)                       # vmovups ymm15,[rdi]
    return bswap_to_ymm(cpu.y[15])


def spec_calldataload(calldata, offset):
    if offset >= len(calldata): return 0
    return int.from_bytes(calldata[offset:offset + 32].ljust(32, b'\0'), 'big')


def read_context_address(cpu, addr20, deferred):
    """emitter.cpp 3816-3835. Writes the chosen general register set."""
    cpu.r['rbx'] = CTX; cpu.put(CTX + OFF_SENDER, addr20)
    g = SETS[cpu.rng.randrange(3)]
    m = CTX + OFF_SENDER
    cpu.r[g[2]] = int.from_bytes(cpu.ld(m, 4).to_bytes(4, 'little'), 'big')          # movbe r32, m32 (zero extends)
    cpu.r[g[1]] = int.from_bytes(cpu.ld(m + 4, 8).to_bytes(8, 'little'), 'big')      # movbe r64, m64
    cpu.r[g[0]] = int.from_bytes(cpu.ld(m + 12, 8).to_bytes(8, 'little'), 'big')
    cpu.r[g[3]] = 0                                                # mov 0 or xor r32,r32
    return sum(cpu.r[g[i]] << (64 * i) for i in range(4))


def read_context_word(cpu, be32, gpr):
    """emitter.cpp 3862-3865 -> read_mem_be: movbe per limb into a general register set when one is
    free, otherwise bswap_to_ymm from memory into an AVX register."""
    cpu.r['rbx'] = CTX; cpu.put(CTX + OFF_VALUE, be32)
    m = CTX + OFF_VALUE
    if gpr:
        cov('rcw.gpr')
        lim = [0] * 4
        for i in range(4):
            lim[3 - i] = int.from_bytes(cpu.ld(m + 8 * i, 8).to_bytes(8, 'little'), 'big')
        return sum(lim[i] << (64 * i) for i in range(4))
    cov('rcw.avx')
    return bswap_to_ymm(cpu.ld(m, 32))


def read_context_uint32_to_word(cpu, size64):
    """emitter.cpp 3876-3892: mov r32, dword [rbx+off]; the other three limbs set to 0."""
    cpu.r['rbx'] = CTX; cpu.st(CTX + OFF_RDSIZE, size64, 8)
    return cpu.ld(CTX + OFF_RDSIZE, 4)


# ---- SIGNEXTEND with a non literal index, emitter.cpp 4587-4835 and destructive_mov_stack_elem_to_bounded_rax

def bounded_rax(cpu, loc, ix, live, free_gpr):
    """destructive_mov_stack_elem_to_bounded_rax(ix, 31): eax = min(ix, 31)."""
    B = 31
    L = [(ix >> (64 * i)) & M64 for i in range(4)]
    if loc == 'gpr':
        cov('br.gpr.live' if live else 'br.gpr.dead')
        a = L[0] > B; z_eq = None                                  # cmp gpq[0], 31
        if not live:
            g1 = L[0] if a else L[1]                               # cmova gpq[1], gpq[0]
            g2 = L[2] | L[3]; g2 |= g1; zf = g2 == 0
        else:
            rax = L[0] if a else L[1]; rax |= L[2]; rax |= L[3]; zf = rax == 0
        eax = B                                                    # mov eax, 31 (flags kept)
        if zf: eax = L[0] & M32                                    # cmovz eax, gpq[0].r32
        return eax
    if loc == 'avx':
        cov('br.avx')
        zf = (ix & ((U - 1) << 5)) == 0                            # vptest y, ~0 << 5
        eax = ix & M32                                             # vmovd eax, xmm
        if not zf: eax = B                                         # cmovnz eax, 31
        return eax
    cov('br.stack.free' if free_gpr else 'br.stack.nofree')
    rax = L[1] | L[2] | L[3]; zf = rax == 0
    rax = B                                                        # mov eax, 31 zero extends
    if free_gpr:
        q = rax
        if zf: rax = L[0]                                          # cmovz rax, [q0]
        if rax > q: rax = q                                        # cmp rax, q ; cmova eax, q.r32
    else:
        if zf: rax = L[0]
        if rax > B: rax = B
    return rax


SX_MEM = sum(x << (64 * i) for i, x in enumerate([0x06050403020100ff, 0x0e0d0c0b0a090807, 0x161514131211100f, 0x1e1d1c1b1a191817]))


def _bytes(v): return list(v.to_bytes(32, 'little'))
def _int(bs): return int.from_bytes(bytes(b & 0xff for b in bs), 'little')
def _sb(b): return b - 256 if b & 0x80 else b


def signextend_avx(eax, src):
    cov('sx.avx')
    b = eax & 0xff
    dst = [b] * 32                                                 # vmovd ; vpbroadcastb
    d0 = (b | b << 8 | b << 16 | b << 24) >> 2                     # vpsrld xmm, 2 (dword lanes)
    tmp_idx = [d0 & 0xff, (d0 >> 8) & 0xff, (d0 >> 16) & 0xff, (d0 >> 24) & 0xff] * 8   # vpbroadcastd
    s = _bytes(src)
    tmp = []
    for lane in range(8):                                          # vpermd: index = low 3 bits of each dword
        k = (tmp_idx[4 * lane] | tmp_idx[4 * lane + 1] << 8 | tmp_idx[4 * lane + 2] << 16 | tmp_idx[4 * lane + 3] << 24) & 7
        tmp += s[4 * k:4 * k + 4]
    sh = []
    for lane in (0, 16):                                           # vpshufb tmp, tmp, dst
        for i in range(16):
            c = dst[lane + i]
            sh.append(0 if c & 0x80 else tmp[lane + (c & 15)])
    w = []
    for i in range(0, 32, 2):                                      # vpsraw 15
        word = sh[i] | sh[i + 1] << 8
        v = 0xffff if word & 0x8000 else 0
        w += [v & 0xff, v >> 8]
    m = _bytes(SX_MEM)
    mask = [0xff if _sb(dst[i]) > _sb(m[i]) else 0 for i in range(32)]   # vpcmpgtb
    return _int([s[i] if mask[i] & 0x80 else w[i] for i in range(32)])   # vpblendvb dst, tmp, src, mask


def signextend_mem(eax, src):
    cov('sx.mem')
    s = _bytes(src)
    sb = s[eax]                                                    # vpbroadcastb tmp, byte [base + rax]
    w = [0xff if sb & 0x80 else 0] * 32                            # vpsraw 15 on words of equal bytes
    m = _bytes(SX_MEM)
    mask = [0xff if _sb(eax & 0xff) > _sb(m[i]) else 0 for i in range(32)]
    return _int([s[i] if mask[i] & 0x80 else w[i] for i in range(32)])


def signextend_gpr(eax, src):
    cov('sx.gpr')
    S = [(src >> (64 * i)) & M64 for i in range(4)]
    shift = (((-56 + eax * 8) & M32) * -1) & M32 & 63              # lea ; neg ; and 63
    D = [(S[i] << shift) & M64 for i in range(4)]                  # shlx (count mod 64)
    def sarx(v, k): k &= 63; return ((s64(v) >> k) & M64)
    for lim, edge in ((0, 8), (1, 16), (2, 24)):
        below = eax < edge                                         # cmp eax, edge
        if below: D[lim + 1] = D[lim]                              # cmovb dst[l+1], dst[l]
        D[lim] = sarx(D[lim], shift)                               # sarx dst[l], dst[l], shift
        if below: shift = 63                                       # cmovb shift, 63
        if not below: D[lim] = S[lim]                              # cmovae dst[l], src[l]
    D[3] = sarx(D[3], shift)
    return sum(D[i] << (64 * i) for i in range(4))


def spec_signextend(b, x):
    if b >= 31: return x
    bit = 8 * b + 7
    if (x >> bit) & 1: return x | ((U - 1) ^ ((1 << (bit + 1)) - 1))
    return x & ((1 << (bit + 1)) - 1)
