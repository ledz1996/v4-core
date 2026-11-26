import json,sys,urllib.request,ssl,os
sys.path.insert(0,os.path.dirname(__file__)); from keccak import keccak256
CTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
URLS=["https://arb1.arbitrum.io/rpc","https://rpc.mainnet.chain.robinhood.com","https://rpc.elysium.kinetiq.xyz"]
def call(u,m,p):
    b=json.dumps(dict(jsonrpc="2.0",id=1,method=m,params=p)).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(u,b,{"content-type":"application/json","user-agent":"curl/8"}),timeout=40,context=CTX))
sel=lambda s:"0x"+keccak256(s.encode())[:4].hex()
for u in URLS:
    print("==",u)
    for s in ["getScheduledUpgrade()","getNativeTokenManagementFrom()","getTransactionFilteringFrom()","getAllChainOwners()"]:
        print(s,call(u,"eth_call",[{"to":"0x000000000000000000000000000000000000006b","data":sel(s)},"latest"]).get("result","ERR")[:300])
    print("arbOSVersion",call(u,"eth_call",[{"to":"0x0000000000000000000000000000000000000064","data":sel("arbOSVersion()")},"latest"]).get("result"))
    blk=call(u,"eth_getBlockByNumber",["latest",False])["result"]; print("block",int(blk["number"],16),"ts",int(blk["timestamp"],16))
