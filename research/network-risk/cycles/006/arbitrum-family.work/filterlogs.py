from lib import *
import concurrent.futures, json
c=4663
head=int(rpc(c,"eth_blockNumber",[])["result"],16)
step=500000
T_ADD=topic("FilteredTransactionAdded(bytes32)"); T_DEL=topic("FilteredTransactionDeleted(bytes32)")
def q(a):
    b=min(a+step-1,head)
    r=rpc(c,"eth_getLogs",[{"address":"0x0000000000000000000000000000000000000074","fromBlock":hex(a),"toBlock":hex(b)}],timeout=60)
    if "result" not in r:
        # split
        out=[]
        s2=step//10
        for x in range(a,b+1,s2):
            r2=rpc(c,"eth_getLogs",[{"address":"0x0000000000000000000000000000000000000074","fromBlock":hex(x),"toBlock":hex(min(x+s2-1,b))}],timeout=60)
            if "result" not in r2: print("FAIL",x,r2); continue
            out+=r2["result"]
        return out
    return r["result"]
logs=[]
with concurrent.futures.ThreadPoolExecutor(6) as ex:
    for res in ex.map(q, range(0,head+1,step)):
        logs+=res
json.dump({"head":head,"logs":logs},open("raw/rh_filter_logs.json","w"))
add=[l for l in logs if l["topics"][0]==T_ADD]; dele=[l for l in logs if l["topics"][0]==T_DEL]
print("head",head,"logs",len(logs),"added",len(add),"deleted",len(dele),"other",len(logs)-len(add)-len(dele))
print("distinct hashes",len(set(l["topics"][1] for l in add)))
print("first",add[0]["blockNumber"],int(add[0]["blockNumber"],16),"last",int(add[-1]["blockNumber"],16))
