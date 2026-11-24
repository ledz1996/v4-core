import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
for cid, urls in {143:['https://rpc3.monad.xyz','https://rpc1.monad.xyz','https://rpc-mainnet.monadinfra.com','https://rpc.monad.xyz'],4326:['https://mainnet.megaeth.com/rpc'],999:['https://rpc.hyperliquid.xyz/evm','https://hyperliquid.drpc.org','https://rpc.hypurrscan.io']}.items():
  for u in urls:
    try:
      b=int(rpc(u,'eth_blockNumber',[],timeout=30),16)
    except Exception as e: print(cid,u,'blockNumber err',str(e)[:100]); continue
    print(cid,u,b)
