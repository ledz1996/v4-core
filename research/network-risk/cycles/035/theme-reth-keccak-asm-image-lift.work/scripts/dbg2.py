import sys
sys.path.insert(0, sys.argv[1])
from xlmodel import *
m = Model(sys.argv[2], sys.argv[3])
IN, OUT = 0x30000000, 0x31000000
a = bytes(range(1, 59)); n = len(a)
m.wr(IN, n, int.from_bytes(a, 'little'))
c = m.run(HASHER, [SEED, SECRET, IN, n]); h = c.r['rax']; idx, tag = h & (CAP - 1), h & (-CAP & M64)
m.run(KCACHE, [OUT, IN, n])
b = BUCKETS + 128 * idx
print('after miss: tag', hex(m.rd(b, 8)), hex(tag), 'len', m.rd(b + 8, 1))
m.wr(b, 8, tag); m.wr(b + 8, 1, n); m.wr(b + 9, 87, int.from_bytes(a + bytes(87 - n), 'little')); m.wr(b + 0x60, 32, int.from_bytes(b'\x5a' * 32, 'little'))
m.run(KCACHE, [OUT, IN, n])
print('hit returns', m.rd(OUT, 32).to_bytes(32, 'little').hex())
