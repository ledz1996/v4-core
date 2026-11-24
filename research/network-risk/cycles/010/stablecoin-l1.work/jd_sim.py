# Lane-exact Python transcription of evm2 66687c18 jumpdest kernels
# (crates/evm2/src/bytecode/analysis.rs, analysis/x86.rs, analysis/aarch64.rs).
import numpy as np, random, sys

U8 = np.uint8
JUMPDEST = 0x5b
PUSH1 = 0x60
PUSHX = PUSH1 - 1            # i8 0x5f
END_OFFSET = PUSH1 - 2       # 0x5e
BIAS = 0x70

def lanes(n, period, start):
    return np.array([(start + (i % period)) & 0xff for i in range(n)], dtype=U8)

def s8(v): return v.view(np.int8)

# ---------------- primitive emulation ----------------
def max_epi8(a, b): return np.maximum(s8(a), s8(b)).view(U8)
def max_epu8(a, b): return np.maximum(a, b)
def min_epu8(a, b): return np.minimum(a, b)
def add8(a, b): return (a.astype(np.uint16) + b).astype(U8)
def sub8(a, b): return (a.astype(np.int16) - b).astype(U8)
def cmpeq(a, b): return np.where(a == b, U8(0xff), U8(0))
def cmpgt_epi8(a, b): return np.where(s8(a) > s8(b), U8(0xff), U8(0))
def movemask(a):  # bit i = msb of byte i
    r = 0
    for i, v in enumerate(a):
        if v & 0x80: r |= 1 << i
    return r
def blendv(a, b, m): return np.where(m & 0x80, b, a)
def pshufb(t, idx):  # works per 128-bit lane
    out = np.zeros_like(idx)
    for base in range(0, len(idx), 16):
        for j in range(16):
            i = idx[base + j]
            out[base + j] = 0 if i & 0x80 else t[base + (i & 0x0f)]
    return out
def permutexvar(idx, a):  # _mm512_permutexvar_epi8(idx, a)
    return np.array([a[i & 63] for i in idx], dtype=U8)
def permutex2var(a, idx, b):  # _mm512_permutex2var_epi8(a, idx, b)
    return np.array([(b if (i & 64) else a)[i & 63] for i in idx], dtype=U8)
def tbx(a, t, idx):  # vqtbx1q_u8
    return np.array([t[i] if i < 16 else a[j] for j, i in enumerate(idx)], dtype=U8)
def set1(n, v): return np.full(n, v & 0xff, dtype=U8)

def uncarried(jd, carried):
    return (jd >> carried) << carried

# ---------------- x86 16-byte family ----------------
LANES16 = lanes(16, 16, BIAS)
END_OFFSETS16 = lanes(16, 16, (BIAS - END_OFFSET) & 0xff)
LANES16X2 = lanes(32, 16, BIAS)
END_OFFSETS16X2 = lanes(32, 16, (BIAS - END_OFFSET) & 0xff)

class E16:  # __m128i entry biased
    @staticmethod
    def new(off): return set1(16, BIAS + off)
    @staticmethod
    def offset(e): return (int(e[0]) - BIAS) & 0xff

def compose16(s): return max_epu8(pshufb(s, s), s)
def successors16(ops):
    n0 = add8(max_epi8(ops, set1(16, PUSHX)), END_OFFSETS16)
    n1 = compose16(n0); n2 = compose16(n1); n3 = compose16(n2)
    return [n0, n1, n2, n3, compose16(n3)]
def next_entry16(exits, entry):
    block = set1(16, 16)
    return max_epu8(pshufb(sub8(exits, block), entry), sub8(entry, block))
def descend16(s, pos):
    nxt = pshufb(s, pos)
    stays = cmpeq(min_epu8(nxt, LANES16), nxt)
    return blendv(pos, nxt, stays)
def starts16(ops, entry):
    n0, n1, n2, n3, n4 = successors16(ops)
    be = entry[0]
    entry[0] = next_entry16(n4, be)
    p = descend16(n3, be); p = descend16(n2, p); p = descend16(n1, p)
    st = cmpeq(p, LANES16) | cmpeq(pshufb(n0, p), LANES16)
    return (movemask(st) & ~movemask(be)) & 0xffff
def jumpdests16(ops): return movemask(cmpeq(ops, set1(16, JUMPDEST)))

def k_sse41(ops, entry):
    return starts16(ops, entry) & jumpdests16(ops)

def k_sse41x4(ops, entry):
    o = [ops[i*16:(i+1)*16] for i in range(4)]
    jd = 0
    for i in range(4): jd |= jumpdests16(o[i]) << (i*16)
    mx = max_epi8(max_epi8(o[0], o[1]), max_epi8(o[2], o[3]))
    if movemask(cmpgt_epi8(mx, set1(16, PUSHX))) == 0:
        c = E16.offset(entry[0]); entry[0] = E16.new(0)
        return uncarried(jd, c)
    if jd == 0:
        for x in o: entry[0] = next_entry16(successors16(x)[4], entry[0])
        return 0
    st = 0
    for i in range(4): st |= starts16(o[i], entry) << (i*16)
    return st & jd

def compose16x2(s): return max_epu8(pshufb(s, s), s)
def descend16x2(s, pos):
    nxt = pshufb(s, pos)
    stays = cmpeq(min_epu8(nxt, LANES16X2), nxt)
    return blendv(pos, nxt, stays)

def k_avx2(ops, entry):
    jd = movemask(cmpeq(ops, set1(32, JUMPDEST)))
    if movemask(cmpgt_epi8(ops, set1(32, PUSHX))) == 0:
        c = E16.offset(entry[0]); entry[0] = E16.new(0)
        return uncarried(jd, c) & 0xffffffff
    n0 = add8(max_epi8(ops, set1(32, PUSHX)), END_OFFSETS16X2)
    n1 = compose16x2(n0); n2 = compose16x2(n1); n3 = compose16x2(n2); ex = compose16x2(n3)
    elo = entry[0]
    ehi = next_entry16(ex[:16], elo)
    entry[0] = next_entry16(ex[16:], ehi)
    if jd == 0: return 0
    ents = np.concatenate([elo, ehi])
    p = descend16x2(n3, ents); p = descend16x2(n2, p); p = descend16x2(n1, p)
    st = cmpeq(p, LANES16X2) | cmpeq(pshufb(n0, p), LANES16X2)
    past = movemask(ents)
    return jd & movemask(st) & ~past & 0xffffffff

# ---------------- AVX-512 VBMI ----------------
LANES64 = lanes(64, 64, 0)
END_OFFSETS64 = lanes(64, 64, (0 - END_OFFSET) & 0xff)
EXITS64 = lanes(64, 64, 64)
class E64:
    @staticmethod
    def new(off): return set1(64, off)
    @staticmethod
    def offset(e): return int(e[0])
def successors64(ops):
    n = [add8(max_epi8(ops, set1(64, PUSHX)), END_OFFSETS64)]
    for i in range(1, 7): n.append(permutex2var(n[i-1], n[i-1], EXITS64))
    return n
def descend64(s, pos):
    nxt = permutexvar(pos, s)
    return np.where(nxt <= LANES64, nxt, pos).astype(U8)
def starts64(n, entry):
    p = entry
    for i in range(5, 0, -1): p = descend64(n[i], p)
    return movemask(cmpeq(p, LANES64)) | movemask(cmpeq(permutexvar(p, n[0]), LANES64))
def next_entry64(n, entry):
    return sub8(permutexvar(entry, n[6]), set1(64, 64))
def k_avx512(ops, entry):
    n = successors64(ops); be = entry[0]
    entry[0] = next_entry64(n, be)
    return movemask(cmpeq(ops, set1(64, JUMPDEST))) & starts64(n, be)
def k_avx512x2(ops, entry):
    a_, b_ = ops[:64], ops[64:]
    ja = movemask(cmpeq(a_, set1(64, JUMPDEST))); jb = movemask(cmpeq(b_, set1(64, JUMPDEST)))
    if movemask(cmpgt_epi8(max_epi8(a_, b_), set1(64, PUSHX))) == 0:
        c = E64.offset(entry[0]); entry[0] = E64.new(0)
        return uncarried(ja, c) | (jb << 64)
    a = successors64(a_); b = successors64(b_)
    ea = entry[0]; eb = next_entry64(a, ea); entry[0] = next_entry64(b, eb)
    if (ja | jb) == 0: return 0
    return (ja & starts64(a, ea)) | ((jb & starts64(b, eb)) << 64)

# ---------------- NEON ----------------
NLANES = lanes(16, 16, 0)
NEND = lanes(16, 16, (0 - END_OFFSET) & 0xff)
WEIGHTS = np.array([1,2,4,8,16,32,64,128]*2, dtype=U8)
class EN:
    @staticmethod
    def new(off): return set1(16, off)
    @staticmethod
    def offset(e): return int(e[0])
def adv(s, pos): return tbx(pos, s, pos)
def nsucc(ops):
    n0 = add8(max_epi8(ops, set1(16, PUSHX)), NEND)
    n = [n0]
    for _ in range(4): n.append(adv(n[-1], n[-1]))
    return n
def nnext(n, e): return sub8(adv(n[4], e), set1(16, 16))
def ndescend(s, pos):
    nxt = adv(s, pos)
    return np.where(nxt <= NLANES, nxt, pos).astype(U8)   # vbslq(vcleq(next,LANES), next, pos)
def nstarts(n, e):
    p = e
    for i in range(3, -1, -1): p = ndescend(n[i], p)
    return cmpeq(p, NLANES)
def paddq(a, b):
    c = np.concatenate([a, b]).astype(np.uint16)
    return ((c[0::2] + c[1::2]) & 0xff).astype(U8)
def to_bitmap(s):
    s = [x & WEIGHTS for x in s]
    q = paddq(paddq(s[0], s[1]), paddq(s[2], s[3]))
    r = paddq(q, q)
    return int.from_bytes(bytes(r[:8]), 'little')
def k_neon(ops, entry):
    n = nsucc(ops)
    st = nstarts(n, entry[0]) & cmpeq(ops, set1(16, JUMPDEST))
    entry[0] = nnext(n, entry[0])
    z = set1(16, 0)
    return to_bitmap([st, z, z, z]) & 0xffff
def k_neonx4(ops, entry):
    o = [ops[i*16:(i+1)*16] for i in range(4)]
    jds = [cmpeq(x, set1(16, JUMPDEST)) for x in o]
    anyj = jds[0] | jds[1] | jds[2] | jds[3]
    has = int(anyj.max()) != 0
    mx = max_epi8(max_epi8(o[0], o[1]), max_epi8(o[2], o[3]))
    if int(s8(mx).max()) <= PUSHX:
        c = EN.offset(entry[0]); entry[0] = EN.new(0)
        return uncarried(to_bitmap(jds), c)
    n = [nsucc(x) for x in o]
    ents = [entry[0]] * 4
    for i in range(1, 4): ents[i] = nnext(n[i-1], ents[i-1])
    entry[0] = nnext(n[3], ents[3])
    if not has: return 0
    return to_bitmap([nstarts(n[i], ents[i]) & jds[i] for i in range(4)])

# ---------------- driver: analyze_blocks / analyze_* / analyze_scalar ----------------
def analyze_blocks(kernel, LEN, E, code, table, state):
    pc, ent = state
    entry = [E.new(ent)]
    while pc + LEN <= len(code):
        bits = kernel(np.frombuffer(code[pc:pc+LEN], dtype=U8).copy(), entry)
        bb = int(bits).to_bytes(16, 'little')[:LEN // 8]
        table[pc//8: pc//8 + LEN//8] = bb
        pc += LEN
    return (pc, E.offset(entry[0]))

def scalar(code, table, pc):
    while pc < len(code):
        b = code[pc]
        if b == JUMPDEST:
            table[pc//8] |= 1 << (pc % 8); pc += 1
        else:
            po = (b - PUSH1) & 0xff
            pc += po + 2 if po < 32 else 1

def reference(code):
    t = bytearray((len(code)+7)//8); pc = 0
    while pc < len(code):
        b = code[pc]
        if b == JUMPDEST: t[pc//8] |= 1 << (pc % 8)
        pc += 1 + (b - 0x5f if 0x60 <= b <= 0x7f else 0)
    return bytes(t)

def run(code, which):
    table = bytearray((len(code)+7)//8)
    pc = 0
    if len(code) >= 16:
        if which == 'sse41':
            st = analyze_blocks(k_sse41x4, 64, E16, code, table, (0, 0))
            p, e = analyze_blocks(k_sse41, 16, E16, code, table, st); pc = p + e
        elif which == 'avx2':
            st = analyze_blocks(k_avx2, 32, E16, code, table, (0, 0))
            p, e = analyze_blocks(k_sse41, 16, E16, code, table, st); pc = p + e
        elif which == 'avx512':
            st = analyze_blocks(k_avx512x2, 128, E64, code, table, (0, 0))
            st = analyze_blocks(k_avx512, 64, E64, code, table, st)
            p, e = analyze_blocks(k_sse41, 16, E16, code, table, st); pc = p + e
        elif which == 'neon':
            st = analyze_blocks(k_neonx4, 64, EN, code, table, (0, 0))
            p, e = analyze_blocks(k_neon, 16, EN, code, table, st); pc = p + e
        elif which == 'scalar':
            pc = 0
    scalar(code, table, pc)
    return bytes(table)

KERNELS = ['scalar', 'sse41', 'avx2', 'avx512', 'neon']

def gen(rng, mode):
    n = rng.choice([rng.randrange(0, 40), rng.randrange(0, 300), rng.randrange(120, 600)])
    if mode == 0: return bytes(rng.randrange(256) for _ in range(n))
    if mode == 1:
        pool = [0x60, 0x7f, 0x5b, 0x5b, 0x00, 0x01, 0x5f, 0x80, 0xff, 0x7e, 0x61, 0x6f]
        return bytes(rng.choice(pool) for _ in range(n))
    if mode == 2:  # all JUMPDEST with a few pushes
        c = bytearray([0x5b]*n)
        for _ in range(rng.randrange(0, 6)):
            if n: c[rng.randrange(n)] = rng.randrange(0x60, 0x80)
        return bytes(c)
    if mode == 3:  # chained PUSH32 / push chains
        c = bytearray()
        while len(c) < n:
            p = rng.choice([0x7f, 0x7f, 0x6f, 0x60, rng.randrange(0x60, 0x80)])
            c.append(p); c += bytes(rng.choice([0x5b, 0x7f, 0x60, 0x00]) for _ in range(p - 0x5f))
            if rng.random() < .3: c.append(0x5b)
        return bytes(c[:n])
    # mode 4: mostly push-free with rare pushes
    return bytes(rng.choice([0x5b]*7 + [0x01]*50 + [rng.randrange(0x60, 0x80)]) for _ in range(n))

if __name__ == '__main__':
    seed = int(sys.argv[1]); count = int(sys.argv[2])
    rng = random.Random(seed)
    bad = 0
    # exhaustive structured: one PUSH at each position near chunk edges, lengths 0..200, every PUSH size
    if seed == 0:
        cases = 0
        for L in list(range(0, 70)) + [127, 128, 129, 143, 144, 191, 192, 193, 200]:
            for at in range(L):
                for p in range(0x60, 0x80):
                    for fill in (0x5b,):
                        c = bytearray([fill]*L); c[at] = p
                        ref = reference(bytes(c))
                        for k in KERNELS:
                            if run(bytes(c), k) != ref:
                                bad += 1; print('MISMATCH', k, bytes(c).hex());
                        cases += 1
        print('structured cases', cases, 'bad', bad)
    for i in range(count):
        c = gen(rng, i % 5)
        ref = reference(c)
        for k in KERNELS:
            if run(c, k) != ref:
                bad += 1; print('MISMATCH', k, c.hex()); break
    print('seed', seed, 'random', count, 'bad', bad)
