import json, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../..'))
nets={n['chainId']:n for n in json.load(open(os.path.join(ROOT,'research/network-risk/state/networks.json')))['networks']}
def rpc(url,method,params,t=30):
    req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=t) as r: return json.load(r)
EV={('0x'+keccak(s.encode()).hex()):s.split('(')[0] for s in ['Donate(bytes32,address,uint256,uint256)','Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)','ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)','Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)','Transfer(address,address,uint256)','Transfer(address,address,address,uint256,uint256)']}
cid=int(sys.argv[1]); n=nets[cid]
for h in sys.argv[2:]:
    tx=rpc(n['rpc'],'eth_getTransactionByHash',[h])['result']; rc=rpc(n['rpc'],'eth_getTransactionReceipt',[h])['result']
    print('TX',h,'block',int(tx['blockNumber'],16),'from',tx['from'],'to',tx['to'],'value',int(tx['value'],16),'selector',tx['input'][:10],'inputlen',len(tx['input'])//2,'status',rc['status'],'gasUsed',int(rc['gasUsed'],16),'index',int(tx['transactionIndex'],16))
    for l in rc['logs']:
        name=EV.get(l['topics'][0],l['topics'][0][:10])
        d=l['data'][2:]; words=[d[i:i+64] for i in range(0,len(d),64)]
        def sint(w):
            v=int(w,16); return v-(1<<256) if v>>255 else v
        extra=''
        if name=='Swap' and l['address'].lower()==n['poolManager'].lower(): extra='a0=%d a1=%d sqrtP=%d liq=%d tick=%d fee=%d'%(sint(words[0]),sint(words[1]),int(words[2],16),int(words[3],16),sint(words[4]),int(words[5],16))
        elif name=='Donate': extra='a0=%d a1=%d sender=0x%s'%(int(words[0],16),int(words[1],16),l['topics'][2][-40:])
        elif name=='ModifyLiquidity': extra='lower=%d upper=%d dL=%d sender=0x%s'%(sint(words[0]),sint(words[1]),sint(words[2]),l['topics'][2][-40:])
        elif name=='Transfer' and len(l['topics'])==3: extra='from=0x%s to=0x%s amt=%d'%(l['topics'][1][-40:],l['topics'][2][-40:],int(words[0],16) if words else -1)
        print('   log',l['address'],name,(l['topics'][1][:14] if len(l['topics'])>1 else ''),extra)
