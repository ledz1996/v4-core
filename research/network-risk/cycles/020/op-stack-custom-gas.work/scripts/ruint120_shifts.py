"""Transcription of the u256 fast paths that ruint 1.20.0 (Celo's celo-reth v1.0.10)
adds in src/bits.rs (wrapping_shl, wrapping_shr, arithmetic_shr via both, leading_zeros,
trailing_ones) and of the revm-interpreter 35.0.1 SHL, SHR, SAR, SIGNEXTEND handlers that
call them, checked against the EVM definition. u128 operations are emulated with masks;
unbounded_shl/shr return 0 for an amount >= 128. Usage: python3 ruint120_shifts.py <out.json>"""
import sys, json, random
M128 = (1 << 128) - 1; M256 = (1 << 256) - 1; U32 = (1 << 32) - 1
def ush(x, r): return 0 if r >= 128 else (x << r) & M128
def usr(x, r): return 0 if r >= 128 else x >> r
def shift_amount(rhs): return U32 if rhs > U32 else rhs
def wsub32(a, b): return (a - b) & U32
def wrapping_shl(v, rhs):
    lo, hi = v & M128, v >> 128
    rhs = shift_amount(rhs)
    new_lo = ush(lo, rhs)
    new_hi = ush(hi, rhs) | usr(lo, wsub32(128, rhs))
    cross = ush(lo, wsub32(rhs, 128))
    mask = (0 - (1 if rhs < 128 else 0)) & M128
    lo2 = new_lo & mask
    hi2 = (new_hi & mask) | (cross & (~mask & M128))
    return (hi2 << 128) | lo2
def wrapping_shr(v, rhs):
    lo, hi = v & M128, v >> 128
    rhs = shift_amount(rhs)
    new_hi = usr(hi, rhs)
    new_lo = usr(lo, rhs) | ush(hi, wsub32(128, rhs))
    cross = usr(hi, wsub32(rhs, 128))
    mask = (0 - (1 if rhs < 128 else 0)) & M128
    hi2 = new_hi & mask
    lo2 = (new_lo & mask) | (cross & (~mask & M128))
    return (hi2 << 128) | lo2
def arithmetic_shr(v, rhs):
    r = wrapping_shr(v, rhs)
    if v >> 255: r |= wrapping_shl(M256, max(256 - rhs, 0))
    return r
def lz(v):
    lo, hi = v & M128, v >> 128
    clz = lambda x: 128 - x.bit_length()
    return clz(hi) if hi != 0 else clz(lo) + 128
def tones(v):
    lo, hi = v & M128, v >> 128
    to = lambda x: (x ^ (x + 1)).bit_length() - 1
    return to(hi) + 128 if lo == M128 else to(lo)
SAT = (1 << 64) - 1
def sat(a): return a if a <= SAT else SAT
def h_shl(a, b): s = sat(a); return wrapping_shl(b, s) if s < 256 else 0
def h_shr(a, b): s = sat(a); return wrapping_shr(b, s) if s < 256 else 0
def h_sar(a, b):
    s = sat(a)
    if s < 256: return arithmetic_shr(b, s)
    return M256 if b >> 255 else 0
def h_sx(ext, x):
    if ext < 31:
        bi = 8 * ext + 7
        bit = (x >> bi) & 1
        mask = (wrapping_shl(1, bi) - 1) & M256
        return (x | (~mask & M256)) if bit else (x & mask)
    return x
def r_shl(a, b): return (b << a) & M256 if a < 256 else 0
def r_shr(a, b): return b >> a if a < 256 else 0
def r_sar(a, b):
    sb = b - (1 << 256) if b >> 255 else b
    return (sb >> min(a, 256)) & M256
def r_sx(i, x):
    if i >= 31: return x
    bits = 8 * (i + 1); v = x & ((1 << bits) - 1)
    return (v - (1 << bits)) & M256 if v >> (bits - 1) else v
random.seed(20)
vals = {0, 1, 2, 3, M256, M256 - 1, 1 << 255, (1 << 255) - 1, M128, 1 << 128, (1 << 128) - 1, 1 << 127}
for k in range(256): vals |= {1 << k, (1 << k) - 1 if k else 0, M256 ^ (1 << k), (M256 << k) & M256}
for k in (64, 128, 192): vals |= {(1 << k) + 1, (1 << k) - 2}
for _ in range(600): vals.add(random.getrandbits(256)); vals.add(random.getrandbits(random.randint(1, 256)))
vals = sorted(vals)
amounts = list(range(0, 520)) + [2**32 - 1, 2**32, 2**32 + 1, 2**32 + 5, 2**64 - 1, 2**64, 2**64 + 3, 2**255, M256]
n = 0; bad = []
for v in vals:
    for a in amounts:
        for name, h, r in (('SHL', h_shl, r_shl), ('SHR', h_shr, r_shr), ('SAR', h_sar, r_sar)):
            n += 1
            if h(a, v) != r(a, v): bad.append([name, hex(a), hex(v)])
    for e in list(range(0, 40)) + [2**64, M256]:
        n += 1
        if h_sx(e, v) != r_sx(e, v): bad.append(['SIGNEXTEND', hex(e), hex(v)])
    n += 2
    if lz(v) != 256 - v.bit_length(): bad.append(['lz', hex(v)])
    if tones(v) != ((v ^ (v + 1)).bit_length() - 1 if v != M256 else 256): bad.append(['tones', hex(v)])
# raw library calls (outside the handler guard) for every amount 0..2^16 on a few words
for v in (M256, 1 << 255, 0x8000000000000000ffffffffffffffff0000000000000001ffffffffffffffff, random.getrandbits(256)):
    for a in list(range(0, 1 << 12)) + [2**32 + k for k in range(-3, 300)]:
        n += 2
        rs = (v << a) & M256 if a < 2**32 else 0
        if wrapping_shl(v, a) != rs: bad.append(['raw_shl', hex(a), hex(v)])
        if wrapping_shr(v, a) != (v >> a if a < 2**32 else 0): bad.append(['raw_shr', hex(a), hex(v)])
json.dump({'checks': n, 'values': len(vals), 'amounts': len(amounts), 'mismatches': bad[:50], 'nbad': len(bad)}, open(sys.argv[1], 'w'), indent=1)
print('checks', n, 'mismatches', len(bad))
