#!/usr/bin/env python3
"""Run the shipped AArch64 KeccakF1600 routine of reth-bsc v0.1.4-hotfix-arm64 in a small A64 model.

Reads the raw instruction words from the binary (file offset equals VMA in this ELF), decodes only the
instruction classes the routine uses, refuses anything else, and compares the permutation with a Python
reference Keccak-f[1600]. It then builds Keccak-256 from the emulated permutation for the input shapes
the PoolManager hashes and for lengths 0 to 1,100 and compares with the reference sponge.

Usage: python3 -I a64keccak.py <reth-bsc arm64 binary> <out.json> [n_random_states]
"""
import sys, json, random, struct, hashlib, time

M64 = (1 << 64) - 1
ENTRY = 0x3e8c540      # KeccakF1600(state*) wrapper
INT_LO, INT_HI = 0x3e8c300, 0x3e8c5f8  # KeccakF1600_int and the wrapper, the only code allowed to run
SENTINEL = 0xDEAD000

def ror(x, n):
    n &= 63
    return ((x >> n) | (x << (64 - n))) & M64 if n else x

def decode_bitmask(N, imms, immr):
    # A64 DecodeBitMasks for 64-bit, immediate form (wmask only)
    v = (N << 6) | ((~imms) & 0x3f)
    length = v.bit_length() - 1
    if length < 1:
        raise ValueError('reserved bitmask')
    esize = 1 << length
    levels = esize - 1
    S = imms & levels
    R = immr & levels
    welem = (1 << (S + 1)) - 1
    # rotate right within esize
    welem = ((welem >> R) | (welem << (esize - R))) & ((1 << esize) - 1) if R else welem
    w = 0
    for i in range(64 // esize):
        w |= welem << (i * esize)
    return w & M64

def sx(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v

class A64:
    def __init__(self, blob):
        self.blob = blob
        self.cache = {}
        self.seen = {}

    def word(self, pc):
        return struct.unpack_from('<I', self.blob, pc)[0]

    def decode(self, pc):
        w = self.word(pc)
        if w == 0xd503201f:
            return ('nop',)
        if w == 0xd65f03c0:
            return ('ret',)
        if (w >> 24) & 0x1f == 0b01010 and (w >> 31) == 1:   # logical shifted register, 64 bit
            opc = (w >> 29) & 3; sh = (w >> 22) & 3; N = (w >> 21) & 1
            return ('logsr', opc, sh, N, (w >> 16) & 31, (w >> 10) & 63, (w >> 5) & 31, w & 31)
        if (w >> 21) == 0b10010011110:                         # EXTR 64 bit
            return ('extr', (w >> 16) & 31, (w >> 10) & 63, (w >> 5) & 31, w & 31)
        if (w >> 24) & 0x9f == 0b10000:                        # ADR
            imm = sx((((w >> 5) & 0x7ffff) << 2) | ((w >> 29) & 3), 21)
            return ('adr', w & 31, imm)
        if (w >> 26) == 0b000101:
            return ('b', sx(w & 0x3ffffff, 26) * 4)
        if (w >> 26) == 0b100101:
            return ('bl', sx(w & 0x3ffffff, 26) * 4)
        if (w >> 24) == 0b01010100 and not (w >> 4) & 1:
            return ('bcond', w & 15, sx((w >> 5) & 0x7ffff, 19) * 4)
        if (w >> 30) == 0b10 and (w >> 27) & 7 == 0b101 and not (w >> 26) & 1:  # LDP/STP 64 bit
            idx = (w >> 23) & 7; L = (w >> 22) & 1
            if idx not in (1, 2, 3):
                raise ValueError('ldp/stp form %x' % w)
            return ('pair', idx, L, sx((w >> 15) & 0x7f, 7) * 8, (w >> 10) & 31, (w >> 5) & 31, w & 31)
        if (w >> 22) & 0x3ff == 0b1111100100 or (w >> 22) & 0x3ff == 0b1111100101:  # STR/LDR uimm 64
            L = (w >> 22) & 1
            return ('ldst_u', L, ((w >> 10) & 0xfff) * 8, (w >> 5) & 31, w & 31)
        if (w >> 21) & 0x7ff in (0b11111000000, 0b11111000010) and (w >> 10) & 3 in (1, 3):  # STR/LDR imm9 post/pre
            L = (w >> 22) & 1
            return ('ldst_i', L, (w >> 10) & 3, sx((w >> 12) & 0x1ff, 9), (w >> 5) & 31, w & 31)
        if (w >> 23) & 0x3f == 0b100010 and (w >> 31) == 1:   # ADD/SUB immediate 64 bit
            op = (w >> 30) & 1; S = (w >> 29) & 1; shf = (w >> 22) & 1
            if S:
                raise ValueError('adds/subs not modelled %x' % w)
            return ('addsub', op, ((w >> 10) & 0xfff) << (12 * shf), (w >> 5) & 31, w & 31)
        if (w >> 23) & 0x1ff == 0b111100100:                   # ANDS immediate 64 bit (tst)
            N = (w >> 22) & 1
            return ('andsi', decode_bitmask(N, (w >> 10) & 63, (w >> 16) & 63), (w >> 5) & 31, w & 31)
        raise ValueError('unmodelled instruction %08x at %x' % (w, pc))

    def run(self, state_words, entry=ENTRY):
        X = [0] * 31
        X[0] = 0x7f0000100000   # state pointer
        stbase = X[0]
        sp = 0x7f00000f0000
        X[30] = SENTINEL
        for r in range(19, 30):
            X[r] = (0x1111111111111111 * (r - 18)) & M64
        callee = X[19:30]
        mem = {}
        for i, v in enumerate(state_words):
            mem[X[0] + 8 * i] = v
        Z = 0
        pc = entry
        steps = 0

        def rd(n):
            return 0 if n == 31 else X[n]
        def rd_sp(n):
            return sp if n == 31 else X[n]
        def ld(a):
            if a & 7:
                raise ValueError('unaligned load')
            if a in mem:
                return mem[a]
            if INT_LO - 0x200 <= a < INT_HI:
                return struct.unpack_from('<Q', self.blob, a)[0]
            raise ValueError('load from unmapped %x' % a)
        while pc != SENTINEL:
            if not (INT_LO <= pc < INT_HI):
                raise ValueError('pc left the routine: %x' % pc)
            ins = self.cache.get(pc)
            if ins is None:
                ins = self.decode(pc); self.cache[pc] = ins
            k = ins[0]
            self.seen[k] = self.seen.get(k, 0) + 1
            steps += 1
            npc = pc + 4
            if k == 'logsr':
                _, opc, sh, N, rm, imm6, rn, d = ins
                b = rd(rm)
                if sh == 0: b = (b << imm6) & M64
                elif sh == 1: b = b >> imm6
                elif sh == 2: b = (sx(b, 64) >> imm6) & M64
                else: b = ror(b, imm6)
                if N: b = (~b) & M64
                a = rd(rn)
                if opc == 0: r = a & b
                elif opc == 1: r = a | b
                elif opc == 2: r = a ^ b
                else:
                    r = a & b; Z = int(r == 0)
                if d != 31: X[d] = r
            elif k == 'extr':
                _, rm, lsb, rn, d = ins
                v = ((rd(rn) << 64) | rd(rm)) >> lsb
                if d != 31: X[d] = v & M64
            elif k == 'adr':
                X[ins[1]] = (pc + ins[2]) & M64
            elif k == 'b':
                npc = pc + ins[1]
            elif k == 'bl':
                X[30] = pc + 4; npc = pc + ins[1]
            elif k == 'bcond':
                c = ins[1]
                if c == 1: take = (Z == 0)
                elif c == 0: take = (Z == 1)
                else: raise ValueError('cond %d not modelled' % c)
                if take: npc = pc + ins[2]
            elif k == 'ret':
                npc = X[30]
            elif k == 'nop':
                pass
            elif k == 'pair':
                _, idx, L, off, t2, n, t = ins
                base = rd_sp(n)
                addr = base if idx == 1 else (base + off) & M64
                if L:
                    v1, v2 = ld(addr), ld(addr + 8)
                    if t != 31: X[t] = v1
                    if t2 != 31: X[t2] = v2
                else:
                    mem[addr] = rd(t); mem[addr + 8] = rd(t2)
                if idx in (1, 3):
                    nb = (base + off) & M64
                    if n == 31: sp = nb
                    else: X[n] = nb
            elif k == 'ldst_u':
                _, L, off, n, t = ins
                addr = (rd_sp(n) + off) & M64
                if L:
                    if t != 31: X[t] = ld(addr)
                else:
                    mem[addr] = rd(t)
            elif k == 'ldst_i':
                _, L, mode, off, n, t = ins
                base = rd_sp(n)
                addr = base if mode == 1 else (base + off) & M64
                if L:
                    v = ld(addr)
                    if t != 31: X[t] = v
                else:
                    mem[addr] = rd(t)
                nb = (base + off) & M64
                if n == 31: sp = nb
                else: X[n] = nb
            elif k == 'addsub':
                _, op, imm, n, d = ins
                a = rd_sp(n)
                r = (a - imm) & M64 if op else (a + imm) & M64
                if d == 31: sp = r
                else: X[d] = r
            elif k == 'andsi':
                _, mask, n, d = ins
                r = rd(n) & mask
                Z = int(r == 0)
                if d != 31: X[d] = r
            else:
                raise ValueError(k)
            pc = npc
            if steps > 100000:
                raise ValueError('runaway')
        if sp != 0x7f00000f0000 or X[19:30] != callee:
            raise ValueError('ABI not restored')
        return [mem[stbase + 8 * i] for i in range(25)], steps

# ---- reference Keccak-f[1600]
RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
      0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
      0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
      0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
      0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]

def rol(x, n):
    return ((x << n) | (x >> (64 - n))) & M64 if n else x

def keccak_f(A):
    s = [[A[x + 5 * y] for y in range(5)] for x in range(5)]
    for rc in RC:
        C = [s[x][0] ^ s[x][1] ^ s[x][2] ^ s[x][3] ^ s[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ rol(C[(x + 1) % 5], 1) for x in range(5)]
        s = [[s[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = rol(s[x][y], ROT[x][y])
        s = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        s[0][0] ^= rc
    return [s[i % 5][i // 5] for i in range(25)]

def sponge(msg, perm, pad=0x01, rate=136, outlen=32):
    st = [0] * 25
    m = bytearray(msg) + bytes([pad])
    while len(m) % rate:
        m.append(0)
    m[-1] |= 0x80
    for off in range(0, len(m), rate):
        blk = m[off:off + rate]
        for i in range(rate // 8):
            st[i] ^= struct.unpack_from('<Q', blk, 8 * i)[0]
        st = perm(st)
    return b''.join(struct.pack('<Q', w) for w in st)[:outlen]

def main():
    blob = open(sys.argv[1], 'rb').read()
    out = sys.argv[2]
    n_rand = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    cpu = A64(blob)
    rng = random.Random(38)
    res = {'binary_sha256': hashlib.sha256(blob).hexdigest(), 'entry': hex(ENTRY), 'checks': {}}
    # reference self check against hashlib (SHA3 padding) and the known empty Keccak-256
    assert sponge(b'', keccak_f).hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    for L in (0, 1, 135, 136, 137, 300):
        m = bytes(rng.getrandbits(8) for _ in range(L))
        assert sponge(m, keccak_f, pad=0x06) == hashlib.sha3_256(m).digest()
    emu = lambda st: cpu.run(st)[0]
    t0 = time.time()
    # 1. permutation on random and structured states
    bad = 0; n = 0
    shapes = []
    for i in range(n_rand):
        shapes.append([rng.getrandbits(64) for _ in range(25)])
    for i in range(25):
        for v in (0, 1, M64, 1 << 63, 0x8000000000000001):
            st = [0] * 25; st[i] = v; shapes.append(st)
    shapes.append([0] * 25); shapes.append([M64] * 25)
    for st in shapes:
        n += 1
        if emu(list(st)) != keccak_f(list(st)):
            bad += 1
    res['checks']['permutation'] = {'cases': n, 'mismatches': bad}
    # 2. Keccak-256 through the emulated permutation
    msgs = []
    for L in range(0, 1101):
        msgs.append(bytes(rng.getrandbits(8) for _ in range(L)))
    word = lambda v: v.to_bytes(32, 'big')
    for _ in range(300):
        a = rng.getrandbits(160); s = rng.randrange(0, 12)
        msgs.append(word(a) + word(s))                                  # mapping slot keccak(key . slot)
        msgs.append(word(rng.getrandbits(256)) + word(rng.getrandbits(256)))  # nested mapping
        msgs.append(b''.join(word(rng.getrandbits(160)) for _ in range(2)) + word(rng.getrandbits(24)) +
                    word(rng.getrandbits(24)) + word(rng.getrandbits(160)))   # PoolKey, 160 bytes
        msgs.append(a.to_bytes(20, 'big') + rng.getrandbits(24).to_bytes(3, 'big') * 2 + word(rng.getrandbits(256)))  # position key, 58 bytes
        msgs.append(word(a) + word(rng.getrandbits(160)))               # transient delta slot keccak(target . currency)
    for k in range(1, 9):
        for d in (-2, -1, 0, 1, 2):
            msgs.append(bytes(rng.getrandbits(8) for _ in range(136 * k + d)))
    for _ in range(14000):
        msgs.append(rng.getrandbits(512).to_bytes(64, 'big'))
    for _ in range(10000):
        msgs.append(rng.getrandbits(256).to_bytes(32, 'big') + rng.randrange(0, 7).to_bytes(32, 'big'))
    bad = 0
    for m in msgs:
        if sponge(m, emu) != sponge(m, keccak_f):
            bad += 1
    res['checks']['keccak256'] = {'cases': len(msgs), 'mismatches': bad, 'lengths': '0..1100, 136k-2..136k+2 for k 1..8, 1,500 PoolManager key shapes, 14,000 random 64 byte keys, 10,000 mapping keys with slot 0..6'}
    # 3. planted faults: flip one bit of one round constant word and of one rotate amount in the model
    caught = 0
    planted = 0
    orig = cpu.blob
    for off, bit in ((0x3e8c240 + 8 * 5, 7), (0x3e8c240 + 8 * 23, 63)):
        b = bytearray(orig); b[off + bit // 8] ^= 1 << (bit % 8)
        f = A64(bytes(b)); planted += 1
        st = [rng.getrandbits(64) for _ in range(25)]
        if f.run(list(st))[0] != keccak_f(list(st)): caught += 1
    b = bytearray(orig)
    w = struct.unpack_from('<I', b, 0x3e8c3e4)[0]                # ror x1, x6, #20  ->  #21
    struct.pack_into('<I', b, 0x3e8c3e4, (w & ~(63 << 10)) | (21 << 10))
    f = A64(bytes(b)); planted += 1
    st = [rng.getrandbits(64) for _ in range(25)]
    if f.run(list(st))[0] != keccak_f(list(st)): caught += 1
    res['checks']['planted_faults'] = {'planted': planted, 'caught': caught}
    res['instruction_classes_executed'] = cpu.seen
    res['distinct_instruction_addresses'] = len(cpu.cache)
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main()
