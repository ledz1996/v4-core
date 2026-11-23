# Faces among pool currencies: move one third of the PoolManager balance of token A (measuring stub at the PoolManager address,
# state override, eth_call) and read balanceOf(PoolManager) of every other listed currency before and after, and the native balance.
import json,sys
from lib import *
from harness import *
from show import dump
cid=int(sys.argv[1]); n=net(cid); pm=n['poolManager'].lower(); u=n['rpc'] if cid==4217 else 'https://arc.drpc.org'
if cid==4217:
    allt=[t['token'] for t in json.load(open('tempo_bal.json'))]
    movers=['0x20c0000000000000000000006a37da5c996874be','0x20c000000000000000000000b9537d11c60e8b50','0x20c0000000000000000000000000000000000000','0x20c000000000000000000000f047dd7018e50367','0x20c00000000000000000000014f22ca97301eb73','0x20c000000000000000000000109394a271f6aae6','0x20c0000000000000000000008ee4fcff88888888','0x20c0000000000000000000008191667423f70e67','0x20c000000000000000000000c412ec89d0c08be5']
    extra=['0x1060000000000000000000000000000000000000']
else:
    allt=[t['token'] for t in json.load(open('arc_top.json'))]
    movers=['0x3600000000000000000000000000000000000000','0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1','0x171a4217b86a807a64eb94757db6849fb4bdbaa0','0x128cc466b61f542da60c70e3aa11c10e19b84edb']
    extra=['0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6','0xc6061272419bb754a6c0386d1df81ddb3fe5cf3c','0xdc0518fa6940ecc05dbe5988a93c5a6e43fec52e','0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789','0x0000000071727de22e5e9d8baf0edac6f37da032','0x4337084d9e255ff0702461cf8895ce9e3b5ff108']
allt=sorted(set(a.lower() for a in allt+extra))
blk=rpc(u,'eth_blockNumber',[])['result']; out={}; coupled=[]
for A in movers:
    b0=rpc(u,'eth_call',[{'to':A,'data':'0x'+cd('balanceOf(address)',pm)},blk]); amt=int(b0['result'],16)//3
    others=[t for t in allt if t!=A]
    reads=[item(t,cd('balanceOf(address)',pm)) for t in others]
    items=reads+[bal(pm), item(A,cd('transfer(address,uint256)',SINK,amt))]+reads+[bal(pm), item(A,cd('balanceOf(address)',pm))]
    ov={pm:{'code':RUNNER}, B:{'code':BAL}}
    r=rpc(u,'eth_call',[{'from':FROM,'to':pm,'data':'0x'+script(0,items),'gas':hex(28_000_000)},blk,ov])
    if 'result' not in r: print(A,'ERR',json.dumps(r)[:200]); out[A]=r; continue
    rec=records(r['result']); k=len(others)
    before=rec[:k]; nat0=rec[k]; xfer=rec[k+1]; after=rec[k+2:2*k+2]; nat1=rec[2*k+2]; selfafter=rec[2*k+3]
    ch=[(t,b[1][-24:],a[1][-24:]) for t,b,a in zip(others,before,after) if b!=a]
    print(A,'moved',amt,'transfer ok',xfer[0],xfer[1][-2:],'currencies read',k,'changed',ch,'native',int(nat0[1] or '0',16),'->',int(nat1[1] or '0',16))
    out[A]={'moved':amt,'changed':ch,'native':[nat0[1],nat1[1]],'n':k}; coupled+=[(A,)+c for c in ch]
json.dump({'block':blk,'out':out},open('raw/f1_coupling_%d.json'%cid,'w'),indent=1)
print('block',int(blk,16),'coupled pairs',len(coupled))
