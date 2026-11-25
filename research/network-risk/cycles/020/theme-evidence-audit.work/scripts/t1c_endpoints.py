# Task 1: historical tag behaviour of every HyperEVM endpoint used in cycles 9-19
import json
from rpch import rpc1, PM
SLOT='0x3560a660714f0d0c98e12a3b78ac746a58a70fa1b2a2bc710b3e8f7bb8570687'
EPS=['https://rpc.hyperliquid.xyz/evm','https://rpc.purroofgroup.com','https://rpc.hypurrscan.io','https://rpc.hyperlend.finance','https://hyperliquid.drpc.org']
out={}
for u in EPS:
    r={}
    for b in (50000000, 52099613, 52099614):
        tag=hex(b)
        r[b]={'storage':rpc1(u,'eth_getStorageAt',[PM,SLOT,tag]),
              'call':rpc1(u,'eth_call',[{'to':PM,'data':'0x1e2eaeaf'+SLOT[2:]},tag]),
              'balance':rpc1(u,'eth_getBalance',[PM,tag])}
    out[u]=r
    for b,v in r.items():
        print(u,b,{k:(str(x[1])[:70] if isinstance(x,list) else str(x)[:120]) for k,x in v.items()}, (v['storage'][0] if isinstance(v['storage'],list) else ''))
json.dump(out,open('../out/t1c_endpoints.json','w'),indent=1)
