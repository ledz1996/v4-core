import json
from rpc import *
from keccak import keccak256
UPG='0x'+keccak256(b'Upgraded(address)').hex()
IMPL='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)[2:]
out={'client_start':rpc(ETH,'web3_clientVersion',[])}
head=int(rpc(ETH,'eth_blockNumber',[]),16); out['head']=head
proxies={'arb1_inbox':'0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f','arb1_bridge':'0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a','arb1_seqinbox':'0x1c479675ad559dc151f6ec7ed3fbf8cee79582b6',
'rh_inbox':'0x1a07cc4bd17e0118bdb54d70990d2158abad7a2d','rh_bridge':'0xdf8755334ce7a73ccf6b581c02ea649ae3e864b3','rh_delayed2':'0xc34f4907822d1cdc6ae3038be22e6f12dea35bd4','arb1_delayed2':'0x57bd336d579a51938619271a7cc137a46d0501b1'}
logs={}
for k,a in proxies.items():
    L=[]
    start=head-400000
    step=50000
    b=start
    while b<=head:
        r=rpc(ETH,'eth_getLogs',[{'address':a,'topics':[UPG],'fromBlock':hex(b),'toBlock':hex(min(b+step-1,head))}])
        if isinstance(r,list): L+= [{'block':int(x['blockNumber'],16),'tx':x['transactionHash'],'impl':'0x'+x['topics'][1][-40:]} for x in r]
        else: L.append({'err':str(r)[:200],'from':b})
        b+=step
    logs[k]=L
out['upgradedLogs_last400k']=logs
json.dump(out,open('../raw/history.json','w'),indent=1)
print(json.dumps(out,indent=1))
