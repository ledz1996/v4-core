import json, urllib.request
exec(open('arc_callfrom.py').read().split("ov={")[0])
NCA="1800000000000000000000000000000000000000"
TOKEN="0x3600000000000000000000000000000000000000"
PM="8366a39CC670B4001A1121B8F6A443A643e40951".lower()
SINK="00000000000000000000000000000000c0ffee09"
S2="0x00000000000000000000000000000000c0ffee02"; S3="0x00000000000000000000000000000000c0ffee04"; S4="0x00000000000000000000000000000000c0ffee05"
STATIC_STUB="0x3660209003806020"+"5f37"+"5f5f91"+"5f5f355afa"+"3d5f5f3e"+"601c57"+"3d5ffd"+"5b3d5ff3"
CALLCODE_STUB="0x3660209003806020"+"5f37"+"5f5f91"+"5f5f5f355af2"+"3d5f5f3e"+"601d57"+"3d5ffd"+"5b3d5ff3"
xfer="beabacc8"+pad(PM)+pad(SINK)+pad(hex(10**12)[2:])
base={S2:{"code":DELEG_STUB},S3:{"code":STATIC_STUB},S4:{"code":CALLCODE_STUB}}
def show(r):
    if "exc" in r: return r
    if "result" in r: return "OK "+r["result"][:74]
    e=r.get("error",{}); d=(e.get("data") or "")
    try:
        if d.startswith("0x08c379a0"):
            n=int(d[10+64:10+128],16); msg=bytes.fromhex(d[10+128:10+128+2*n]).decode()
            return "REVERT "+msg
    except Exception: pass
    return "ERR "+str(e.get("message"))+" "+d[:40]
for url in ["https://rpc.mainnet.arc.io","https://arc.drpc.org"]:
    print("==",url, rpc(url,"web3_clientVersion",[]).get("result"), int(rpc(url,"eth_blockNumber",[]).get("result","0x0"),16))
    ovc=dict(base); ovc[TOKEN]={"code":CALL_STUB}
    ovs=dict(base); ovs[TOKEN]={"code":STATIC_STUB}
    ovd=dict(base); ovd[TOKEN]={"code":DELEG_STUB}
    tests=[("A control: stub at token address CALLs authority        ",ovc,"0x"+pad(NCA)+xfer),
           ("B stub at token CALLs helper, helper DELEGATECALLs       ",ovc,"0x"+pad(S2[2:])+pad(NCA)+xfer),
           ("C stub at token CALLs helper, helper uses CALLCODE       ",ovc,"0x"+pad(S4[2:])+pad(NCA)+xfer),
           ("D stub at token CALLs helper, helper uses STATICCALL     ",ovc,"0x"+pad(S3[2:])+pad(NCA)+xfer),
           ("E stub at token address STATICCALLs authority            ",ovs,"0x"+pad(NCA)+xfer),
           ("F stub at token address DELEGATECALLs authority          ",ovd,"0x"+pad(NCA)+xfer)]
    for name,ov,data in tests:
        r=rpc(url,"eth_call",[{"from":V,"to":TOKEN,"data":data},"latest",ov])
        print("  ",name,":",show(r))
