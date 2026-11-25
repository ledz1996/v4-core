import json
from rpc import *
from keccak import keccak256
FB='https://rpc.flashbots.net'
UPG='0x'+keccak256(b'Upgraded(address)').hex()
IMPL='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)[2:]
out={'client_start':rpc1(FB,'web3_clientVersion',[])}
c=26302289
logs=[]
# scan 20,000 blocks before the L1 inclusion block of the impersonated tx and 2,000 after, all Arbitrum One proxies
addrs=['0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f','0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a','0x1c479675ad559dc151f6ec7ed3fbf8cee79582b6','0x0b9857ae2d4a3dbe74ffe1d7df045bb7f96e4840','0x57bd336d579a51938619271a7cc137a46d0501b1']
for b in range(c-20000,c+2000,2000):
    r=rpc1(FB,'eth_getLogs',[{'address':addrs,'topics':[UPG],'fromBlock':hex(b),'toBlock':hex(b+1999)}])
    if isinstance(r,list): logs+=[{'block':int(x['blockNumber'],16),'addr':x['address'],'tx':x['transactionHash'],'impl':'0x'+x['topics'][1][-40:]} for x in r]
    else: logs.append({'err':str(r)[:200],'from':b})
out['logs']=logs
# implementation slot sampled over time
samp={}
for blk in [25500000,26000000,26200000,26290000,26300000,26302000,26302288,26302289,26302290,26303000,26310000,26400000,26493000]:
    samp[blk]=rpc1(FB,'eth_getStorageAt',['0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f',IMPL,hex(blk)])
out['inboxImplSlotOverTime']=samp
out['client_end']=rpc1(FB,'web3_clientVersion',[])
json.dump(out,open('../raw/upgrades_arb1.json','w'),indent=1); print(json.dumps(out,indent=1))
