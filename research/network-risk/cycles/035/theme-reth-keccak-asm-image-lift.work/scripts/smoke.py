import sys, time
sys.path.insert(0, sys.argv[1])
from xlmodel import *
m = Model(sys.argv[2], sys.argv[3])
IN, OUT = 0x30000000, 0x31000000
for fn, n in ((KCACHE, 0), (KCACHE, 5), (KCACHE, 5), (KCACHE, 64), (KCACHE, 88), (KCACHE, 136), (KLONG, 300)):
    d = bytes((i * 7 + n) & 0xff for i in range(n))
    m.wr(IN, n, int.from_bytes(d, 'little'))
    t = time.time(); s0 = m.steps
    m.run(fn, [OUT, IN, n])
    got = m.rd(OUT, 32).to_bytes(32, 'little')
    print(hex(fn), n, got == keccak(d), m.steps - s0, round(time.time() - t, 2))
