import json, urllib.request, os, sys, time
from keccak import keccak256
RPC={42161:"https://arb1.arbitrum.io/rpc",4663:"https://rpc.mainnet.chain.robinhood.com",99901:"https://rpc.elysium.kinetiq.xyz"}
PM={42161:"0x360e68faccca8ca495c1b759fd9eee466db9fb32",4663:"0x8366a39cc670b4001a1121b8f6a443a643e40951",99901:"0xe2e105d3f7209a9da11f83ccf3e7398a753823f1"}
def sel(sig): return "0x"+keccak256(sig.encode())[:4].hex()
def topic(sig): return "0x"+keccak256(sig.encode()).hex()
def rpc(chain, method, params, timeout=40, retries=3):
    url = RPC[chain] if isinstance(chain,int) else chain
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,data=body,headers={"content-type":"application/json","user-agent":"curl/8"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                j=json.loads(r.read())
            return j
        except Exception as e:
            last=e; time.sleep(1+i)
    return {"error":{"message":"transport: "+str(last)}}
def call(chain,to,data,frm=None,block="latest",overrides=None):
    tx={"to":to,"data":data}
    if frm: tx["from"]=frm
    p=[tx,block]
    if overrides: p.append(overrides)
    return rpc(chain,"eth_call",p)
def pad(a): return a.lower().replace("0x","").rjust(64,"0")
