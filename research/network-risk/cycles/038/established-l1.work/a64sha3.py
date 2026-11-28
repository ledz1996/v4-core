#!/usr/bin/env python3
"""L-1292: run the shipped AArch64 SHA3_absorb and SHA3_squeeze of reth-bsc v0.1.4-hotfix-arm64
("Keccak-1600 absorb and squeeze for ARMv8, CRYPTOGAMS by @dot-asm", iotas at 0x3fe3540) in a small A64 model.

These are the routines the Rust code of the binary calls (54 BL sites to SHA3_absorb at 0x3fe3920, 40 to
SHA3_squeeze at 0x3fe3b00; the _cext variants have no BL caller). The model decodes raw instruction words
from the binary (file offset equals VMA), implements only the classes these routines use and refuses
anything else. Keccak-256 is formed as the Rust wrapper does: whole blocks through SHA3_absorb, the
padded last block through SHA3_absorb, 32 bytes through SHA3_squeeze. The padding step is Python.

Usage: python3 -I a64sha3.py <reth-bsc arm64 binary> <out.json> [n_random_states]
"""
import sys, json, random, struct, hashlib, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/established-l1.work')
from a64keccak import keccak_f, sponge, decode_bitmask, sx, ror, M64

LO, HI = 0x3fe3540, 0x3fe3be0      # iotas, KeccakF1600_int, KeccakF1600, SHA3_absorb, SHA3_squeeze
ABSORB, SQUEEZE, PERM = 0x3fe3920, 0x3fe3b00, 0x3fe3840
SENTINEL = 0xDEAD000
MBASE, MSIZE = 0x7f0000000000, 1 << 20
SP0 = MBASE + 0xF0000
STATE = MBASE + 0x100
INP = MBASE + 0x1000
OUT = MBASE + 0x80000

class A64:
    def __init__(self, blob):
        self.blob = blob; self.cache = {}; self.seen = {}

    def decode(self, pc):
        w = struct.unpack_from('<I', self.blob, pc)[0]
        if w in (0xd503201f, 0xd503233f, 0xd50323bf):       # nop, paciasp, autiasp (PAC modelled as identity)
            return ('nop',)
        if w == 0xd65f03c0:
            return ('ret',)
        top = w >> 24
        if (w >> 24) & 0x1f == 0b01010 and (w >> 31) == 1:
            return ('logsr', (w >> 29) & 3, (w >> 22) & 3, (w >> 21) & 1, (w >> 16) & 31, (w >> 10) & 63, (w >> 5) & 31, w & 31)
        if (w >> 24) & 0x1f == 0b01011 and not (w >> 21) & 1 and (w >> 31) == 1:   # add/sub shifted register
            if (w >> 22) & 3 != 0:
                raise ValueError('shift type in add/sub %08x' % w)
            return ('asr', (w >> 30) & 1, (w >> 29) & 1, (w >> 16) & 31, (w >> 10) & 63, (w >> 5) & 31, w & 31)
        if (w >> 21) == 0b10010011110:
            return ('extr', (w >> 16) & 31, (w >> 10) & 63, (w >> 5) & 31, w & 31)
        if (w >> 23) == 0b110100110 and (w >> 22) & 1:     # UBFM 64 (lsr alias when imms == 63)
            immr, imms = (w >> 16) & 63, (w >> 10) & 63
            if imms != 63:
                raise ValueError('ubfm form %08x' % w)
            return ('lsr', immr, (w >> 5) & 31, w & 31)
        if (w >> 24) & 0x9f == 0b10000:
            return ('adr', w & 31, sx((((w >> 5) & 0x7ffff) << 2) | ((w >> 29) & 3), 21))
        if (w >> 26) == 0b000101:
            return ('b', sx(w & 0x3ffffff, 26) * 4)
        if (w >> 26) == 0b100101:
            return ('bl', sx(w & 0x3ffffff, 26) * 4)
        if top == 0b01010100 and not (w >> 4) & 1:
            return ('bcond', w & 15, sx((w >> 5) & 0x7ffff, 19) * 4)
        if (w >> 30) == 0b10 and (w >> 27) & 7 == 0b101 and not (w >> 26) & 1:
            idx = (w >> 23) & 7
            if idx not in (1, 2, 3):
                raise ValueError('pair form %08x' % w)
            return ('pair', idx, (w >> 22) & 1, sx((w >> 15) & 0x7f, 7) * 8, (w >> 10) & 31, (w >> 5) & 31, w & 31)
        if (w >> 22) & 0x3ff in (0b1111100100, 0b1111100101):
            return ('ldst_u', (w >> 22) & 1, 8, ((w >> 10) & 0xfff) * 8, (w >> 5) & 31, w & 31)
        if (w >> 21) & 0x7ff in (0b11111000000, 0b11111000010, 0b00111000000, 0b00111000010) and (w >> 10) & 3 in (1, 3):
            size = 8 if (w >> 30) == 3 else 1
            return ('ldst_i', (w >> 22) & 1, size, (w >> 10) & 3, sx((w >> 12) & 0x1ff, 9), (w >> 5) & 31, w & 31)
        if (w >> 23) & 0x3f == 0b100010 and (w >> 31) == 1:
            return ('addsub', (w >> 30) & 1, (w >> 29) & 1, ((w >> 10) & 0xfff) << (12 * ((w >> 22) & 1)), (w >> 5) & 31, w & 31)
        if (w >> 23) & 0x1ff == 0b111100100:
            return ('andsi', decode_bitmask((w >> 22) & 1, (w >> 10) & 63, (w >> 16) & 63), (w >> 5) & 31, w & 31)
        raise ValueError('unmodelled instruction %08x at %x' % (w, pc))

    def call(self, entry, args, mem):
        X = [0] * 31
        for i, a in enumerate(args):
            X[i] = a
        sp = SP0
        X[30] = SENTINEL
        for r in range(19, 30):
            X[r] = (0x1111111111111111 * (r - 18)) & M64
        callee = X[19:30]
        N = Z = C = 0
        pc = entry
        steps = 0
        blob = self.blob

        def rd(n): return 0 if n == 31 else X[n]
        def rd_sp(n): return sp if n == 31 else X[n]
        def ld(a, size):
            if MBASE <= a and a + size <= MBASE + MSIZE:
                return int.from_bytes(mem[a - MBASE:a - MBASE + size], 'little')
            if LO <= a and a + size <= HI:
                return int.from_bytes(blob[a:a + size], 'little')
            raise ValueError('load from unmapped %x' % a)
        def st(a, v, size):
            if not (MBASE <= a and a + size <= MBASE + MSIZE):
                raise ValueError('store to unmapped %x' % a)
            mem[a - MBASE:a - MBASE + size] = (v & ((1 << (8 * size)) - 1)).to_bytes(size, 'little')
        while pc != SENTINEL:
            if not (LO + 0xc0 <= pc < HI):
                raise ValueError('pc left the routines: %x' % pc)
            ins = self.cache.get(pc)
            if ins is None:
                ins = self.decode(pc); self.cache[pc] = ins
            k = ins[0]
            self.seen[k] = self.seen.get(k, 0) + 1
            steps += 1
            npc = pc + 4
            if k == 'logsr':
                _, opc, sh, inv, rm, imm6, rn, d = ins
                b = rd(rm)
                if sh == 0: b = (b << imm6) & M64
                elif sh == 1: b = b >> imm6
                elif sh == 2: b = (sx(b, 64) >> imm6) & M64
                else: b = ror(b, imm6)
                if inv: b = (~b) & M64
                a = rd(rn)
                if opc == 0: r = a & b
                elif opc == 1: r = a | b
                elif opc == 2: r = a ^ b
                else:
                    r = a & b; N, Z, C = r >> 63, int(r == 0), 0
                if d != 31: X[d] = r
            elif k == 'asr' or k == 'addsub':
                if k == 'asr':
                    _, op, S, rm, imm6, rn, d = ins
                    a, b = rd(rn), (rd(rm) << imm6) & M64
                else:
                    _, op, S, b, rn, d = ins
                    a = rd_sp(n=rn) if not S else rd_sp(rn)
                if op:
                    r = (a - b) & M64
                    if S: C = int(a >= b)
                else:
                    r = (a + b) & M64
                    if S: C = int(a + b > M64)
                if S:
                    N, Z = r >> 63, int(r == 0)
                    if d != 31: X[d] = r
                else:
                    if d == 31 and k == 'addsub': sp = r
                    elif d != 31: X[d] = r
            elif k == 'extr':
                _, rm, lsb, rn, d = ins
                if d != 31: X[d] = (((rd(rn) << 64) | rd(rm)) >> lsb) & M64
            elif k == 'lsr':
                _, sh, rn, d = ins
                if d != 31: X[d] = rd(rn) >> sh
            elif k == 'adr':
                X[ins[1]] = (pc + ins[2]) & M64
            elif k == 'b':
                npc = pc + ins[1]
            elif k == 'bl':
                X[30] = pc + 4; npc = pc + ins[1]
            elif k == 'bcond':
                c = ins[1]
                if c == 0: t = Z == 1
                elif c == 1: t = Z == 0
                elif c == 3: t = C == 0          # lo
                elif c == 8: t = C == 1 and Z == 0   # hi
                else: raise ValueError('cond %d' % c)
                if t: npc = pc + ins[2]
            elif k == 'ret':
                npc = X[30]
            elif k == 'nop':
                pass
            elif k == 'pair':
                _, idx, L, off, t2, n, t = ins
                base = rd_sp(n)
                addr = base if idx == 1 else (base + off) & M64
                if L:
                    v1, v2 = ld(addr, 8), ld(addr + 8, 8)
                    if t != 31: X[t] = v1
                    if t2 != 31: X[t2] = v2
                else:
                    st(addr, rd(t), 8); st(addr + 8, rd(t2), 8)
                if idx in (1, 3):
                    if n == 31: sp = (base + off) & M64
                    else: X[n] = (base + off) & M64
            elif k == 'ldst_u':
                _, L, size, off, n, t = ins
                addr = (rd_sp(n) + off) & M64
                if L:
                    if t != 31: X[t] = ld(addr, size)
                else:
                    st(addr, rd(t), size)
            elif k == 'ldst_i':
                _, L, size, mode, off, n, t = ins
                base = rd_sp(n)
                addr = base if mode == 1 else (base + off) & M64
                if L:
                    v = ld(addr, size)
                    if t != 31: X[t] = v
                else:
                    st(addr, rd(t), size)
                if n == 31: sp = (base + off) & M64
                else: X[n] = (base + off) & M64
            elif k == 'andsi':
                _, mask, n, d = ins
                r = rd(n) & mask
                N, Z, C = r >> 63, int(r == 0), 0
                if d != 31: X[d] = r
            else:
                raise ValueError(k)
            pc = npc
            if steps > 2000000:
                raise ValueError('runaway')
        if sp != SP0 or X[19:30] != callee:
            raise ValueError('ABI not restored')
        return X[0]

def keccak256_emu(cpu, msg, misalign=0):
    mem = bytearray(MSIZE)
    rate = 136
    inp = INP + misalign
    full = len(msg) - len(msg) % rate
    mem[inp - MBASE:inp - MBASE + full] = msg[:full]
    if full:
        rem = cpu.call(ABSORB, [STATE, inp, full, rate], mem)
        if rem != 0:
            raise ValueError('absorb left %d' % rem)
    last = bytearray(msg[full:]) + b'\x01' + bytes(rate - len(msg) % rate - 1)
    last[-1] |= 0x80
    mem[inp - MBASE:inp - MBASE + rate] = last
    rem = cpu.call(ABSORB, [STATE, inp, rate, rate], mem)
    if rem != 0:
        raise ValueError('absorb left %d' % rem)
    cpu.call(SQUEEZE, [STATE, OUT, 32, rate], mem)
    return bytes(mem[OUT - MBASE:OUT - MBASE + 32])

def perm_emu(cpu, st):
    mem = bytearray(MSIZE)
    mem[STATE - MBASE:STATE - MBASE + 200] = b''.join(struct.pack('<Q', w) for w in st)
    cpu.call(PERM, [STATE], mem)
    return list(struct.unpack_from('<25Q', mem, STATE - MBASE))

def main():
    blob = open(sys.argv[1], 'rb').read()
    out = sys.argv[2]
    n_rand = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    cpu = A64(blob)
    rng = random.Random(1292)
    t0 = time.time()
    res = {'binary_sha256': hashlib.sha256(blob).hexdigest(), 'routines': {'SHA3_absorb': hex(ABSORB), 'SHA3_squeeze': hex(SQUEEZE), 'KeccakF1600': hex(PERM), 'iotas': hex(LO)}, 'checks': {}}
    ref = lambda m: sponge(m, keccak_f)
    assert ref(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    for L in (0, 1, 135, 136, 137, 300):
        m = bytes(rng.getrandbits(8) for _ in range(L))
        assert sponge(m, keccak_f, pad=0x06) == hashlib.sha3_256(m).digest()
    # permutation through KeccakF1600 (the squeeze path)
    bad = 0; shapes = [[rng.getrandbits(64) for _ in range(25)] for _ in range(n_rand)]
    for i in range(25):
        for v in (1, M64, 1 << 63):
            s = [0] * 25; s[i] = v; shapes.append(s)
    shapes += [[0] * 25, [M64] * 25]
    for s in shapes:
        if perm_emu(cpu, s) != keccak_f(list(s)): bad += 1
    res['checks']['permutation'] = {'cases': len(shapes), 'mismatches': bad}
    # Keccak-256 sets
    sets = {}
    def add(name, m, mis=0): sets.setdefault(name, []).append((m, mis))
    for L in range(0, 1101): add('len0-1100', bytes(rng.getrandbits(8) for _ in range(L)))
    for k in range(1, 9):
        for d in (-2, -1, 0, 1, 2): add('boundary', bytes(rng.getrandbits(8) for _ in range(136 * k + d)))
    for L in (32, 58, 64, 136, 160, 200, 272, 300):
        for mis in range(1, 8):
            for _ in range(10): add('unaligned', bytes(rng.getrandbits(8) for _ in range(L)), mis)
    W = lambda v: v.to_bytes(32, 'big')
    for _ in range(300):
        add('poolId160', W(rng.getrandbits(160)) + W(rng.getrandbits(160)) + W(rng.getrandbits(24)) + W(rng.getrandbits(24)) + W(rng.getrandbits(160)))
        add('positionKey58', rng.getrandbits(160).to_bytes(20, 'big') + rng.getrandbits(24).to_bytes(3, 'big') + rng.getrandbits(24).to_bytes(3, 'big') + W(rng.getrandbits(256)))
        add('currencyDelta64', W(rng.getrandbits(160)) + W(rng.getrandbits(160)))
        add('mappingSmallSlot64', W(rng.getrandbits(256)) + W(rng.randrange(0, 7)))
        base = rng.getrandbits(256)
        for off, nm in ((4, 'ticksSlot64'), (5, 'bitmapSlot64'), (6, 'positionsSlot64')):
            add(nm, W(rng.getrandbits(24)) + W((base + off) % (1 << 256)))
        add('erc6909Outer64', W(rng.getrandbits(160)) + W(4))
        add('erc6909Inner64', W(rng.getrandbits(160)) + W(rng.getrandbits(256)))
    for _ in range(14000): add('bulk64', rng.getrandbits(512).to_bytes(64, 'big'))
    for _ in range(8000): add('bulk32', rng.getrandbits(256).to_bytes(32, 'big'))
    tot = 0; totbad = 0
    for name, lst in sets.items():
        b = 0
        for m, mis in lst:
            if keccak256_emu(cpu, m, mis) != ref(m): b += 1
        res['checks']['keccak256:' + name] = {'cases': len(lst), 'mismatches': b}
        tot += len(lst); totbad += b
    res['checks']['keccak256_total'] = {'cases': tot, 'mismatches': totbad}
    # planted faults
    planted = caught = 0
    def faulty(patch):
        b = bytearray(blob); patch(b); return A64(bytes(b))
    m = bytes(rng.getrandbits(8) for _ in range(200))
    for off, bit in ((LO + 8 * 3, 15), (LO + 8 * 23, 63), (LO + 8 * 0, 0)):
        f = faulty(lambda b: b.__setitem__(off + bit // 8, b[off + bit // 8] ^ (1 << (bit % 8))))
        planted += 1; caught += int(keccak256_emu(f, m) != ref(m))
    # change the first rotate amount in KeccakF1600_int and the absorb compare against 0x68
    import re
    dis_rot = None
    for pc in range(0x3fe3600, 0x3fe3830, 4):
        w = struct.unpack_from('<I', blob, pc)[0]
        if (w >> 21) == 0b10010011110:
            dis_rot = pc; break
    def p_rot(b):
        w = struct.unpack_from('<I', b, dis_rot)[0]; lsb = (w >> 10) & 63
        struct.pack_into('<I', b, dis_rot, (w & ~(63 << 10)) | (((lsb + 1) & 63) << 10))
    f = faulty(p_rot); planted += 1; caught += int(keccak256_emu(f, m) != ref(m))
    def p_cmp(b):
        w = struct.unpack_from('<I', b, 0x3fe39ac)[0]   # cmp x30, #0x68 -> #0x60
        struct.pack_into('<I', b, 0x3fe39ac, (w & ~(0xfff << 10)) | (0x60 << 10))
    f = faulty(p_cmp)
    m2 = bytes(rng.getrandbits(8) for _ in range(104 * 2))
    # with rate 104 (SHA3-512 style) the compare decides how many lanes are absorbed; run absorb with rate 104
    mem1 = bytearray(MSIZE); mem2 = bytearray(MSIZE)
    for mm in (mem1, mem2): mm[INP - MBASE:INP - MBASE + len(m2)] = m2
    cpu.call(ABSORB, [STATE, INP, len(m2), 104], mem1); f.call(ABSORB, [STATE, INP, len(m2), 104], mem2)
    planted += 1; caught += int(mem1[STATE - MBASE:STATE - MBASE + 200] != mem2[STATE - MBASE:STATE - MBASE + 200])
    res['checks']['planted_faults'] = {'planted': planted, 'caught': caught}
    res['instruction_classes_executed'] = cpu.seen
    res['distinct_instruction_addresses'] = len(cpu.cache)
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
