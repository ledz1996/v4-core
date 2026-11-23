from base import *
from stubs import *
pm = net(1)['poolManager'].lower()
W = '0x9cdf242ef7975d8c68d5c1f5b6905801699b1940'; PAIR = '0x6ec94f50cadcc79984463688de42a0ca696ec2db'
data = '0x' + u256(3) + ''.join(adr(W) + adr(r) for r in (PAIR, SINK, W, '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'))
r = ecall(1, pm, data, {pm: {'code': SURCH}}, gas=45_000_000, frm=A)
print(r if not isinstance(r, str) else [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(4)])
sels = ['a8aa1b31', '49bd5a5e', '8da5cb5b', '1694505e', '0dfe1681']
d2 = '0x' + ''.join(adr(W) + s.ljust(64, '0') for s in sels)
r = ecall(1, STUB if False else '0x00000000000000000000000000000000000ba1a5', d2, {'0x00000000000000000000000000000000000ba1a5': {'code': GET}})
print(r)
