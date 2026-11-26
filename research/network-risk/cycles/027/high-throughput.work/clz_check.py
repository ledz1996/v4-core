"""Transcription of countl_zero and bit_width from category/core/runtime/uint256.hpp at v0.16.7 (lines 1063-1074, 1164-1168),
checked against Python integers on every power of two, every 2^k-1, every 2^k+1 and 200,000 random words of random bit length."""
import random
def clz64(w): return 64 - w.bit_length()
def countl_zero(x):
    words = [(x >> (64 * i)) & (2**64 - 1) for i in range(4)]
    cnt = 256
    for i in range(4):
        if words[i] != 0:
            cnt = 192 - 64 * i + clz64(words[i])
    return cnt
def bit_width(x): return 256 - countl_zero(x)
bad = 0; n = 0
vals = [0] + [1 << k for k in range(256)] + [(1 << k) - 1 for k in range(1, 257)] + [(1 << k) + 1 for k in range(1, 256)]
r = random.Random(27)
vals += [r.getrandbits(r.randint(1, 256)) for _ in range(200000)]
for v in vals:
    n += 1
    if countl_zero(v) != 256 - v.bit_length(): bad += 1
for k in (96, 128):
    assert bit_width(1 << k) - 1 == k
print('checked', n, 'mismatches', bad, 'exp for 2^96 and 2^128:', bit_width(1 << 96) - 1, bit_width(1 << 128) - 1)
