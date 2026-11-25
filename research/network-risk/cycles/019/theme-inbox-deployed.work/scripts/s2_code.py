import json,os
from rpc import *
impls={'arb1_inbox':(ETH,'0x7c058ad1d0ee415f7e7f30e62db1bcf568470a10'),'arb1_delayed2':(ETH,'0x6d576e220cb44c3e8ef75d0efbeb1ff041e2e4a5'),
'rh_inbox':(ETH,'0x8d3b93dffff4842e7b61fb553b383db2c6bc91c6'),'rh_delayed2':(ETH,'0x796fee4adced1cb47a3e3d1b6925472f8fc8f1f9'),
'ely_inbox':(HYPER,'0x748c47ee3702bd88f0906a0d655d2a35a37735f4'),'ely_delayed2':(HYPER,'0xcd2fa60afe0f7f19f15c7618e370900aaa87892d'),
'arb1_bridge':(ETH,'0xfe4749061fb052c354aac65b9fb0ccd7e20d2418'),'rh_bridge':(ETH,'0xc678f7b95a7d1f77c6024c0086301d21402854b1'),'ely_bridge':(HYPER,'0xc03993205894aa8ee6889d844720ddef2bd67c51'),
'arb1_seqinbox':(ETH,'0x98a58adab0f8a66a1bf4544d804bc0475dff32c7'),'rh_seqinbox':(ETH,'0xb015d78fb9b890e96fd3e23819b2c8d9fffa3cc5'),'ely_seqinbox':(HYPER,'0x90eea97b25ae5903703222a72130b19b245dcbb5')}
os.makedirs('../raw/code',exist_ok=True)
for url in (ETH,HYPER): print(url, rpc(url,'web3_clientVersion',[]))
for k,(u,a) in impls.items():
    c=rpc(u,'eth_getCode',[a,'latest'])
    open(f'../raw/code/{k}_{a}.hex','w').write(c)
    print(k,a,(len(c)-2)//2)
for url in (ETH,HYPER): print(url, rpc(url,'web3_clientVersion',[]))
