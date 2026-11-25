import json,sys,urllib.request,ssl
CTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
NETS={42161:("https://arb1.arbitrum.io/rpc","0x360e68faccca8ca495c1b759fd9eee466db9fb32"),
4663:("https://rpc.mainnet.chain.robinhood.com","0x8366a39cc670b4001a1121b8f6a443a643e40951"),
99901:("https://rpc.elysium.kinetiq.xyz","0xe2e105d3f7209a9da11f83ccf3e7398a753823f1")}
def batch(url,reqs):
    out=[]
    for i in range(0,len(reqs),20):
        chunk=reqs[i:i+20]
        body=json.dumps([dict(jsonrpc="2.0",id=j,method=m,params=p) for j,(m,p) in enumerate(chunk)]).encode()
        import time
        for t in range(8):
          try:
            r=urllib.request.Request(url,body,{"content-type":"application/json","user-agent":"curl/8"})
            res=json.load(urllib.request.urlopen(r,timeout=60,context=CTX)); break
          except Exception as e:
            time.sleep(3*(t+1))
        time.sleep(0.5)
        res=sorted(res,key=lambda x:x["id"])
        out+= [x.get("result",("ERR",x.get("error",{}).get("message"))) for x in res]
    return out
addrs=list(range(1,0x120))+list(range(0x800,0x820))+list(range(0xa4b000,0xa4b010))+[0xfffe,0xffff]
def A(i): return "0x%040x"%i
shapes={"empty":"0x","balanceOf":None,"transfer":None}
res={}
for cid,(url,pm) in NETS.items():
    bo="0x70a08231"+pm[2:].rjust(64,"0")
    tr="0xa9059cbb"+"00"*12+"11"*20+"%064x"%1
    reqs=[]
    for a in addrs:
        reqs.append(("eth_getCode",[A(a),"latest"]))
        reqs.append(("eth_call",[{"from":pm,"to":A(a),"data":"0x"},"latest"]))
        reqs.append(("eth_call",[{"from":pm,"to":A(a),"data":bo},"latest"]))
        reqs.append(("eth_call",[{"from":pm,"to":A(a),"data":tr},"latest"]))
    r=batch(url,reqs)
    res[cid]={A(a):r[4*k:4*k+4] for k,a in enumerate(addrs)}
json.dump(res,open(sys.argv[1],"w"),indent=0)
# print addresses where any answer is not (code 0x, result 0x)
for a in [A(x) for x in addrs]:
    row={cid:res[cid][a] for cid in res}
    if all(v==["0x","0x","0x","0x"] for v in row.values()): continue
    print(a, {c:[str(x)[:40] for x in v] for c,v in row.items()})
