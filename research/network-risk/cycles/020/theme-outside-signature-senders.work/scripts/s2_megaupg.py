import json
from rpc import *
from keccak import keccak256
portal='0x7f82f57F0Dd546519324392e408b01fcC7D709e8'
UPG='0x'+keccak256(b'Upgraded(address)').hex()
ADM='0x'+keccak256(b'AdminChanged(address,address)').hex()
out={'client_start':rpc(ETH,'web3_clientVersion',[])}
for name,t in [('Upgraded',UPG),('AdminChanged',ADM)]:
    r=rpc(ETH,'eth_getLogs',[{'address':portal,'topics':[t],'fromBlock':'0x1000000','toBlock':'latest'}])
    out[name]=r if not isinstance(r,list) else [{'block':int(x['blockNumber'],16),'tx':x['transactionHash'],'topics':x['topics'],'data':x['data']} for x in r]
out['client_end']=rpc(ETH,'web3_clientVersion',[])
print(json.dumps(out,indent=1)[:5000])
json.dump(out,open('../raw/megaportal_upgrades.json','w'),indent=1)
