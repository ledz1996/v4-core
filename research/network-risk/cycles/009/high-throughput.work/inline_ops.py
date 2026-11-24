"""Transcriptions of inline x86 paths of the Monad v0.16.5 compiler
(category/vm/compiler/ir/x86/emitter.cpp at tag v0.16.5), compared with the EVM definitions.

Covered, each at the operand locations the emitter distinguishes:
- SIGNEXTEND by a literal index: signextend_avx_reg_by_int8 (4401-4462, vpshufb, vpsraw, vpblendvb)
  and signextend_general_reg_or_stack_offset_by_int8 (4464-4567), with signextend_by_literal_ix (4569-4585).
- BYTE with a variable index: byte_non_literal_ix_literal_or_stack_offset_src (4137-4197),
  byte_non_literal_ix_general_reg_src (4243-4303), byte_non_literal_ix_avx_reg_src (4343-4398);
  BYTE with a literal index: byte_literal_ix_general_reg_src (4199-4241), byte_literal_ix_avx_reg_src (4305-4341).
- LT, GT, SLT, SGT as deferred comparisons: lt (3917-3961), slt (3963-4027) with general_bin_instr
  (5604-5700, cmp then sbb, leading zero limbs of a literal skipped) and issigned (2948-2980),
  read through the flags the JUMPI would test.
"""
import random, json, sys

M = (1 << 256) - 1; M64 = (1 << 64) - 1


def by(x): return list(x.to_bytes(32, 'little'))
def unby(b): return int.from_bytes(bytes(b), 'little')
def limbs(x): return [(x >> (64 * i)) & M64 for i in range(4)]
def s64(v): return v - (1 << 64) if v >> 63 else v


def spec_signextend(b, x):
    if b >= 31: return x
    bit = 8 * b + 7; mask = (1 << (bit + 1)) - 1
    return (x | (M ^ mask)) if (x >> bit) & 1 else (x & mask)


def spec_byte(i, x): return (x >> (8 * (31 - i))) & 0xff if i < 32 else 0


def spec_slt(a, b):
    sa = a - (1 << 256) if a >> 255 else a; sb = b - (1 << 256) if b >> 255 else b
    return int(sa < sb)


def vpshufb256(src, ctl):  # per 128 bit lane
    out = []
    for j in range(32):
        c = ctl[j]; lane = j // 16
        out.append(0 if c & 0x80 else src[16 * lane + (c & 15)])
    return out


def signext_avx(ix, x):
    src = by(x)
    shuf = [0xff] * 32
    for j in range(ix + 1, 32): shuf[j] = ix
    if ix >= 16: dst = vpshufb256(src, shuf)
    else: dst = vpshufb256(src[:16] + src[:16], shuf)
    # vpsraw 15 per 16 bit word
    for w in range(16):
        hi = dst[2 * w + 1]; v = 0xff if hi & 0x80 else 0
        dst[2 * w] = v; dst[2 * w + 1] = v
    out = [src[j] if shuf[j] & 0x80 else dst[j] for j in range(32)]  # vpblendvb
    return unby(out)


def signext_gpr(ix, x):
    g = limbs(x); r = ix // 8; off = ix % 8
    v = g[r]
    if off == 0: v = (s64(((v & 0xff) ^ 0x80) - 0x80 & M64) if False else ((v & 0xff) - (0x100 if v & 0x80 else 0)) & M64)
    elif off == 1: v = ((v & 0xffff) - (0x10000 if v & 0x8000 else 0)) & M64
    elif off == 3: v = ((v & 0xffffffff) - (1 << 32 if v & 0x80000000 else 0)) & M64
    elif off == 7: pass
    else:
        sh = (7 - off) * 8; v = (v << sh) & M64; v = (s64(v) >> sh) & M64
    g[r] = v
    if r + 1 < 4:
        ones = (s64(v) >> 63) & M64
        for k in range(r + 1, 4): g[k] = ones
    return sum(l << (64 * i) for i, l in enumerate(g))


def signext_literal_ix(ix, x, kind):
    if ix >= 31: return x
    return signext_avx(ix, x) if kind == 'avx' else signext_gpr(ix, x)


def hi192_nonzero(i): return (i >> 64) != 0


def byte_mem_src(i, x):
    ix0 = i & M64
    d0 = (31 - ix0) & M64; cf = ix0 > 31
    if cf: d0 = 0
    b = by(x)[d0]
    if cf: b = 0
    if hi192_nonzero(i): b = 0
    return b


def byte_gpr_src(i, x):
    s = limbs(x); ix0 = i & M64
    d0 = s[0]
    if ix0 < 24: d0 = s[1]
    if ix0 < 16: d0 = s[2]
    if ix0 < 8: d0 = s[3]
    d1 = (31 - ix0) & M64; cf = ix0 > 31
    if cf: d0 = 0
    if hi192_nonzero(i): d0 = 0
    d1 = (d1 & 7) << 3
    return (d0 >> d1) & 0xff


def byte_avx_src(i, x):
    zf_nz = hi192_nonzero(i)
    rax = i & M64
    if zf_nz: rax = 32
    above = rax > 31
    rax = (rax - 31) & M64
    if above: rax = 1
    rax = (-rax) & M64
    eax = rax & 0xffffffff
    idx = eax >> 2  # vpsrld 2 on dword 0
    dwords = [(x >> (32 * k)) & 0xffffffff for k in range(8)]
    d0 = dwords[idx & 7]  # vpermps uses the low 3 bits of each index
    c = eax & 0xe3
    if c & 0x80: return 0
    return (d0 >> (8 * (c & 15))) & 0xff if (c & 15) < 4 else None


def byte_lit_gpr(i, x):
    bi = 31 - i; w = bi >> 3; sh = (bi & 7) << 3
    return (limbs(x)[w] >> sh) & 0xff


def byte_lit_avx(i, x):
    bi = 31 - i; yw = bi >> 4; sub = bi & 15
    b = by(x)
    lane = b[16:32] if yw else b[0:16]
    return lane[sub]


def flags_cmp_sbb(dst, src, src_literal):
    """cmp/sbb chain over limbs, skipping leading zero limbs of a literal src; returns CF, SF, OF of the last op."""
    d = limbs(dst); s = limbs(src); emitted = 0; cf = 0; last = None
    for i in range(4):
        if src_literal and emitted == 0 and s[i] == 0: continue
        borrow = cf if emitted else 0
        r = d[i] - s[i] - borrow
        cf = int(r < 0); r &= M64
        sf = r >> 63
        of = int((s64(d[i]) - s64(s[i]) - borrow) != s64(r))
        last = (cf, sf, of); emitted += 1
    return last


def lt_compiled(a, b, a_lit, b_lit):
    # Emitter::lt(pre_dst=a, pre_src=b): a < b
    if a_lit and b_lit: return int(a < b)
    negate = False
    if a_lit:
        a, b = b, (a + 1) & M; a_lit, b_lit = b_lit, True; negate = True
    if b_lit and b == 0: return 0
    cf, sf, of = flags_cmp_sbb(a, b, b_lit)
    return int(not cf) if negate else cf


def slt_compiled(a, b, a_lit, b_lit):
    if a_lit and b_lit: return spec_slt(a, b)
    negate = False
    if a_lit:
        a, b = b, (a + 1) & M; a_lit, b_lit = b_lit, True; negate = True
    if b_lit and b == 1 << 255: return 0
    if b_lit and b == 0:
        less = a >> 255  # issigned: test of the top limb, Less = sign
        return int(not less) if negate else less
    cf, sf, of = flags_cmp_sbb(a, b, b_lit)
    less = int(sf != of)
    return int(not less) if negate else less


if __name__ == '__main__':
    rnd = random.Random(575)
    edge = [0, 1, 2, 0x7f, 0x80, 0xff, 0x7fffff, 0x800000, 0xffffff, (1 << 255) - 1, 1 << 255, M, M - 1, (1 << 255) + 1,
            M64, 1 << 64, (1 << 64) - 1, 1 << 63, (1 << 128) - 1, 1 << 127, 1 << 128, (1 << 192) - 1, 1 << 191, 1 << 192,
            M ^ 0x7fffff, M ^ 0xffffff, 887272, (-887272) & M, 887271, (-887271) & M, 0x7fffffffffffffffffffffffffffffff,
            (-(1 << 127)) & M]
    vals = edge + [rnd.getrandbits(256) for _ in range(3000)] + [rnd.getrandbits(rnd.randint(1, 256)) for _ in range(3000)] + \
        [(M ^ rnd.getrandbits(rnd.randint(1, 255))) for _ in range(1000)]
    bad = {}; n = {}
    def chk(name, got, want, ctx):
        n[name] = n.get(name, 0) + 1
        if got != want: bad.setdefault(name, []).append(ctx)
    for x in vals:
        for ix in list(range(0, 40)) + [255, 256, 1 << 64, M]:
            for kind in ('avx', 'gpr'):
                chk('SIGNEXTEND literal ix ' + kind, signext_literal_ix(ix, x, kind), spec_signextend(ix, x), (ix, hex(x)))
    idxs = list(range(0, 40)) + [63, 64, 255, 256, (1 << 32) + 3, (1 << 64) - 1, (1 << 64) + 3, 1 << 64, 1 << 100, (1 << 192) + 5, M, M - 31]
    for x in vals[:3000]:
        for i in idxs:
            want = spec_byte(i, x)
            chk('BYTE var ix, literal or memory src', byte_mem_src(i, x), want, (hex(i), hex(x)))
            chk('BYTE var ix, gpr src', byte_gpr_src(i, x), want, (hex(i), hex(x)))
            chk('BYTE var ix, avx src', byte_avx_src(i, x), want, (hex(i), hex(x)))
            if i < 32:
                chk('BYTE literal ix, gpr src', byte_lit_gpr(i, x), want, (i, hex(x)))
                chk('BYTE literal ix, avx src', byte_lit_avx(i, x), want, (i, hex(x)))
    cmpv = edge + [rnd.getrandbits(256) for _ in range(300)] + [rnd.getrandbits(64) << (64 * rnd.randint(0, 3)) for _ in range(200)]
    for a in cmpv:
        for b in cmpv[:200] + [a, (a + 1) & M, (a - 1) & M]:
            for al, bl in ((False, False), (True, False), (False, True)):
                chk('LT/GT deferred', lt_compiled(a, b, al, bl), int(a < b), (hex(a), hex(b), al, bl))
                chk('SLT/SGT deferred', slt_compiled(a, b, al, bl), spec_slt(a, b), (hex(a), hex(b), al, bl))
    res = {'cases': n, 'mismatches': {k: len(v) for k, v in bad.items()}, 'first': {k: v[:5] for k, v in bad.items()}}
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1: json.dump(res, open(sys.argv[1], 'w'), indent=1)
