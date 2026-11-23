from lib import *
import json, collections, concurrent.futures
c=4663
d=json.load(open("raw/rh_filter_logs.json"))
logs=d["logs"]
first={}
cnt=collections.Counter()
for l in logs:
    h=l["topics"][1]; cnt[h]+=1
    b=int(l["blockNumber"],16)
    if h not in first: first[h]=(b,l["transactionHash"])
print("adds per hash distribution",collections.Counter(cnt.values()).most_common(10))
hashes=list(first)
def gt(h):
    t=rpc(c,"eth_getTransactionByHash",[h]).get("result")
    r=rpc(c,"eth_getTransactionReceipt",[h]).get("result")
    return h,t,r
out={}
with concurrent.futures.ThreadPoolExecutor(8) as ex:
    for h,t,r in ex.map(gt,hashes):
        out[h]={"tx":t,"rc":r,"addBlock":first[h][0],"addTx":first[h][1],"adds":cnt[h]}
json.dump(out,open("raw/rh_filtered_txs.json","w"))
