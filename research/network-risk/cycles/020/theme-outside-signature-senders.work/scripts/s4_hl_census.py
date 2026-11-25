import json,collections,sys
from rpc import *
PM='12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
OWNER='2d09d0c2f82c59b19b3c65a48ce2c550bf0921f9'
N=int(sys.argv[1]) if len(sys.argv)>1 else 1500
out={'client_start':rpc(HYPER,'web3_clientVersion',[])}
head=int(rpc(HYPER,'eth_blockNumber',[]),16)
out['range']=[head-N+1,head]
senders=collections.Counter(); targets=collections.Counter(); hits=[]; ntx=0; errs=0
for b in range(head-N+1,head+1):
    r=rpc(HYPER,'eth_getSystemTxsByBlockNumber',[hex(b)])
    if not isinstance(r,list): errs+=1; continue
    for t in r:
        ntx+=1
        senders[t['from'].lower()]+=1; targets[(t.get('to') or '').lower()]+=1
        blob=json.dumps(t).lower()
        if PM in blob or OWNER in blob: hits.append(t)
out.update({'systemTxs':ntx,'errors':errs,'senders':senders.most_common(),'targets':targets.most_common(40),'hits':hits})
out['client_end']=rpc(HYPER,'web3_clientVersion',[])
json.dump(out,open('../raw/hl_systx_census.json','w'),indent=1)
print(ntx,errs,len(senders),len(hits)); print(senders.most_common(10))
