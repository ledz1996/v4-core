import json, sys, urllib.request
R='https://mainnet.megaeth.com/rpc'; PM='0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m,p):
    rq=urllib.request.Request(R,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8.5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
cache={}
def bal(b):
    if b not in cache: cache[b]=int(rpc('eth_getBalance',[PM,hex(b)])['result'],16)
    return cache[b]
out=[]
def go(lo,hi):  # balance changes in (lo,hi]
    if bal(lo)==bal(hi): return
    if hi-lo==1: out.append((hi,bal(hi)-bal(lo))); return
    m=(lo+hi)//2; go(lo,m); go(m,hi)
lo,hi=int(sys.argv[1]),int(sys.argv[2])
go(lo,hi)
json.dump(out,open(sys.argv[3],'w')); print(len(out),'blocks with native balance change',bal(lo),bal(hi))
