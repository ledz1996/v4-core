import sys
sys.path.insert(0, sys.argv[1])
from xlmodel import *
m = Model(sys.argv[2], sys.argv[3])
IN, OUT = 0x30000000, 0x31000000
a = bytes(range(1, 21))
m.wr(IN, 20, int.from_bytes(a, 'little'))
m.run(KCACHE, [OUT, IN, 20])
bs = sorted(k for k in m.state if BUCKETS <= k < BUCKETS + CAP * 128)
print('bucket bytes', len(bs), hex(bs[0]), (bs[0] - BUCKETS) // 128, hex(m.rd((bs[0] - BUCKETS) // 128 * 128 + BUCKETS, 8)))
c = m.run(HASHER, [SEED, SECRET, IN, 20]); h = c.r['rax']
print(hex(h), (h & (CAP - 1)), hex(h & (-CAP & M64)))
b = BUCKETS + 128 * (h & (CAP - 1))
m.wr(b + 0x60, 32, int.from_bytes(bytes([0x5a]) * 32, 'little'))
m.run(KCACHE, [OUT, IN, 20])
print('hit returns', m.rd(OUT, 32).to_bytes(32, 'little').hex())
print('tag word now', hex(m.rd(b, 8)), 'len', m.rd(b + 8, 1))
