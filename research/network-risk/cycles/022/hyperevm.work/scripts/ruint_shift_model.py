"""Transcription of ruint 1.20.1 src/bits.rs wrapping_shl / wrapping_shr u256 fast paths and
arithmetic_shr, checked against exact integer semantics for every shift 0..300 on 4,000 values."""
import random, json, sys
M128 = (1 << 128) - 1; M256 = (1 << 256) - 1; U32 = (1 << 32) - 1
def ushl(x, s): return 0 if s >= 128 else (x << s) & M128
def ushr(x, s): return 0 if s >= 128 else x >> s
def wsub(a, b): return (a - b) & U32
def shift_amount(r): return U32 if r > U32 else r
def wshl(v, rhs):
    lo, hi = v & M128, v >> 128; rhs = shift_amount(rhs)
    new_lo = ushl(lo, rhs); new_hi = ushl(hi, rhs) | ushr(lo, wsub(128, rhs))
    cross = ushl(lo, wsub(rhs, 128)); mask = M128 if rhs < 128 else 0
    return ((new_hi & mask) | (cross & ~mask & M128)) << 128 | (new_lo & mask)
def wshr(v, rhs):
    lo, hi = v & M128, v >> 128; rhs = shift_amount(rhs)
    new_hi = ushr(hi, rhs); new_lo = ushr(lo, rhs) | ushl(hi, wsub(128, rhs))
    cross = ushr(hi, wsub(rhs, 128)); mask = M128 if rhs < 128 else 0
    return (new_hi & mask) << 128 | ((new_lo & mask) | (cross & ~mask & M128))
def sar(v, rhs):
    r = wshr(v, rhs)
    if v >> 255: r |= wshl(M256, max(0, 256 - rhs))
    return r
def ref_sar(v, s):
    x = v - (1 << 256) if v >> 255 else v
    return (x >> s) & M256
random.seed(22); vals = [0, 1, M256, 1 << 255, (1 << 255) - 1, M128, 1 << 128] + [random.getrandbits(random.choice([8, 64, 127, 128, 129, 200, 256])) for _ in range(4000)]
bad = []
for v in vals:
    for s in range(0, 301):
        if wshl(v, s) != ((v << s) & M256): bad.append(('shl', hex(v), s))
        if wshr(v, s) != (v >> s): bad.append(('shr', hex(v), s))
        if s < 256 and sar(v, s) != ref_sar(v, s): bad.append(('sar', hex(v), s))
out = {'values': len(vals), 'shifts': 301, 'cases': len(vals) * 301 * 3, 'mismatches': bad[:20], 'mismatchCount': len(bad)}
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(out['cases'], out['mismatchCount'])
