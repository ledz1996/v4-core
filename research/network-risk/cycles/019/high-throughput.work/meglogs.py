import json, sys, urllib.request
R='https://mainnet.megaeth.com/rpc'; PM='0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m,p):
    rq=urllib.request.Request(R,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8.5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
lo,hi=int(sys.argv[1]),int(sys.argv[2]); step=int(sys.argv[3]) if len(sys.argv)>3 else 2000
blocks={}; b=lo
while b<=hi:
    e=min(hi,b+step-1); r=rpc('eth_getLogs',[{'address':PM,'fromBlock':hex(b),'toBlock':hex(e)}])
    if 'error' in r: print('err',b,e,r['error']); step=max(100,step//2); continue
    for l in r['result']: blocks.setdefault(int(l['blockNumber'],16),set()).add(l['topics'][0][:10])
    b=e+1
json.dump({str(k):sorted(v) for k,v in sorted(blocks.items())},open(sys.argv[4] if len(sys.argv)>4 else 'meglogs.json','w'))
print(len(blocks),'blocks with PM logs', sum(1 for v in blocks.values()))
