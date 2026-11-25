# Task 2 (L-911): which forno backend answers, its head, and the hash of 75,046,581 and twenty later heights
import json, time, random
from rpch import rpcb
U='https://forno.celo.org'
rng=random.Random(20)  # seed 20
H0=75046581
out={'seed':20,'batches':[]}
for i in range(40):
    later=[H0+k for k in (1,2,3,10,100)]+sorted(rng.sample(range(H0+1000, 83700000),15))
    calls=[('web3_clientVersion',[]),('eth_blockNumber',[]),('eth_getBlockByNumber',[hex(H0),False])]+[('eth_getBlockByNumber',[hex(h),False]) for h in later]+[('eth_blockNumber',[]),('web3_clientVersion',[])]
    r=rpcb(U,calls)
    if isinstance(r,dict): out['batches'].append({'error':str(r)[:300]}); time.sleep(2); continue
    hashes={H0:(r[2] or {}).get('hash') if isinstance(r[2],dict) else str(r[2])[:100]}
    for h,x in zip(later,r[3:3+len(later)]): hashes[h]=x.get('hash') if isinstance(x,dict) else str(x)[:100]
    b={'clientStart':r[0],'clientEnd':r[-1],'headStart':int(r[1],16) if isinstance(r[1],str) else r[1],'headEnd':int(r[-2],16) if isinstance(r[-2],str) else r[-2],'hashes':hashes}
    out['batches'].append(b); time.sleep(1)
# reference hashes from a second provider (ankr, celo-reth) for every height asked
hs=sorted({h for b in out['batches'] if 'hashes' in b for h in b['hashes']})
ref={}
for j in range(0,len(hs),40):
    chunk=hs[j:j+40]
    r=rpcb('https://rpc.ankr.com/celo',[('web3_clientVersion',[])]+[('eth_getBlockByNumber',[hex(h),False]) for h in chunk]+[('web3_clientVersion',[])])
    if isinstance(r,dict): out.setdefault('refErr',[]).append(str(r)[:200]); continue
    out.setdefault('refClients',[]).append([r[0],r[-1]])
    for h,x in zip(chunk,r[1:-1]): ref[h]=x.get('hash') if isinstance(x,dict) else None
out['ref']={str(k):v for k,v in ref.items()}
from collections import Counter
summ=Counter(); bad=[]
for b in out['batches']:
    if 'hashes' not in b: summ['error']+=1; continue
    key=(b['clientStart'],b['clientEnd'])
    summ[str(key)]+=1
    for h,v in b['hashes'].items():
        if ref.get(h) and v!=ref[h]: bad.append([b['clientStart'],h,v,ref[h]])
out['summary']={k:v for k,v in summ.items()}; out['mismatch']=bad
out['heads']=[[b['clientStart'],b['headStart'],b['headEnd']] for b in out['batches'] if 'hashes' in b]
json.dump(out,open('../out/t2_celo_heads.json','w'),indent=1)
print(json.dumps(out['summary'],indent=1)); print('mismatch',len(bad), bad[:3]); print(out.get('refClients'), out.get('refErr'))
for x in out['heads']: print(x)
