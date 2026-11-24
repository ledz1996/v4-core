# Read-only: wasmModuleRoot() of the Arbitrum One and Robinhood Chain rollups on Ethereum and of Elysium's rollup on HyperEVM.
import sys,json
sys.path.insert(0,sys.argv[1])
from rpc import call,sel,raw
R=[('42161','0x4DCeB440657f21083db8aDd07665f8ddBe1DCfc0','https://ethereum-rpc.publicnode.com'),
   ('4663','0x23a19d23e89166adedbdcb432518ab01e4272d94','https://ethereum-rpc.publicnode.com'),
   ('99901','0x508C173dFe5F737B3493195Bf785d71fA76fD217','https://rpc.hyperliquid.xyz/evm')]
out={}
for cid,a,rpc in R:
    b=int(raw('eth_blockNumber',[],rpc=rpc)['result'],16)
    out[cid]={'rollup':a,'rpc':rpc,'block':b,'wasmModuleRoot':call(a,sel('wasmModuleRoot()'),rpc=rpc,block=hex(b))}
    print(cid,out[cid])
json.dump(out,open(sys.argv[2],'w'),indent=1)
