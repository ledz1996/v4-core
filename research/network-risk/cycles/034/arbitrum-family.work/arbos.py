import json,subprocess,sys
sys.path.insert(0,'tools/opdiff')
from evm import keccak
def rpc(u,m,p):
    out=subprocess.run(['curl','-s','--max-time','40','-X','POST','-H','content-type: application/json','--data',json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}),u],capture_output=True,text=True).stdout
    try: return json.loads(out)
    except: return {'raw':out[:200]}
sel=lambda s:'0x'+keccak(s.encode()).hex()[:8]
U={42161:'https://arb1.arbitrum.io/rpc',4663:'https://rpc.mainnet.chain.robinhood.com',99901:'https://rpc.elysium.kinetiq.xyz'}
calls=[('0x0000000000000000000000000000000000000064','arbOSVersion()'),('0x000000000000000000000000000000000000006b','getScheduledUpgrade()'),('0x000000000000000000000000000000000000006b','getNativeTokenManagementFrom()'),('0x000000000000000000000000000000000000006b','getTransactionFilteringFrom()'),('0x000000000000000000000000000000000000006b','isCalldataPriceIncreaseEnabled()'),('0x000000000000000000000000000000000000006b','getNetworkFeeAccount()'),('0x000000000000000000000000000000000000006b','getAllChainOwners()'),('0x000000000000000000000000000000000000006b','getParentGasFloorPerToken()'),('0x000000000000000000000000000000000000006b','getMaxStylusContractFragments()'),('0x000000000000000000000000000000000000006b','getCollectTips()')]
out={}
for c,u in U.items():
    bn=rpc(u,'eth_blockNumber',[]).get('result')
    blk=rpc(u,'eth_getBlockByNumber',[bn,False]).get('result',{})
    r={'block':int(bn,16),'timestamp':int(blk.get('timestamp','0x0'),16),'client':rpc(u,'web3_clientVersion',[]).get('result'),'mixHash':blk.get('mixHash')}
    for a,f in calls:
        x=rpc(u,'eth_call',[{'to':a,'data':sel(f)},bn])
        r[f]=x.get('result',x.get('error',x))
    out[c]=r; print(c,json.dumps(r,indent=0))
json.dump(out,open(sys.argv[1],'w'),indent=1)
