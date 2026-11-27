import json,urllib.request,sys
OFF="https://rpc.mainnet.arc.io"; SIM="https://arc-rpc.publicnode.com"
def rpc(m,p,u):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"rpc-client"})
    return json.load(urllib.request.urlopen(r,timeout=120))
b=int(sys.argv[1]); idx=int(sys.argv[2]); shift=int(sys.argv[3])
blk=rpc("eth_getBlockByNumber",[hex(b),True],OFF)["result"]; rc=rpc("eth_getBlockReceipts",[hex(b)],OFF)["result"]
calls=[]
for t in blk["transactions"][:idx+1]:
    c={"from":t["from"],"to":t.get("to"),"gas":t["gas"],"value":t["value"],"input":t["input"],"nonce":t["nonce"]}
    if t.get("maxFeePerGas"): c["maxFeePerGas"]=t["maxFeePerGas"]; c["maxPriorityFeePerGas"]=t["maxPriorityFeePerGas"]
    else: c["gasPrice"]=t["gasPrice"]
    calls.append({k:v for k,v in c.items() if v is not None})
bo={"number":hex(b),"time":hex(int(blk["timestamp"],16)+shift),"gasLimit":blk["gasLimit"],"feeRecipient":blk["miner"],"baseFeePerGas":blk["baseFeePerGas"],"prevRandao":blk["mixHash"]}
r=rpc("eth_simulateV1",[{"blockStateCalls":[{"blockOverrides":bo,"calls":calls}],"validation":True},hex(b-1)],SIM)["result"][0]["calls"]
print("block ts",int(blk["timestamp"],16),hex(int(blk["timestamp"],16)))
for a,s in zip(rc[idx]["logs"],r[idx]["logs"]):
    if (a["topics"],a["data"],a["address"].lower())!=(s["topics"],s["data"],s["address"].lower()):
        print("addr",a["address"],s["address"]); print(" mined",a["topics"],a["data"]); print(" sim  ",s["topics"],s["data"])
