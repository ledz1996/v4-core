# Cycle 32: read-only ArbOS state, client versions and EntryPoint code on the three chains.
import json,urllib.request,sys
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
def sel(s): return keccak(s.encode()).hex()[:8]
def rpc(u,m,p):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"curl/8"})
    try:
        j=json.loads(urllib.request.urlopen(r,timeout=40).read()); return j.get('result', j.get('error'))
    except Exception as e: return 'ERR '+str(e)[:100]
urls=["https://arb1.arbitrum.io/rpc","https://rpc.mainnet.chain.robinhood.com","https://rpc.elysium.kinetiq.xyz"]
calls=[("0x000000000000000000000000000000000000006b","getScheduledUpgrade()"),("0x000000000000000000000000000000000000006b","getNativeTokenManagementFrom()"),("0x000000000000000000000000000000000000006b","getTransactionFilteringFrom()"),("0x0000000000000000000000000000000000000064","arbOSVersion()"),("0x000000000000000000000000000000000000006c","getMultiGasPricingConstraints()")]
eps={"EPv0.6":"0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789","EPv0.7":"0x0000000071727De22E5E9d8BAf0edAc6f37da032","EPv0.8":"0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108"}
for u in urls:
    b=rpc(u,"eth_getBlockByNumber",["latest",False])
    print("==",u,rpc(u,"web3_clientVersion",[]),"block",int(b['number'],16),"ts",int(b['timestamp'],16))
    for a,s in calls:
        print(s, rpc(u,"eth_call",[{"to":a,"data":"0x"+sel(s)},b['number']]))
    for n,a in eps.items():
        c=rpc(u,"eth_getCode",[a,b['number']]); print(n,a,"codeLen",(len(c)-2)//2 if isinstance(c,str) and c.startswith('0x') else c, "sha", keccak(bytes.fromhex(c[2:])).hex()[:16] if isinstance(c,str) and len(c)>2 else '')
pms={"https://arb1.arbitrum.io/rpc":"0x360e68faccca8ca495c1b759fd9eee466db9fb32","https://rpc.mainnet.chain.robinhood.com":"0x8366a39cc670b4001a1121b8f6a443a643e40951","https://rpc.elysium.kinetiq.xyz":"0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1"}
for u,a in pms.items():
    c=rpc(u,"eth_getCode",[a,"latest"]); print("PoolManager",u,a,"codeLen",(len(c)-2)//2,"keccak",keccak(bytes.fromhex(c[2:])).hex()[:16])
    print("  activationGas? ArbWasm.stylusVersion", rpc(u,"eth_call",[{"to":"0x0000000000000000000000000000000000000071","data":"0x"+sel("stylusVersion()")},"latest"]))
