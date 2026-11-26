"""Re-read the blocks whose finalized re-read was rate limited in monad_heads.json. Usage: monad_recheck.py IN OUT"""
import json,sys,time,urllib.request,urllib.error
U="https://rpc.monad.xyz"
def rpc(m,p):
    for i in range(8):
        try:
            r=urllib.request.urlopen(urllib.request.Request(U,json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),{"Content-Type":"application/json","User-Agent":"rpc-probe"}),timeout=20)
            return json.loads(r.read())["result"]
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            time.sleep(3*(i+1))
d=json.load(open(sys.argv[1])); out={"cvStart":rpc("web3_clientVersion",[]),"finalized":int(rpc("eth_getBlockByNumber",["finalized",False])["number"],16),"rows":[]}
for m in d["mismatches"]:
    b=rpc("eth_getBlockByNumber",[hex(m["number"]),False]); time.sleep(1)
    out["rows"].append({"number":m["number"],"hashAtLatest":m["hash"],"hashNow":b["hash"],"equal":b["hash"]==m["hash"]})
out["cvEnd"]=rpc("web3_clientVersion",[]); json.dump(out,open(sys.argv[2],"w"),indent=1); print(out)
