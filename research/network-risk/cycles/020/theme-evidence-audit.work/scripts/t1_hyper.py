# Task 1 (L-912): does rpc.hyperliquid.xyz/evm honour historical block tags?
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
import urllib.request, ssl
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpcb(url, calls):
    body=[{'jsonrpc':'2.0','id':i,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    req=urllib.request.Request(url, json.dumps(body).encode(), {'content-type':'application/json','user-agent':'rpc-client'})
    try:
        r=json.loads(urllib.request.urlopen(req, timeout=60, context=CTX).read())
    except Exception as e:
        return {'error':repr(e)}
    if isinstance(r,dict): return {'error':r}
    r=sorted(r,key=lambda x:x['id'])
    return [x.get('result', {'error':x.get('error')}) for x in r]
def rpc1(url,m,p):
    out=rpcb(url,[('web3_clientVersion',[]),(m,p),('web3_clientVersion',[])])
    return out
OFF='https://rpc.hyperliquid.xyz/evm'; ARC='https://rpc.purroofgroup.com'
PM='0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
SWAP=keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
rec={'swapTopic':SWAP}
head=int(rpc1(ARC,'eth_blockNumber',[])[1],16); rec['archiveHead']=head
# find Swap logs in recent windows on the archive endpoint
logs=[]; to=head
while len(logs)<40 and to>head-200000:
    fr=to-999
    r=rpc1(ARC,'eth_getLogs',[{'address':PM,'topics':['0x'+SWAP],'fromBlock':hex(fr),'toBlock':hex(to)}])
    if isinstance(r,list) and isinstance(r[1],list): logs+=r[1]
    else: rec.setdefault('logErr',[]).append(str(r)[:300])
    to=fr-1
rec['nlogs']=len(logs)
from collections import Counter
c=Counter(l['topics'][1] for l in logs); pid=c.most_common(1)[0][0]
bl=sorted({int(l['blockNumber'],16) for l in logs if l['topics'][1]==pid})
rec['pool']=pid; rec['blocks']=bl
slot='0x'+keccak(bytes.fromhex(pid[2:])+(6).to_bytes(32,'big')).hex()
rec['slot0Slot']=slot
# choose B1 = earliest swap block -1, B2 = latest swap block (slot0 differs)
B1=bl[0]-1; B2=bl[-1]
rec['B1']=B1; rec['B2']=B2
res={}
for name,url in (('official',OFF),('archive',ARC)):
    d={}
    for tag in (hex(B1),hex(B2),'latest'):
        d[tag]={
          'getStorageAt':rpc1(url,'eth_getStorageAt',[PM,slot,tag]),
          # extsload(bytes32) selector 0x1e2eaeaf
          'eth_call_extsload':rpc1(url,'eth_call',[{'to':PM,'data':'0x1e2eaeaf'+slot[2:]},tag]),
          'getBalance':rpc1(url,'eth_getBalance',[PM,tag]),
          'getCodeLen':(lambda r: [r[0], (len(r[1])-2)//2 if isinstance(r[1],str) else r[1], r[2]])(rpc1(url,'eth_getCode',[PM,tag])),
          'blockNumberCall':None,
        }
    res[name]=d
rec['results']=res
# also: eth_getBalance of an account created/changed recently? the PM native balance moves with native pools
json.dump(rec,open('../out/t1_hyper.json','w'),indent=1)
print(json.dumps({k:v for k,v in rec.items() if k!='results'})[:1500])
for n,d in res.items():
    for t,v in d.items(): print(n,t,{k:(x[1] if isinstance(x,list) else x) for k,x in v.items()}, v['getStorageAt'][0] if isinstance(v['getStorageAt'],list) else '')
