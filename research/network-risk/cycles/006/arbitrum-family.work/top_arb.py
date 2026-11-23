from lib import *
import gzip, json, urllib.request
c=42161
prices=json.load(gzip.open('../../005/theme-assigned-balance.work/raw/prices_42161.json.gz'))
pm=PM[c]
toks=list(prices.keys())
def batch(calls):
    body=json.dumps([{"jsonrpc":"2.0","id":i,"method":"eth_call","params":[{"to":t,"data":d},"latest"]} for i,(t,d) in enumerate(calls)]).encode()
    req=urllib.request.Request(RPC[c],data=body,headers={"content-type":"application/json","user-agent":"curl/8"})
    with urllib.request.urlopen(req,timeout=60) as r: j=json.loads(r.read())
    out=[None]*len(calls)
    if isinstance(j,dict): raise Exception(str(j)[:200])
    for x in j: out[x["id"]]=x.get("result")
    return out
bal={}
data="0x70a08231"+pad(pm)
for i in range(0,len(toks),40):
    ch=toks[i:i+40]
    try:
        res=batch([(t,data) for t in ch])
    except Exception as e:
        print("batch fail",e); res=[call(c,t,data).get("result") for t in ch]
    for t,r in zip(ch,res):
        bal[t]=int(r,16) if r and len(r)>=66 else None
rows=[]
for t,p in prices.items():
    b=bal.get(t)
    if b is None: continue
    usd=b/10**p["decimals"]*p["price"]
    rows.append((usd,t,p["symbol"],b/10**p["decimals"],p["price"],p.get("confidence")))
nb=int(rpc(c,"eth_getBalance",[pm,"latest"])["result"],16)/1e18
rows.sort(reverse=True)
json.dump({"native":nb,"rows":rows},open("raw/arb_top.json","w"))
print("native ETH",nb)
for r in rows[:30]: print("%14.0f %s %-12s %18.4f price %.6g conf %s"%r)
print("total priced usd",sum(r[0] for r in rows))
