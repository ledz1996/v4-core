import json,urllib.request,sys,collections
U=sys.argv[1]; PM="0x8366a39CC670B4001A1121B8F6A443A643e40951"
def rpc(m,p,u=U):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"rpc-client"})
    return json.load(urllib.request.urlopen(r,timeout=60))
head=int(rpc("eth_blockNumber",[])["result"],16)
blocks=collections.defaultdict(set); step=int(sys.argv[2]); n=int(sys.argv[3]); out=sys.argv[4]
lo=head
for i in range(n):
    a=lo-step; res=rpc("eth_getLogs",[{"address":PM,"fromBlock":hex(a),"toBlock":hex(lo-1)}])
    if "error" in res: print(res); break
    for l in res["result"]: blocks[int(l["blockNumber"],16)].add(l["transactionHash"])
    lo=a
multi={b:sorted(t) for b,t in blocks.items() if len(t)>=2}
print("head",head,"scanned",lo,head,"blocks with PM logs",len(blocks),"multi",len(multi))
json.dump({"head":head,"from":lo,"multi":multi,"counts":{b:len(t) for b,t in blocks.items()}},open(out,"w"))
