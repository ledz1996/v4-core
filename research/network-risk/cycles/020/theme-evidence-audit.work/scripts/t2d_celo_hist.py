# Task 2: past-block state reads from each forno backend, each read in its own pinned batch [clientVersion, read, clientVersion]
import json, time
from rpch import rpcb
U='https://forno.celo.org'; PM='0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'
tags=[hex(43985162),hex(60000000),hex(75046581),hex(83000000),'latest']
reads=[(m,t) for t in tags for m in ('eth_getCode','eth_getBalance','eth_getStorageAt')]
def params(m,t): return [PM,t] if m!='eth_getStorageAt' else [PM,'0x0',t]
res={}; stats={'req':0,'unpinned':0}
for m,t in reads:
    for n in range(60):
        have={k for k in res.get(f'{m}@{t}',{})}
        if any(h.startswith('Geth') for h in have) and any(h.startswith('reth') for h in have): break
        r=rpcb(U,[('web3_clientVersion',[]),(m,params(m,t)),('web3_clientVersion',[])]); stats['req']+=1
        if not isinstance(r,list) or r[0]!=r[2]: stats['unpinned']+=1; continue
        v=r[1]; v=((len(v)-2)//2) if (m=='eth_getCode' and isinstance(v,str)) else v
        res.setdefault(f'{m}@{t}',{}).setdefault(r[0],str(v)[:120]); time.sleep(0.3)
json.dump({'stats':stats,'reads':res},open('../out/t2d_celo_hist.json','w'),indent=1)
print(stats)
for k,v in res.items():
    vals=list(v.values()); print(k,'AGREE' if len(set(vals))==1 and len(vals)==2 else 'CHECK',{c[:12]:x[:70] for c,x in v.items()})
