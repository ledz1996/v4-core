# Read-only: any account can initialize a fresh pool at a price of its choice on the deployed PoolManagers (OpenZeppelin M-03 precondition).
import json
from walk import NETS, rpc, EOA
from keccak import sel
PK='(address,address,uint24,int24,address)'
s=sel('initialize(%s,uint160)'%PK)
def w(x): return (x%(1<<256)).to_bytes(32,'big').hex()
out={}
for n in NETS:
    c1=0x00000000000000000000000000000000fAcE0007
    res=[]
    for price in ((1<<96), (1<<96)*1000, 4295128739, 1461446703485210103287273052203988822378723970341):
        data='0x'+s+w(0)+w(c1)+w(3000)+w(60)+w(0)+w(price)
        r=rpc(n['rpc'],'eth_call',[{'from':EOA,'to':n['poolManager'],'data':data},'latest'])
        if 'result' in r:
            v=int(r['result'],16); v=v-(1<<256) if v>>255 else v
            res.append(v)
        else: res.append('err '+json.dumps(r['error'])[:80])
    out[n['chainId']]=res; print(n['chainId'],n['name'],res)
json.dump(out,open('raw/init.json','w'),indent=1)
