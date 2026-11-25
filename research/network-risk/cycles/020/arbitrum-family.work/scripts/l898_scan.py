# Scan Upgraded(address) logs on the four Elysium bridge proxies on HyperEVM, 1000-block windows, batched.
import json,sys,urllib.request,ssl,time
CTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
U="https://rpc.hyperliquid.xyz/evm"
A=["0xce59f8b65ad41c9dae4c07a0571a39824bd92cff","0x503d572157113faaad4dbed2647bb10b949216b6","0x37c92ba3796febe10a1bd2494a7e6e5357a3e1fb","0x7f3ff53aecb87261206ad3bdc27a88b6d8420fa6"]
T=["0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b","0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f"] # Upgraded, AdminChanged
def post(body):
    for t in range(10):
        try:
            r=urllib.request.Request(U,json.dumps(body).encode(),{"content-type":"application/json","user-agent":"curl/8"})
            return json.load(urllib.request.urlopen(r,timeout=60,context=CTX))
        except Exception as e:
            time.sleep(2*(t+1))
    raise SystemExit("rpc failed")
start=int(sys.argv[1]); head=int(post(dict(jsonrpc="2.0",id=0,method="eth_blockNumber",params=[]))["result"],16)
logs=[];windows=0;errs=[]
b=start
while b<=head:
    q=dict(jsonrpc="2.0",id=b,method="eth_getLogs",params=[{"address":A,"topics":[T],"fromBlock":hex(b),"toBlock":hex(min(b+999,head))}])
    for t in range(30):
        x=post(q)
        if "result" in x: logs+=x["result"]; windows+=1; break
        time.sleep(1.5*(t+1))
    else: errs.append((b,x.get("error")))
    b+=1000
    time.sleep(0.25)
json.dump(dict(start=start,head=head,windows=windows,errors=errs,logs=logs),open(sys.argv[2],"w"),indent=0)
print("windows",windows,"errors",len(errs),"logs",len(logs))
for l in logs: print(int(l["blockNumber"],16),l["address"],l["topics"][0][:10],l["topics"][1] if len(l["topics"])>1 else l["data"][:66])
