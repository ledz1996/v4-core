# Instruction-level emulator for the subset of MIPS64 that build/ops.elf uses, written from the
# semantics of Cannon's MIPS64Instructions.sol (the on-chain step function of the OP Stack fault proof;
# copy in cycles/012/theme-proof-builds.work/op/MIPS64Instructions.sol): delay slots as cpu.pc/nextPC,
# 6-bit masks on DSLLV/DSRLV/DSRAV, 32-bit ops sign-extended, MOVN/MOVZ testing the whole register,
# DMULTU/DMULT/DDIVU on hi/lo, DCLZ by loop. Memory is big-endian.
# Usage as a module: E=Emu('build/ops.elf'); E.call('evm_mul', a, b, c) -> 256-bit int
import struct

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1
RET_MAGIC = 0xDEAD0000


def sx(v, bits):
    v &= (1 << bits) - 1
    return (v | (M64 ^ ((1 << bits) - 1))) & M64 if v >> (bits - 1) & 1 else v


def s64(v):
    return v - (1 << 64) if v >> 63 else v


class Fault(Exception):
    pass


class Emu:
    def __init__(self, path, faults=()):
        self.faults = set(faults)
        data = open(path, 'rb').read()
        assert data[:4] == b'\x7fELF' and data[4] == 2 and data[5] == 2
        (e_entry, e_phoff, e_shoff) = struct.unpack('>QQQ', data[24:48])
        e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx = struct.unpack('>HHHHH', data[54:64])
        self.mem = {}
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack('>IIQQQQQQ', data[off:off + 56])
            if p_type == 1:
                seg = data[p_offset:p_offset + p_filesz] + b'\0' * (p_memsz - p_filesz)
                for j, b in enumerate(seg):
                    self.mem[p_vaddr + j] = b
        # symbols
        self.sym = {}
        shs = [struct.unpack('>IIQQQQIIQQ', data[e_shoff + k * e_shentsize:e_shoff + (k + 1) * e_shentsize]) for k in range(e_shnum)]
        for k, sh in enumerate(shs):
            if sh[1] == 2:  # SHT_SYMTAB
                strtab = shs[sh[6]]
                st = data[strtab[4]:strtab[4] + strtab[5]]
                for o in range(sh[4], sh[4] + sh[5], 24):
                    st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack('>IBBHQQ', data[o:o + 24])
                    nm = st[st_name:st.index(b'\0', st_name)].decode()
                    if nm:
                        self.sym[nm] = st_value
        self.decode_cache = {}
        self.steps = 0

    # memory helpers (big-endian)
    def rd(self, a, n):
        v = 0
        for i in range(n):
            v = (v << 8) | self.mem.get(a + i, 0)
        return v

    def wr(self, a, n, v):
        for i in range(n):
            self.mem[a + i] = (v >> (8 * (n - 1 - i))) & 0xFF

    def put256(self, a, x):
        for i in range(4):
            self.wr(a + 8 * i, 8, (x >> (64 * i)) & M64)

    def get256(self, a):
        return sum(self.rd(a + 8 * i, 8) << (64 * i) for i in range(4))

    def call(self, fn, a, b, c, limit=2_000_000):
        R = [0] * 32
        base = 0x7000_0000
        self.put256(base, a); self.put256(base + 32, b); self.put256(base + 64, c); self.put256(base + 96, 0)
        R[4], R[5], R[6], R[7] = base, base + 32, base + 64, base + 96
        R[29] = 0x7f00_0000
        R[31] = RET_MAGIC
        R[25] = self.sym[fn]
        R[28] = self.sym.get('_gp', 0)
        self.run(R, self.sym[fn], limit)
        return self.get256(base + 96)

    def run(self, R, pc, limit):
        npc = pc + 4
        hi = lo = 0
        mem = self.mem
        F = self.faults
        n = 0
        while True:
            if pc == RET_MAGIC:
                self.steps += n
                return
            n += 1
            if n > limit:
                raise Fault('step limit')
            insn = (mem.get(pc, 0) << 24) | (mem.get(pc + 1, 0) << 16) | (mem.get(pc + 2, 0) << 8) | mem.get(pc + 3, 0)
            op = insn >> 26
            rsn = (insn >> 21) & 31; rtn = (insn >> 16) & 31; rdn = (insn >> 11) & 31
            sa = (insn >> 6) & 31; fun = insn & 63
            imm = insn & 0xFFFF
            simm = sx(imm, 16)
            rs = R[rsn]; rt = R[rtn]
            nxt = npc + 4
            dest = None; val = 0
            if op == 0:
                if fun == 0x00: dest, val = rdn, sx((rt << sa) & M32, 32)
                elif fun == 0x02: dest, val = rdn, sx((rt & M32) >> sa, 32)
                elif fun == 0x03: dest, val = rdn, sx((rt & M32) >> sa, 32 - sa)
                elif fun == 0x04: dest, val = rdn, sx((rt << (rs & 31)) & M32, 32)
                elif fun == 0x06: dest, val = rdn, sx((rt & M32) >> (rs & 31), 32)
                elif fun == 0x07: dest, val = rdn, sx((rt & M32) >> (rs & 31), 32 - (rs & 31))
                elif fun == 0x08:  # jr
                    if npc != pc + 4: raise Fault('jump in delay slot')
                    pc, npc = npc, rs; continue
                elif fun == 0x09:  # jalr
                    if npc != pc + 4: raise Fault('jump in delay slot')
                    if rdn: R[rdn] = (pc + 8) & M64
                    pc, npc = npc, rs; continue
                elif fun == 0x0a:
                    if rt == 0: dest, val = rdn, rs
                elif fun == 0x0b:
                    if 'movn_bit0' in F:
                        if rt & 1: dest, val = rdn, rs
                    elif rt != 0: dest, val = rdn, rs
                elif fun == 0x10: dest, val = rdn, hi
                elif fun == 0x12: dest, val = rdn, lo
                elif fun == 0x11: hi = rs
                elif fun == 0x13: lo = rs
                elif fun == 0x14: dest, val = rdn, (rt << (rs & (31 if 'dsllv5' in F else 63))) & M64
                elif fun == 0x16: dest, val = rdn, rt >> (rs & 63)
                elif fun == 0x17: dest, val = rdn, (s64(rt) >> (rs & 63)) & M64
                elif fun == 0x18:
                    acc = (s64(sx(rs, 32)) * s64(sx(rt, 32))) & M64
                    hi, lo = sx(acc >> 32, 32), sx(acc & M32, 32)
                elif fun == 0x19:
                    acc = (rs & M32) * (rt & M32)
                    hi, lo = sx(acc >> 32, 32), sx(acc & M32, 32)
                elif fun == 0x1c:
                    res = s64(rs) * s64(rt)
                    hi, lo = (res >> 64) & M64, res & M64
                elif fun == 0x1d:
                    res = rs * rt
                    if 'dmultu_hi' in F: res ^= 1 << 64 if (rs & rt) >> 63 else 0
                    hi, lo = (res >> 64) & M64, res & M64
                elif fun == 0x1f:
                    if rt == 0: raise Fault('MIPS64: division by zero')
                    hi, lo = rs % rt, rs // rt
                elif fun == 0x1e:
                    if rt == 0: raise Fault('MIPS64: division by zero')
                    q = abs(s64(rs)) // abs(s64(rt)); q = q if (s64(rs) < 0) == (s64(rt) < 0) else -q
                    r = s64(rs) - q * s64(rt)
                    hi, lo = r & M64, q & M64
                elif fun in (0x20, 0x21): dest, val = rdn, sx(((rs & M32) + (rt & M32)) & M32, 32)
                elif fun in (0x22, 0x23): dest, val = rdn, sx(((rs & M32) - (rt & M32)) & M32, 32)
                elif fun == 0x24: dest, val = rdn, rs & rt
                elif fun == 0x25: dest, val = rdn, rs | rt
                elif fun == 0x26: dest, val = rdn, rs ^ rt
                elif fun == 0x27: dest, val = rdn, (~(rs | rt)) & M64
                elif fun == 0x2a: dest, val = rdn, int(s64(rs) < s64(rt))
                elif fun == 0x2b: dest, val = rdn, int(rs < rt)
                elif fun in (0x2c, 0x2d): dest, val = rdn, (rs + rt) & M64
                elif fun in (0x2e, 0x2f): dest, val = rdn, (rs - rt) & M64
                elif fun == 0x38: dest, val = rdn, (rt << sa) & M64
                elif fun == 0x3a: dest, val = rdn, rt >> sa
                elif fun == 0x3b: dest, val = rdn, (s64(rt) >> sa) & M64
                elif fun == 0x3c: dest, val = rdn, (rt << (sa + 32)) & M64
                elif fun == 0x3e: dest, val = rdn, rt >> (sa + 32)
                elif fun == 0x3f: dest, val = rdn, (s64(rt) >> (sa + 32)) & M64
                else: raise Fault('invalid SPECIAL %x at %x' % (fun, pc))
            elif op == 0x1c:  # SPECIAL2
                if fun == 0x2: dest, val = rdn, sx(((s64(sx(rs, 32)) * s64(sx(rt, 32))) & M32), 32)
                elif fun in (0x24, 0x25):
                    x = (~rs) & M64 if fun == 0x24 else rs
                    i = 0
                    while x & (1 << 63):
                        i += 1; x = (x << 1) & M64
                    dest, val = rdn, i
                elif fun in (0x20, 0x21):
                    x = (~rs) & M64 if fun == 0x20 else rs
                    i = 0
                    while x & 0x80000000:
                        i += 1; x = (x << 1) & M64
                    dest, val = rdn, i
                else: raise Fault('invalid SPECIAL2 %x at %x' % (fun, pc))
            elif op in (2, 3):  # j, jal
                if npc != pc + 4: raise Fault('jump in delay slot')
                tgt = (npc & ~0x0FFFFFFF & M64) | ((insn & 0x03FFFFFF) << 2)
                if op == 3: R[31] = (pc + 8) & M64
                pc, npc = npc, tgt; continue
            elif op in (4, 5, 6, 7, 1):
                if npc != pc + 4: raise Fault('branch in delay slot')
                if op == 4: br = rs == rt
                elif op == 5: br = rs != rt
                elif op == 6: br = s64(rs) <= 0
                elif op == 7: br = s64(rs) > 0
                else:
                    if rtn in (0, 0x10): br = s64(rs) < 0
                    elif rtn in (1, 0x11): br = s64(rs) >= 0
                    else: raise Fault('invalid REGIMM %x at %x' % (rtn, pc))
                    if rtn in (0x10, 0x11): R[31] = (pc + 8) & M64
                tgt = (pc + 4 + (simm << 2)) & M64 if br else npc + 4
                pc, npc = npc, tgt; R[0] = 0; continue
            elif op in (0x8, 0x9): dest, val = rtn, sx(((rs & M32) + (simm & M32)) & M32, 32)
            elif op == 0xA: dest, val = rtn, int(s64(rs) < s64(simm))
            elif op == 0xB: dest, val = rtn, int(rs < simm)
            elif op == 0xC: dest, val = rtn, rs & imm
            elif op == 0xD: dest, val = rtn, rs | imm
            elif op == 0xE: dest, val = rtn, rs ^ imm
            elif op == 0xF: dest, val = rtn, sx(imm << 16, 32)
            elif op in (0x18, 0x19): dest, val = rtn, (rs + simm) & M64
            elif op >= 0x20:
                addr = (rs + simm) & M64
                if op == 0x20: dest, val = rtn, sx(self.rd(addr, 1), 8)
                elif op == 0x24: dest, val = rtn, self.rd(addr, 1)
                elif op == 0x21: dest, val = rtn, sx(self.rd(addr, 2), 16)
                elif op == 0x25: dest, val = rtn, self.rd(addr, 2)
                elif op == 0x23: dest, val = rtn, sx(self.rd(addr, 4), 32)
                elif op == 0x27: dest, val = rtn, self.rd(addr, 4)
                elif op == 0x37: dest, val = rtn, self.rd(addr & ~7, 8)
                elif op == 0x28: self.wr(addr, 1, rt)
                elif op == 0x29: self.wr(addr, 2, rt)
                elif op == 0x2b: self.wr(addr, 4, rt)
                elif op == 0x3f: self.wr(addr & ~7, 8, rt)
                else: raise Fault('unsupported load/store %x at %x' % (op, pc))
            else:
                raise Fault('invalid opcode %x at %x' % (op, pc))
            if dest:
                R[dest] = val & M64
            pc, npc = npc, nxt
