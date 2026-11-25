import json,urllib.request,sys
# eth_call to an override address whose code is GAS PUSH0 MSTORE PUSH1 32 PUSH0 RETURN; read GAS at entry for several gas limits
EPS={10:"https://mainnet.optimism.io",8453:"https://mainnet.base.org/",130:"https://mainnet.unichain.org",7777777:"https://rpc.zora.energy/",480:"https://worldchain-mainnet.g.alchemy.com/public",57073:"https://rpc-gel.inkonchain.com",1868:"https://rpc.soneium.org"}
def rpc(u,m,p):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"rpc-check"})
    return json.load(urllib.request.urlopen(r,timeout=30))
A="0x00000000000000000000000000000000000c0de1"
code="0x5a5f5260205ff3"
out={}
for c,u in EPS.items():
    row={"clientBefore":rpc(u,"web3_clientVersion",[]).get("result")}
    for g in [16_000_000,16_777_216,16_777_217,20_000_000,30_000_000]:
        try:
            r=rpc(u,"eth_call",[{"to":A,"gas":hex(g)},"latest",{A:{"code":code}}])
            row[str(g)]=int(r["result"],16) if "result" in r else r.get("error")
        except Exception as e: row[str(g)]=str(e)[:120]
    try:
        r=rpc(u,"eth_estimateGas",[{"to":A,"gas":hex(30_000_000)},"latest",{A:{"code":code}}]); row["estimate30M"]=r.get("result",r.get("error"))
    except Exception as e: row["estimate30M"]=str(e)[:120]
    row["clientAfter"]=rpc(u,"web3_clientVersion",[]).get("result")
    out[c]=row; print(c,json.dumps(row))
json.dump(out,open(sys.argv[1],"w"),indent=1)
