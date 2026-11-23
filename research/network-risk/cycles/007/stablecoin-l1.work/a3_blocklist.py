# Arc: what one USDC blocklist entry for the PoolManager address stops. The PoolManager is an inner caller here:
# a measuring stub is placed at its address by state override and called from another account. Read-only eth_call.
import json
from lib import *
from harness import *
from show import dump
from keccak import keccak256
u='https://arc.drpc.org'; n=net(5042); pm=n['poolManager'].lower()
NCC='0x1800000000000000000000000000000000000001'; USDC='0x3600000000000000000000000000000000000000'
WETH='0x128cc466b61f542da60c70e3aa11c10e19b84edb'; EURC='0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1'; CBTC='0x171a4217b86a807a64eb94757db6849fb4bdbaa0'
slot='0x'+keccak256(bytes.fromhex(w(pm))+(2).to_bytes(32,'big')).hex()
items=[item(SINK,'',1), item(USDC,cd('transfer(address,uint256)',SINK,1)), item(WETH,cd('transfer(address,uint256)',SINK,1)),
       item(EURC,cd('transfer(address,uint256)',SINK,1)), item(CBTC,cd('transfer(address,uint256)',SINK,1)),
       item(USDC,cd('balanceOf(address)',pm)), item(WETH,cd('balanceOf(address)',pm))]
labels=['native send 1 wei','USDC face transfer 1','WETH transfer 1','EURC transfer 1','cirBTC transfer 1','USDC balanceOf','WETH balanceOf']
blk=rpc(u,'eth_blockNumber',[])['result']; out={}
for name,extra in (('today',{}),('PoolManager on the USDC blocklist',{NCC:{'stateDiff':{slot:'0x'+'0'*63+'1'}}})):
    ov={pm:{'code':RUNNER}}; ov.update(extra)
    r=rpc(u,'eth_call',[{'from':FROM,'to':pm,'data':'0x'+script(0,items),'gas':hex(5_000_000)},blk,ov]); out[name]=r
    print('==',name, int(blk,16))
    if 'result' in r:
        for l,line in zip(labels,dump(r['result'])): print('   %-24s %s'%(l,line))
    else: print(r)
# inbound side: a holder pays the PoolManager while it is listed (real PoolManager code, stub at a holder address)
H='0x77777777dcc4d5a8b6e418fd04d8997ef11000ee'
items2=[item(USDC,cd('transfer(address,uint256)',pm,1)), item(pm,cd('settle()'),10**12), item(WETH,cd('transfer(address,uint256)',pm,0)), item(EURC,cd('transfer(address,uint256)',pm,0))]
for name,extra in (('today',{}),('PoolManager on the USDC blocklist',{NCC:{'stateDiff':{slot:'0x'+'0'*63+'1'}}})):
    ov={H:{'code':RUNNER,'balance':hex(10**20)}}; ov.update(extra)
    r=rpc(u,'eth_call',[{'from':FROM,'to':H,'data':'0x'+script(0,items2),'gas':hex(5_000_000)},blk,ov]); out['in '+name]=r
    print('== inbound,',name)
    if 'result' in r:
        for l,line in zip(['USDC face transfer to PM','value call to settle (locked, so it reverts either way)','WETH transfer 0 to PM','EURC transfer 0 to PM'],dump(r['result'])): print('   %-58s %s'%(l,line))
    else: print(r)
json.dump({'block':blk,'out':out},open('raw/a3_blocklist.json','w'),indent=1)
