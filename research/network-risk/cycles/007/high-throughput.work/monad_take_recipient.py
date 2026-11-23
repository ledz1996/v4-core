from realpm import *
chain=143; pm=PM[chain]
ST='0x0000000000000000000000000000000000001000'
R='0x00000000000000000000000000000000000ec1e1'
G=1_000_000
Rcode=asm(['CALLER','0x'+pm[2:],'EQ',('ref','probe'),'JUMPI',
  0,'SLOAD',1,'SLOAD',8,'SHL','OR',3,'SLOAD',16,'SHL','OR',4,'SLOAD',24,'SHL','OR',0,'MSTORE',2,'SLOAD',32,'MSTORE',64,0,'RETURN',
  ('label','probe'),'0x'+sel('delegate(uint64)'),224,'SHL',0,'MSTORE',1,4,'MSTORE',
  0,0,36,0,ST,G,'DELEGATECALL',1,'ADD',0,'SSTORE',
  0,0,36,0,'CALLVALUE',ST,G,'CALLCODE',1,'ADD',1,'SSTORE',
  'CALLVALUE',2,'SSTORE',
  0,0,36,0,ST,G,'STATICCALL',1,'ADD',3,'SSTORE',
  0,0,36,0,'CALLVALUE',ST,G,'CALL',1,'ADD',4,'SSTORE','STOP'])
V=10**18
gd=lambda who: sel('getDelegator(uint64,address)')+w(1)+w(int(who,16))
recs=[('take(native, R, 1 MON): PoolManager calls R with value',rec(0,pm,sel('take(address,address,uint256)')+w(0)+w(int(R,16))+w(V))),
      ('R report: byte0 DELEGATECALL, byte1 CALLCODE, byte2 STATICCALL, byte3 CALL (2 = success, 1 = failure); word1 = CALLVALUE seen',rec(1,R,'')),
      ('getDelegator(1, PoolManager)',rec(0,ST,gd(pm))),
      ('getDelegator(1, R)',rec(0,ST,gd(R))),
      ('settle{value: 1 MON} by X',rec(0,pm,sel('settle()'),V)),
      ('exttload count',rec(1,pm,sel('exttload(bytes32)')+'7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b'))]
bn=rpc('eth_blockNumber',[],URL[chain])
res=unlock_inner(chain,[r[1] for r in recs],extra={R:{'code':Rcode}},blk=bn,gas=29_000_000,g=6_000_000)
print('block',int(bn,16))
for (n,_),x in zip(recs,res): print(f'{n[:80]:80}',(x.get('ok'),x.get('rds'),x.get('ret','')[:128]) if 'ok' in x else x)
