import json,urllib.request,sys,random
OFF="https://rpc.mainnet.arc.io"; SIM=sys.argv[1]; src=json.load(open(sys.argv[2])); N=int(sys.argv[3]); out=sys.argv[4]
def rpc(m,p,u):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"rpc-client"})
    return json.load(urllib.request.urlopen(r,timeout=120))
multi=sorted(src["multi"].items(),key=lambda kv:-len(kv[1]))
random.seed(39); pick=random.sample(multi,len(multi)); got=0
res=[]
for b,txh in pick:
    if got>=N: break
    b=int(b); blk=rpc("eth_getBlockByNumber",[hex(b),True],OFF)["result"]
    rc=rpc("eth_getBlockReceipts",[hex(b)],OFF)["result"]
    calls=[]
    for t in blk["transactions"]:
        c={"from":t["from"],"to":t.get("to"),"gas":t["gas"],"value":t["value"],"input":t["input"],"nonce":t["nonce"]}
        if t.get("maxFeePerGas"): c["maxFeePerGas"]=t["maxFeePerGas"]; c["maxPriorityFeePerGas"]=t["maxPriorityFeePerGas"]
        else: c["gasPrice"]=t["gasPrice"]
        if t.get("accessList"): c["accessList"]=t["accessList"]
        if t.get("authorizationList"): c["authorizationList"]=t["authorizationList"]
        if t.get("type") not in ("0x0","0x1","0x2","0x4"): c["_type"]=t.get("type")
        calls.append({k:v for k,v in c.items() if v is not None and not k.startswith("_")})
    par=rpc("eth_getBlockByNumber",[hex(b-1),False],OFF)["result"]; tm=max(int(blk["timestamp"],16),int(par["timestamp"],16)+1); tshift=tm-int(blk["timestamp"],16)
    if tshift or sum(int(t["gas"],16) for t in blk["transactions"])>int(blk["gasLimit"],16): continue
    got+=1
    capped=0
    if sum(int(c["gas"],16) for c in calls)>int(blk["gasLimit"],16):
        for c,m in zip(calls,rc):
            g=min(int(c["gas"],16),int(m["gasUsed"],16)*2+200000)
            if g<int(c["gas"],16): capped+=1
            c["gas"]=hex(g)
    gl=int(blk["gasLimit"],16)
    bo={"number":hex(b),"time":hex(tm),"gasLimit":hex(gl),"feeRecipient":blk["miner"],"baseFeePerGas":blk["baseFeePerGas"],"prevRandao":blk.get("mixHash")}
    r=rpc("eth_simulateV1",[{"blockStateCalls":[{"blockOverrides":bo,"calls":calls}],"validation":True},hex(b-1)],SIM)
    if "error" in r: res.append({"block":b,"error":r["error"]}); print(b,"ERR",r["error"]); continue
    sc=r["result"][0]["calls"]; diffs=[]
    for i,(s,m) in enumerate(zip(sc,rc)):
        ms=m["status"]; ss=s["status"]
        ml=[(l["address"].lower(),l["topics"],l["data"]) for l in m["logs"]]; sl=[(l["address"].lower(),l["topics"],l["data"]) for l in s["logs"]]
        if ms!=ss or ml!=sl or int(m["gasUsed"],16)!=int(s["gasUsed"],16): diffs.append({"i":i,"tx":m["transactionHash"],"status":[ms,ss],"gas":[m["gasUsed"],s["gasUsed"]],"logsEqual":ml==sl})
    pmtx=[i for i,m in enumerate(rc) if m["transactionHash"] in txh]
    res.append({"block":b,"tshift":tshift,"gasCapped":capped,"txs":len(calls),"pmTxIdx":pmtx,"diffs":diffs})
    print(b,len(calls),"pm",len(pmtx),"diffs",len(diffs), diffs[:2])
json.dump(res,open(out,"w"),indent=1)
