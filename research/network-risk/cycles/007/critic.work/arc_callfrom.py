import json, urllib.request, sys
RPCS=["https://rpc.mainnet.arc.io","https://arc.drpc.org"]
MC3F="522fAf9A91c41c443c66765030741e4AaCe147D0".lower()
V="0x00000000000000000000000000000000000a11ce"
M="0x00000000000000000000000000000000c0ffee01"
M2="0x00000000000000000000000000000000c0ffee02"
W="0x00000000000000000000000000000000c0ffee03"
CALL_STUB="0x3660209003806020"+"5f37"+"5f5f91"+"5f5f5f355af1"+"3d5f5f3e"+"601d57"+"3d5ffd"+"5b3d5ff3"
DELEG_STUB="0x3660209003806020"+"5f37"+"5f5f91"+"5f5f355af4"+"3d5f5f3e"+"601c57"+"3d5ffd"+"5b3d5ff3"
WHO="0x335f5260205ff3"
def pad(h): return h.rjust(64,"0")
def agg3(target):
    d="82ad56cb"+pad("20")+pad("1")+pad("20")+pad(target[2:] if target.startswith("0x") else target)+pad("0")+pad("60")+pad("4")+"deadbeef".ljust(64,"0")
    return d
def rpc(url,method,params):
    req=urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"curl/8"})
    try:
        return json.loads(urllib.request.urlopen(req,timeout=40).read())
    except Exception as e:
        return {"exc":str(e)}
ov={M:{"code":CALL_STUB},M2:{"code":DELEG_STUB},W:{"code":WHO}}
for url in RPCS:
    print("==",url, rpc(url,"web3_clientVersion",[]).get("result"), rpc(url,"eth_blockNumber",[]).get("result"))
    print(" code len MC3F", len(rpc(url,"eth_getCode",["0x"+MC3F,"latest"]).get("result","0x"))//2-1)
    # (i) V calls Multicall3From directly
    r=rpc(url,"eth_call",[{"from":V,"to":"0x"+MC3F,"data":"0x"+agg3(W)},"latest",ov]); print(" (i) direct      :",json.dumps(r)[:420])
    # (ii) V calls M (plain contract) which CALLs Multicall3From
    r=rpc(url,"eth_call",[{"from":V,"to":M,"data":"0x"+pad(MC3F)+agg3(W)},"latest",ov]); print(" (ii) via CALL   :",json.dumps(r)[:420])
    # (iii) V calls M2 which DELEGATECALLs Multicall3From code
    r=rpc(url,"eth_call",[{"from":V,"to":M2,"data":"0x"+pad(MC3F)+agg3(W)},"latest",ov]); print(" (iii) via DELEG :",json.dumps(r)[:420])
    # control: V calls M which CALLs W directly
    r=rpc(url,"eth_call",[{"from":V,"to":M,"data":"0x"+pad(W[2:])+"deadbeef"},"latest",ov]); print(" control M->W    :",json.dumps(r)[:200])
