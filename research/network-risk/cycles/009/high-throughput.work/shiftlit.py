"""Transcription of Monad v0.16.6 Emitter::shift_literal_by_non_literal
(category/vm/compiler/ir/x86/emitter.cpp lines 5253-5326 at tag v0.16.6, identical at v0.16.7)
and of destructive_mov_stack_elem_to_bounded_rax with bound 256 (lines 4122-4175),
compared with the EVM definitions of SHL, SHR and SAR.

The rodata window is modelled as a byte array; vmovups is a 32 byte little endian load;
vpsllq and vpsrlq shift each 64 bit lane by the low 64 bits of the count register.
"""
import random, sys, json

M = (1 << 256) - 1
M64 = (1 << 64) - 1


def le(x, n=32):
    return x.to_bytes(n, 'little')


def add96(x0, x1, x2):
    return bytearray(le(x0) + le(x1) + le(x2))


def load32(buf, off):
    assert 0 <= off and off + 32 <= len(buf), off
    return int.from_bytes(buf[off:off + 32], 'little')


def lanes(x):
    return [(x >> (64 * i)) & M64 for i in range(4)]


def unl(ls):
    return sum(v << (64 * i) for i, v in enumerate(ls))


def vpsllq(x, c):
    return unl([(v << c) & M64 if c < 64 else 0 for v in lanes(x)])


def vpsrlq(x, c):
    return unl([(v >> c) if c < 64 else 0 for v in lanes(x)])


def bounded_rax_gpr(x, bound=256, live=False):
    g = lanes(x)
    zf_src = None
    if not live:
        if g[0] > bound: g[1] = g[0]
        g[2] |= g[3]; g[2] |= g[1]; zf_src = g[2]
    else:
        rax = g[1]
        if g[0] > bound: rax = g[0]
        rax |= g[2]; rax |= g[3]; zf_src = rax
    eax = bound
    if zf_src == 0: eax = g[0] & 0xffffffff
    return eax


def bounded_rax_avx(x, bound=256):
    if (bound + 1) & bound == 0:  # popcount(bound+1) == 1
        shift = bound.bit_length(); mask = (M << shift) & M
        nz = (x & mask) != 0
    else:
        # vpsubusw tmp, y, add32(bound-1): unsigned saturating subtract of 16 bit words
        b = bound - 1
        ws = [(x >> (16 * i)) & 0xffff for i in range(16)]
        bs = [(b >> (16 * i)) & 0xffff for i in range(16)]
        t = [max(0, w - c) for w, c in zip(ws, bs)]
        nz = any(t)
    eax = x & 0xffffffff
    if nz: eax = bound
    return eax


def shift_literal_by_non_literal(kind, value, eax):
    assert 0 <= eax <= 256
    if kind == 'SHL':
        buf = add96(7, 0, value); bit_mask_off = 0; base = 64
    else:
        neg = kind == 'SAR' and (value >> 255) & 1
        fill = M if neg else 0
        x2 = (fill & M64) | ((fill & M64) << 64) | (7 << 128)
        buf = add96(value, fill, x2); bit_mask_off = 80; base = 0
    # padding entries before and after are other rodata; place guard bytes to detect reads outside the window
    guard = 64
    buf = bytearray(b'\xa5' * guard) + buf + bytearray(b'\x5a' * guard)
    base += guard; bit_mask_off += guard
    mask128 = int.from_bytes(buf[bit_mask_off:bit_mask_off + 16], 'little')
    tmp1 = eax & mask128  # vmovd zero extends; vpand with 16 byte memory operand
    rax = eax >> 3
    if kind == 'SHL': rax = -rax
    carry = -1 if kind == 'SHL' else 1
    out = load32(buf, base + rax)
    tmp2 = load32(buf, base + rax + carry)
    c = tmp1 & M64  # vpsllq/vpsrlq take the low 64 bits of the xmm count
    if kind == 'SHL':
        out = vpsllq(out, c); tmp2 = vpsllq(tmp2, c); tmp2 = vpsrlq(tmp2, 8)
    else:
        out = vpsrlq(out, c); tmp2 = vpsrlq(tmp2, c); tmp2 = vpsllq(tmp2, 8)
    return out | tmp2


def spec(kind, shift, value):
    if kind == 'SHL': return (value << shift) & M if shift < 256 else 0
    if kind == 'SHR': return value >> shift if shift < 256 else 0
    sv = value - (1 << 256) if value >> 255 else value
    if shift >= 256: return M if sv < 0 else 0
    return (sv >> shift) & M


if __name__ == '__main__':
    rnd = random.Random(9_143)
    src_values = {
        'one (TickBitmap.sol:73, :110)': 1,
        'all ones (TickBitmap.sol:97)': M,
        'BitMath.sol:22 table': 0x8421084210842108cc6318c6db6d54be,
        'BitMath.sol:40-42 table': 0x8040405543005266443200005020610674053026020000107506200176117077,
        'bytes4 mask at pc 16643': 0xffffffff << 224,
    }
    extra = [0, 2, 3, 0xff, 1 << 63, 1 << 64, (1 << 64) - 1, 1 << 127, 1 << 128, 1 << 255, M - 1, (1 << 255) - 1,
             M ^ (1 << 255), 0x8000000000000000000000000000000000000000000000000000000000000001,
             0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0]
    values = list(src_values.values()) + extra + [rnd.getrandbits(256) for _ in range(400)] + \
        [rnd.getrandbits(256) | (1 << 255) for _ in range(200)] + [rnd.getrandbits(rnd.randint(1, 255)) for _ in range(400)]
    shifts = list(range(0, 300)) + [1 << 32, (1 << 32) + 3, 1 << 64, (1 << 64) + 5, M, M - 254, 1 << 128, (1 << 192) + 1, 257 << 64]
    bad = []; n = 0
    for kind in ('SHL', 'SHR', 'SAR'):
        for v in values:
            for s in shifts:
                eaxs = {bounded_rax_gpr(s, 256, False), bounded_rax_gpr(s, 256, True), bounded_rax_avx(s, 256)}
                for eax in eaxs:
                    n += 1
                    got = shift_literal_by_non_literal(kind, v, eax)
                    if got != spec(kind, s, v):
                        bad.append((kind, hex(v), hex(s), eax, hex(got)))
                if len(eaxs) != 1: bad.append(('bound', hex(s), sorted(eaxs)))
    # bounded rax on its own, bound 256 and bound 31 (signextend)
    for s in shifts + [rnd.getrandbits(256) for _ in range(2000)]:
        for b in (256, 31):
            want = s if s < b else b
            for got in (bounded_rax_gpr(s, b, False), bounded_rax_gpr(s, b, True), bounded_rax_avx(s, b)):
                n += 1
                if got != want: bad.append(('bounded', b, hex(s), got))
    res = {'cases': n, 'mismatches': len(bad), 'first': bad[:20], 'sourceValues': {k: hex(v) for k, v in src_values.items()}}
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1: json.dump(res, open(sys.argv[1], 'w'), indent=1)
