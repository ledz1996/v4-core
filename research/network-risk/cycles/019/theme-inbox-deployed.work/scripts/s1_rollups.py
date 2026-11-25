import json,sys
from rpc import *
from keccak import keccak256
def sel(s): return '0x'+keccak256(s.encode()).hex()[:8]
assert keccak256(b'').hex().startswith('c5d2460186f7233c')
IMPL='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)[2:]
ADMIN='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.admin'),'big')-1)[2:]
chains={42161:(ETH,'0x4DCeB440657f21083db8aDd07665f8ddBe1DCfc0'),4663:(ETH,'0x23a19d23e89166adedbdcb432518ab01e4272d94'),99901:(HYPER,'0x508C173dFe5F737B3493195Bf785d71fA76fD217')}
out={}
for url in (ETH,HYPER): out['client_'+url]=rpc(url,'web3_clientVersion',[]); out['block_'+url]=rpc(url,'eth_blockNumber',[])
for cid,(url,rollup) in chains.items():
    d={'rollup':rollup}
    for f in ('inbox()','bridge()','sequencerInbox()','outbox()','owner()','wasmModuleRoot()','validatorWhitelistDisabled()'):
        d[f]=addr(call(url,rollup,sel(f))) if f not in('wasmModuleRoot()','validatorWhitelistDisabled()') else call(url,rollup,sel(f))
    for k in ['rollup','inbox()','bridge()','sequencerInbox()','outbox()']+['L:'+x for x in []]:
        a=d[k] if k=='rollup' else d[k]
        if not (isinstance(a,str) and len(a)==42): continue
        d[k+'_impl']=addr(rpc(url,'eth_getStorageAt',[a,IMPL,'latest']))
        d[k+'_admin']=addr(rpc(url,'eth_getStorageAt',[a,ADMIN,'latest']))
    b=d['bridge()']
    # delayed inbox / outbox lists
    for lst in ('allowedDelayedInboxList(uint256)','allowedOutboxList(uint256)'):
        L=[]
        for i in range(20):
            r=call(url,b,sel(lst)+hex(i)[2:].rjust(64,'0'))
            if not(isinstance(r,str) and r.startswith('0x') and len(r)==66): break
            L.append(addr(r))
        d[lst]=L
    for a in d['allowedDelayedInboxList(uint256)']+d['allowedOutboxList(uint256)']:
        d['allowed?'+a]=[call(url,b,sel('allowedDelayedInboxes(address)')+a[2:].lower().rjust(64,'0')),call(url,b,sel('allowedOutboxes(address)')+a[2:].lower().rjust(64,'0'))]
    for a in d['allowedDelayedInboxList(uint256)']+d['allowedOutboxList(uint256)']:
        d['impl?'+a]=addr(rpc(url,'eth_getStorageAt',[a,IMPL,'latest']))
        d['admin?'+a]=addr(rpc(url,'eth_getStorageAt',[a,ADMIN,'latest']))
        d['codelen?'+a]=(len(rpc(url,'eth_getCode',[a,'latest']))-2)//2
    out[cid]=d
for url in (ETH,HYPER): out['client_end_'+url]=rpc(url,'web3_clientVersion',[])
json.dump(out,open('../raw/rollups.json','w'),indent=1); print(json.dumps(out,indent=1))
