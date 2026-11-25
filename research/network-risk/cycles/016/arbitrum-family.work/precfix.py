import json,sys,time,urllib.request,ssl
CTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
d=json.load(open(sys.argv[1]))
url="https://rpc.elysium.kinetiq.xyz"; pm="0xe2e105d3f7209a9da11f83ccf3e7398a753823f1"
bo="0x70a08231"+pm[2:].rjust(64,"0"); tr="0xa9059cbb"+"00"*12+"11"*20+"%064x"%1
def one(m,p):
    for t in range(10):
        body=json.dumps(dict(jsonrpc="2.0",id=1,method=m,params=p)).encode()
        try:
            x=json.load(urllib.request.urlopen(urllib.request.Request(url,body,{"content-type":"application/json","user-agent":"curl/8"}),timeout=60,context=CTX))
        except Exception as e:
            time.sleep(2+2*t); continue
        if "error" in x and "Rate" in x["error"].get("message",""): time.sleep(2+2*t); continue
        return x.get("result",["ERR",x.get("error",{}).get("message")])
    return ["ERR","giveup"]
n=0
for a,v in d["99901"].items():
    for k,(m,data) in enumerate([("eth_getCode",None),("eth_call","0x"),("eth_call",bo),("eth_call",tr)]):
        if isinstance(v[k],list) and "Rate" in str(v[k][1]):
            p=[a,"latest"] if m=="eth_getCode" else [{"from":pm,"to":a,"data":data},"latest"]
            v[k]=one(m,p); n+=1; time.sleep(0.25)
json.dump(d,open(sys.argv[1],"w"),indent=0)
print("refetched",n)
diff=0
for a in d["42161"]:
    r=[d[c][a] for c in ("42161","4663","99901")]
    norm=lambda v:[ (x if not isinstance(x,list) else "ERR:"+str(x[1])) for x in v]
    r=[norm(x) for x in r]
    # balanceOf / transfer data contains chain-specific PM address for echo precompiles; normalise identity (0x4)
    if r[0]!=r[2] or r[0]!=r[1]:
        diff+=1; print(a, [ [str(y)[:60] for y in x] for x in r])
print("addresses differing",diff)
