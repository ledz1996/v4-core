"""Compare block hashes and head tags served by each forno backend (Geth and reth) at the same heights. Read-only."""
import json, urllib.request, collections
U='https://forno.celo.org'
def batch(calls):
    body=[{'jsonrpc':'2.0','id':0,'method':'web3_clientVersion','params':[]}]+[{'jsonrpc':'2.0','id':i+1,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    r=urllib.request.Request(U,data=json.dumps(body).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    res={x['id']:x.get('result') for x in json.load(urllib.request.urlopen(r,timeout=60))}
    return res[0].split('/')[0], [res[i+1] for i in range(len(calls))]
seen=collections.defaultdict(dict); tags=collections.defaultdict(list)
for k in range(60):
    who,(l,s,f)=batch([('eth_getBlockByNumber',['latest',False]),('eth_getBlockByNumber',['safe',False]),('eth_getBlockByNumber',['finalized',False])])
    tags[who].append([int(x['number'],16) if x else None for x in (l,s,f)])
    base=int(s['number'],16)
    hs=list(range(base-20,base+320,17))
    who2,bl=batch([('eth_getBlockByNumber',[hex(h),False]) for h in hs])
    for h,b in zip(hs,bl):
        if b: seen[h][who2]=b['hash']
diff=[h for h,v in seen.items() if len(set(v.values()))>1]
both=[h for h,v in seen.items() if len(v)>1]
print(json.dumps({'tagsSamples':{k:v[:3] for k,v in tags.items()},'counts':{k:len(v) for k,v in tags.items()},'heightsSeenByBoth':len(both),'heightsWithDifferentHash':diff},indent=1))
