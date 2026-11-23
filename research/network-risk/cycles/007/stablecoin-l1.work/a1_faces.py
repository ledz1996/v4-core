# Arc: the two faces of USDC with fee collection, self transfer and forced native value inside a sync bracket.
# Read-only eth_call with state overrides on the deployed PoolManager; nothing is sent.
import json
from lib import *
from harness import *
from show import dump
cid=5042; n=net(cid); pm=n['poolManager'].lower(); u='https://arc.drpc.org'
F='0x3600000000000000000000000000000000000000'; IMPL='0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6'; AD=n['protocolFeeController']
Z1='0x7e57000000000000000000000000000000000f11'; Z2='0x7e57000000000000000000000000000000000f12'
blk=rpc(u,'eth_blockNumber',[])['result']
Bal=int(rpc(u,'eth_getBalance',[pm,blk])['result'],16); r0=Bal%10**12
acc0=int(rpc(u,'eth_call',[{'to':pm,'data':'0x'+cd('protocolFeesAccrued(address)',0)},blk])['result'],16)
accF=int(rpc(u,'eth_call',[{'to':pm,'data':'0x'+cd('protocolFeesAccrued(address)',F)},blk])['result'],16)
print('block',int(blk,16),'native',Bal,'r0',r0,'fees native',acc0,'fees face',accF)
def collect(cur,amt): return sel('collect((address,uint256)[])')+w(0x20)+w(1)+w(cur)+w(amt)
force1=10**12-r0
inner=script(1,[
  # part A: forced native value below one face unit inside a bracket
  item(pm, cd('sync(address)', F)), tl(pm, RESERVES),                   # 0 1
  item(Z1, ''), bal(pm), item(F, cd('balanceOf(address)', pm)),         # 2 3 4  Z1 destroys itself in favour of the PoolManager
  item(pm, cd('settle()')), tl(pm, delta_slot(E, F)),                   # 5 6    credit in face units
  # part B: now the balance is a whole number of face units. A native payout of 1 wei lowers the face reading by one unit.
  item(pm, cd('take(address,address,uint256)', 0, SINK, 1)),            # 7
  item(F, cd('balanceOf(address)', pm)),                                # 8
  item(pm, cd('sync(address)', F)), tl(pm, RESERVES),                   # 9 10
  item(Z2, ''), item(F, cd('balanceOf(address)', pm)),                  # 11 12  1 wei arrives
  item(pm, cd('settle()')), tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)),   # 13 14 15
  # part C: fee collection through the open adapter inside a bracket
  item(pm, cd('sync(address)', F)), tl(pm, RESERVES),                   # 16 17
  item(AD, collect(F, 1)),                                              # 18 expect ProtocolFeeCurrencySynced
  item(AD, collect(0, 1)),                                              # 19 native fee of 1 wei leaves while the face is synced
  item(F, cd('balanceOf(address)', pm)),                                # 20
  item(pm, cd('settle()')),                                             # 21 expect Panic: reading below the synced reserves
  item(pm, cd('sync(address)', IMPL)), tl(pm, CURRENCY),                # 22 23
  item(AD, collect(F, 1)),                                              # 24 allowed: the synced id is the implementation address
  item(pm, cd('settle()')),                                             # 25 expect Panic
  # part D: self transfer and native payout to the PoolManager itself
  item(pm, cd('sync(address)', F)), tl(pm, RESERVES),                   # 26 27
  item(pm, cd('take(address,address,uint256)', F, pm, 5)),              # 28
  item(F, cd('balanceOf(address)', pm)),                                # 29
  item(pm, cd('settle()')),                                             # 30 expect 0
  item(pm, cd('take(address,address,uint256)', 0, pm, 1)),              # 31 expect revert
  item(pm, cd('take(address,address,uint256)', IMPL, SINK, 1)),         # 32 expect revert
  item(pm, cd('take(address,address,uint256)', IMPL, SINK, 0)),         # 33
  tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)), tl(pm, delta_slot(E, IMPL)),   # 34 35 36
])
outer=script(0,[ bal(pm), item(F, cd('balanceOf(address)', pm)), item(pm, unlock(inner)) ])
ov=overrides(pm, True)
ov[Z1]={'code':'0x73'+pm[2:]+'ff','balance':hex(force1)}
ov[Z2]={'code':'0x73'+pm[2:]+'ff','balance':hex(1)}
r=rpc(u,'eth_call',[{'from':FROM,'to':E,'data':'0x'+outer,'gas':hex(15_000_000)},blk,ov])
json.dump({'block':blk,'native':Bal,'r0':r0,'force1':force1,'res':r},open('raw/a1_faces.json','w'),indent=1)
print('force1',force1)
print('\n'.join(dump(r['result'])) if 'result' in r else r)
