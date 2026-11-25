# Task 2: cross-check every height's hash: across forno batches, and against celo-rpc.publicnode.com in batches of 10
import json, time
from rpch import rpcb
d=json.load(open('../out/t2_celo_heads.json'))
from collections import defaultdict
seen=defaultdict(lambda: defaultdict(list))
for b in d['batches']:
    if 'hashes' not in b: continue
    pinned = b['clientStart']==b['clientEnd']
    for h,v in b['hashes'].items(): seen[int(h)][v].append((b['clientStart'][:12],b['clientEnd'][:12],pinned))
ref={}; refc=[]
hs=sorted(seen)
for j in range(0,len(hs),10):
    chunk=hs[j:j+10]
    for t in range(5):
        r=rpcb('https://celo-rpc.publicnode.com',[('web3_clientVersion',[])]+[('eth_getBlockByNumber',[hex(h),False]) for h in chunk]+[('web3_clientVersion',[])])
        if isinstance(r,list): break
        time.sleep(3)
    if not isinstance(r,list): continue
    refc.append([r[0],r[-1]])
    for h,x in zip(chunk,r[1:-1]): ref[h]=x.get('hash') if isinstance(x,dict) else None
    time.sleep(1)
multi=[h for h in hs if len(seen[h])>1]
mism=[h for h in hs if ref.get(h) and any(v!=ref[h] for v in seen[h])]
gethpinned=sum(1 for h in hs for v,l in seen[h].items() for x in l if x[0].startswith('Geth') and x[2])
res={'heights':len(hs),'heightsWithMoreThanOneHash':multi,'refHeights':len(ref),'refClients':refc,'mismatchVsRef':mism,'gethPinnedAnswers':gethpinned}
json.dump(res,open('../out/t2b_celo_ref.json','w'),indent=1); print(json.dumps(res)[:1500])
