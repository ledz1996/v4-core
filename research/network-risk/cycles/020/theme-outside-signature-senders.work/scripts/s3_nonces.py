import json
from rpc import *
nets=json.load(open('../../../../state/networks.json'))
nets = nets if isinstance(nets,list) else nets.get('networks')
out={}
for x in nets:
    if x['chainId'] not in (4326,137,56,43114,143,4217,5042,999,1): continue
    u=x['rpc'];pm=x['poolManager']
    d={'rpc':u,'pm':pm,'client_start':rpc(u,'web3_clientVersion',[])}
    d['block']=rpc(u,'eth_blockNumber',[])
    d['nonce']=rpc(u,'eth_getTransactionCount',[pm,'latest'])
    c=rpc(u,'eth_getCode',[pm,'latest']); d['codeLen']=(len(c)-2)//2 if isinstance(c,str) else c
    d['client_end']=rpc(u,'web3_clientVersion',[])
    out[x['chainId']]=d; print(x['chainId'],json.dumps(d))
json.dump(out,open('../raw/pm_nonces.json','w'),indent=1)
