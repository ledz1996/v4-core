import json,sys
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
from swaps import SWAP
R='https://rpc.monad.xyz'
bn=int(rpc(R,'eth_blockNumber',[]),16)
r=rpc(R,'eth_getLogs',[{'address':'0x188d586ddcf52439676ca21a244753fa19f9ea8e','fromBlock':hex(bn-90),'toBlock':hex(bn-10),'topics':[SWAP]}])
print(bn, len(r))
tx=r[0]['transactionHash']
t=rpc(R,'debug_traceTransaction',[tx,{'disableStack':True,'disableMemory':True,'disableStorage':True}],timeout=120)
print(tx,str(t)[:600])
