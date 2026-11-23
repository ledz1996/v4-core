# World Chain: the public RPC caps eth_getLogs at 100 blocks; the Blockscout API of the chain explorer serves logs by address and topic0 (1000 per page).
import json, requests, time, os
from lib import *
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
B='https://worldchain-mainnet.explorer.alchemy.com/api'
pm=net(480)['poolManager']; head=int(rpc(net(480)['rpc'],'eth_blockNumber',[]),16)
out=[]; pages={}
for T in (OP,AP):
    frm=0; n=0
    while True:
        for i in range(5):
            try:
                j=requests.get(B,params=dict(module='logs',action='getLogs',fromBlock=frm,toBlock=head,address=pm,topic0=T),timeout=90,headers={'user-agent':'curl/8'}).json(); break
            except Exception as e: j=None; time.sleep(3)
        r=(j or {}).get('result') or []
        n+=1
        for l in r: out.append(dict(b=int(l['blockNumber'],16),tx=l['transactionHash'],t=[x for x in l['topics'] if x],d=l['data'],li=l['logIndex']))
        print(T[:10],'page',n,'from',frm,'got',len(r),(j or {}).get('message'),flush=True)
        if len(r)<1000: break
        frm=max(int(l['blockNumber'],16) for l in r)
    pages[T]=n
seen=set(); logs=[]
for l in out:
    k=(l['tx'],l['li'])
    if k in seen: continue
    seen.add(k); logs.append(l)
json.dump(dict(chainId=480,poolManager=pm,url=B,fromBlock=0,toBlock=head,pages=pages,logs=logs),open(os.path.join(HERE,'raw','logs_480.json'),'w'))
print(len(logs))
