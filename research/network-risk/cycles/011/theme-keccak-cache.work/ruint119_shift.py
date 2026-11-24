"""Python transcription of ruint 1.19.0 src/bits.rs wrapping_shl / wrapping_shr (u256 primitive path,
lines 451-467 and 587-603) and arithmetic_shr (612-623), checked against the EVM definition of SHL, SHR,
SAR for every shift amount 0..255 that revm-interpreter's clamp (bitwise.rs:120-158) lets through.
Usage: python3 ruint119_shift.py <out.json>"""
import sys, json, random
M128 = (1 << 128) - 1; M256 = (1 << 256) - 1
def ushl(x, r): r &= 0xffffffff; return 0 if r >= 128 else (x << r) & M128
def ushr(x, r): r &= 0xffffffff; return 0 if r >= 128 else x >> r
def wsub(a, b): return (a - b) & 0xffffffff
def wshl(v, rhs):
    lo, hi = v & M128, v >> 128; rhs &= 0xffffffff
    new_lo = ushl(lo, rhs); new_hi = ushl(hi, rhs) | ushr(lo, wsub(128, rhs))
    cross = ushl(lo, wsub(rhs, 128)); mask = M128 if rhs < 128 else 0
    lo2 = new_lo & mask; hi2 = (new_hi & mask) | (cross & ~mask & M128)
    return lo2 | (hi2 << 128)
def wshr(v, rhs):
    lo, hi = v & M128, v >> 128; rhs &= 0xffffffff
    new_hi = ushr(hi, rhs); new_lo = ushr(lo, rhs) | ushl(hi, wsub(128, rhs))
    cross = ushr(hi, wsub(rhs, 128)); mask = M128 if rhs < 128 else 0
    hi2 = new_hi & mask; lo2 = (new_lo & mask) | (cross & ~mask & M128)
    return lo2 | (hi2 << 128)
def ashr(v, rhs):
    sign = v >> 255; r = wshr(v, rhs)
    if sign: r |= wshl(M256, max(256 - rhs, 0))
    return r
def evm_sar(v, s):
    sv = v - (1 << 256) if v >> 255 else v
    return (sv >> s) & M256
rnd = random.Random(633); vals = [0, 1, M256, 1 << 255, (1 << 255) - 1, M128, M128 << 128]
vals += [1 << i for i in range(256)] + [rnd.getrandbits(256) for _ in range(400)]
bad = []; n = 0
for v in vals:
    for s in range(256):
        n += 3
        if wshl(v, s) != (v << s) & M256: bad.append(('shl', hex(v), s))
        if wshr(v, s) != v >> s: bad.append(('shr', hex(v), s))
        if ashr(v, s) != evm_sar(v, s): bad.append(('sar', hex(v), s))
json.dump({'cases': n, 'mismatches': bad[:20], 'mismatchCount': len(bad)}, open(sys.argv[1], 'w'), indent=1)
print(n, len(bad))
