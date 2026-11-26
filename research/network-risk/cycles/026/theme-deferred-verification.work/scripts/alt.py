import json,sys,urllib.request
def rpc(u,m,p):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),{"Content-Type":"application/json","User-Agent":"rpc-probe"}),timeout=20)
        return json.loads(r.read()).get("result")
    except Exception as e: return repr(e)[:120]
out=[]
for cid,u in [(1,"https://eth.drpc.org"),(1,"https://ethereum.publicnode.com"),(137,"https://polygon-rpc.com"),(137,"https://polygon.drpc.org")]:
    row={"chainId":cid,"url":u,"cvStart":rpc(u,"web3_clientVersion",[])}
    for t in ["latest","safe","finalized"]:
        b=rpc(u,"eth_getBlockByNumber",[t,False])
        row[t]={"number":int(b["number"],16),"ts":int(b["timestamp"],16),"hash":b["hash"]} if isinstance(b,dict) else b
    row["cvEnd"]=rpc(u,"web3_clientVersion",[])
    try: row["safeLag"]=[row["latest"]["number"]-row["safe"]["number"],row["latest"]["ts"]-row["safe"]["ts"]]; row["finLag"]=[row["latest"]["number"]-row["finalized"]["number"],row["latest"]["ts"]-row["finalized"]["ts"]]
    except Exception: pass
    print(cid,u,row["cvStart"],row.get("safeLag"),row.get("finLag")); out.append(row)
json.dump(out,open(sys.argv[1],"w"),indent=1)
