# RV64IM emulator written from the RISC-V unprivileged specification (RV64I base and the M extension:
# MULHU/MULH/MULHSU high halves, DIV/DIVU by zero giving all ones, REM by zero giving the dividend,
# signed overflow of DIV giving the dividend). Used to run build/ops.elf, the revm-interpreter 42.0.0
# handlers over ruint 1.18.0 compiled for riscv64 with the M extension, the instruction set of the
# SP1 range program on Base. Memory is little-endian.
import struct

M64 = (1 << 64) - 1
RET_MAGIC = 0xDEAD0000


def sx(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) & 1 else v


def s64(v):
    return v - (1 << 64) if v >> 63 else v


class Fault(Exception):
    pass


class Emu:
    def __init__(self, path, faults=()):
        self.faults = set(faults)
        data = open(path, 'rb').read()
        assert data[:4] == b'\x7fELF' and data[4] == 2 and data[5] == 1
        e_phoff, e_shoff = struct.unpack('<QQ', data[32:48])
        e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHHHH', data[54:64])
        self.mem = bytearray(0)
        self.m = {}
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack('<IIQQQQQQ', data[off:off + 56])
            if p_type == 1:
                seg = data[p_offset:p_offset + p_filesz] + b'\0' * (p_memsz - p_filesz)
                for j, b in enumerate(seg):
                    self.m[p_vaddr + j] = b
        self.sym = {}
        shs = [struct.unpack('<IIQQQQIIQQ', data[e_shoff + k * e_shentsize:e_shoff + (k + 1) * e_shentsize]) for k in range(e_shnum)]
        for sh in shs:
            if sh[1] == 2:
                strtab = shs[sh[6]]
                st = data[strtab[4]:strtab[4] + strtab[5]]
                for o in range(sh[4], sh[4] + sh[5], 24):
                    st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack('<IBBHQQ', data[o:o + 24])
                    nm = st[st_name:st.index(b'\0', st_name)].decode()
                    if nm:
                        self.sym[nm] = st_value
        self.steps = 0

    def rd(self, a, n):
        m = self.m
        return sum(m.get(a + i, 0) << (8 * i) for i in range(n))

    def wr(self, a, n, v):
        for i in range(n):
            self.m[a + i] = (v >> (8 * i)) & 0xFF

    def put256(self, a, x):
        for i in range(4):
            self.wr(a + 8 * i, 8, (x >> (64 * i)) & M64)

    def get256(self, a):
        return sum(self.rd(a + 8 * i, 8) << (64 * i) for i in range(4))

    def call(self, fn, a, b, c, limit=2_000_000):
        R = [0] * 32
        base = 0x7000_0000
        self.put256(base, a); self.put256(base + 32, b); self.put256(base + 64, c); self.put256(base + 96, 0)
        R[10], R[11], R[12], R[13] = base, base + 32, base + 64, base + 96
        R[2] = 0x7f00_0000
        R[1] = RET_MAGIC
        R[3] = self.sym.get('__global_pointer$', 0)
        self.run(R, self.sym[fn], limit)
        return self.get256(base + 96)

    def run(self, R, pc, limit):
        m = self.m; F = self.faults
        n = 0
        while pc != RET_MAGIC:
            n += 1
            if n > limit: raise Fault('step limit')
            insn = m.get(pc, 0) | (m.get(pc + 1, 0) << 8) | (m.get(pc + 2, 0) << 16) | (m.get(pc + 3, 0) << 24)
            if insn & 3 != 3: raise Fault('compressed instruction at %x' % pc)
            op = insn & 0x7f; rd = (insn >> 7) & 31; f3 = (insn >> 12) & 7; rs1 = (insn >> 15) & 31; rs2 = (insn >> 20) & 31; f7 = insn >> 25
            a = R[rs1]; b = R[rs2]
            npc = pc + 4; v = None
            if op == 0x37: v = sx(insn & 0xFFFFF000, 32) & M64
            elif op == 0x17: v = (pc + sx(insn & 0xFFFFF000, 32)) & M64
            elif op == 0x6f:
                imm = sx(((insn >> 31) << 20) | (((insn >> 12) & 0xff) << 12) | (((insn >> 20) & 1) << 11) | (((insn >> 21) & 0x3ff) << 1), 21)
                v = npc; npc = (pc + imm) & M64
            elif op == 0x67:
                v = npc; npc = (a + sx(insn >> 20, 12)) & M64 & ~1
            elif op == 0x63:
                imm = sx(((insn >> 31) << 12) | (((insn >> 7) & 1) << 11) | (((insn >> 25) & 0x3f) << 5) | (((insn >> 8) & 0xf) << 1), 13)
                if f3 == 0: t = a == b
                elif f3 == 1: t = a != b
                elif f3 == 4: t = s64(a) < s64(b)
                elif f3 == 5: t = s64(a) >= s64(b)
                elif f3 == 6: t = a < b
                elif f3 == 7: t = a >= b
                else: raise Fault('bad branch')
                if t: npc = (pc + imm) & M64
            elif op == 0x03:
                ad = (a + sx(insn >> 20, 12)) & M64
                if f3 == 0: v = sx(self.rd(ad, 1), 8) & M64
                elif f3 == 1: v = sx(self.rd(ad, 2), 16) & M64
                elif f3 == 2: v = sx(self.rd(ad, 4), 32) & M64
                elif f3 == 3: v = self.rd(ad, 8)
                elif f3 == 4: v = self.rd(ad, 1)
                elif f3 == 5: v = self.rd(ad, 2)
                elif f3 == 6: v = self.rd(ad, 4)
                else: raise Fault('bad load')
            elif op == 0x23:
                ad = (a + sx(((insn >> 25) << 5) | ((insn >> 7) & 31), 12)) & M64
                self.wr(ad, 1 << f3, b)
            elif op == 0x13:
                imm = sx(insn >> 20, 12) & M64; sh = (insn >> 20) & 63
                if f3 == 0: v = (a + imm) & M64
                elif f3 == 2: v = int(s64(a) < s64(imm))
                elif f3 == 3: v = int(a < imm)
                elif f3 == 4: v = a ^ imm
                elif f3 == 6: v = a | imm
                elif f3 == 7: v = a & imm
                elif f3 == 1: v = (a << sh) & M64
                elif f3 == 5: v = (s64(a) >> sh) & M64 if (insn >> 30) & 1 else a >> sh
            elif op == 0x1b:
                imm = sx(insn >> 20, 12); sh = (insn >> 20) & 31
                if f3 == 0: v = sx(a + imm, 32) & M64
                elif f3 == 1: v = sx(a << sh, 32) & M64
                elif f3 == 5: v = (sx(a, 32) >> sh) & M64 if (insn >> 30) & 1 else sx((a & 0xFFFFFFFF) >> sh, 32) & M64
                else: raise Fault('bad op-imm-32')
            elif op == 0x33:
                if f7 == 1:
                    if f3 == 0: v = (a * b) & M64
                    elif f3 == 1: v = ((s64(a) * s64(b)) >> 64) & M64
                    elif f3 == 2: v = ((s64(a) * b) >> 64) & M64
                    elif f3 == 3:
                        v = ((a * b) >> 64) & M64
                        if 'mulhu_carry' in F and a >> 63 and b >> 63: v ^= 1
                    elif f3 == 4: v = M64 if b == 0 else (a if (a == 1 << 63 and b == M64) else (int(abs(s64(a)) // abs(s64(b))) * (1 if (s64(a) < 0) == (s64(b) < 0) else -1)) & M64)
                    elif f3 == 5: v = M64 if b == 0 else a // b
                    elif f3 == 6:
                        if b == 0: v = a
                        elif a == 1 << 63 and b == M64: v = 0
                        else:
                            q = abs(s64(a)) // abs(s64(b)); q = q if (s64(a) < 0) == (s64(b) < 0) else -q
                            v = (s64(a) - q * s64(b)) & M64
                    elif f3 == 7: v = a if b == 0 else a % b
                else:
                    sh = b & (31 if 'sll5' in F else 63)
                    if f3 == 0: v = (a - b) & M64 if f7 == 0x20 else (a + b) & M64
                    elif f3 == 1: v = (a << sh) & M64
                    elif f3 == 2: v = int(s64(a) < s64(b))
                    elif f3 == 3: v = int(a < b)
                    elif f3 == 4: v = a ^ b
                    elif f3 == 5: v = (s64(a) >> (b & 63)) & M64 if f7 == 0x20 else a >> (b & 63)
                    elif f3 == 6: v = a | b
                    elif f3 == 7: v = a & b
            elif op == 0x3b:
                if f7 == 1:
                    x, y = sx(a, 32), sx(b, 32)
                    if f3 == 0: v = sx(x * y, 32) & M64
                    elif f3 == 5: v = M64 if (b & 0xFFFFFFFF) == 0 else sx((a & 0xFFFFFFFF) // (b & 0xFFFFFFFF), 32) & M64
                    elif f3 == 7: v = sx(a, 32) & M64 if (b & 0xFFFFFFFF) == 0 else sx((a & 0xFFFFFFFF) % (b & 0xFFFFFFFF), 32) & M64
                    else: raise Fault('unsupported M-32 %d' % f3)
                else:
                    sh = b & 31
                    if f3 == 0: v = sx(a - b, 32) & M64 if f7 == 0x20 else sx(a + b, 32) & M64
                    elif f3 == 1: v = sx(a << sh, 32) & M64
                    elif f3 == 5: v = (sx(a, 32) >> sh) & M64 if f7 == 0x20 else sx((a & 0xFFFFFFFF) >> sh, 32) & M64
                    else: raise Fault('bad op-32')
            else:
                raise Fault('unsupported opcode %x at %x' % (op, pc))
            if v is not None and rd:
                R[rd] = v
            pc = npc
        self.steps += n
