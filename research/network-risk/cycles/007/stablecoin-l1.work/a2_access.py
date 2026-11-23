# Arc: every storage slot a transfer out of and into the PoolManager touches, for the pooled tokens with value (eth_createAccessList, read-only).
import json,sys
from lib import *
from keccak import keccak256
cid=5042; n=net(cid); pm=n['poolManager'].lower(); u='https://arc.drpc.org'
SINK='0x7e57000000000000000000000000000000000505'; SINK2='0x7e57000000000000000000000000000000000506'
toks={'USDC':'0x3600000000000000000000000000000000000000','EURC':'0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1','cirBTC':'0x171a4217b86a807a64eb94757db6849fb4bdbaa0','WETH':'0x128cc466b61f542da60c70e3aa11c10e19b84edb'}
toks.update(dict(a.split('=') for a in sys.argv[1:]))
KNOWN={'360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc':'EIP-1967 implementation','b53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103':'EIP-1967 admin','a3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50':'EIP-1967 beacon',
 '10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b':'FiatTokenProxy admin (legacy slot)','7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3':'FiatTokenProxy implementation (legacy slot)'}
def name_slot(s, parties):
    h=s[2:].rjust(64,'0')
    if h in KNOWN: return KNOWN[h]
    if int(h,16)<1000: return 'slot %d'%int(h,16)
    for label,a in parties.items():
        for i in range(0,400):
            if keccak256(bytes.fromhex(w(a))+i.to_bytes(32,'big')).hex()==h: return 'mapping at slot %d, key %s'%(i,label)
        # namespaced (ERC-7201 style) bases are not searched
    return 'unresolved'
blk=rpc(u,'eth_blockNumber',[])['result']; out={}
for name,t in toks.items():
    bal=int(rpc(u,'eth_call',[{'to':t,'data':'0x'+cd('balanceOf(address)',pm)},blk])['result'],16)
    rows=[]
    for label,frm,to,amt in (('out 1',pm,SINK,1),('out all',pm,SINK,bal),('out third',pm,bal and SINK2,bal//3)):
        r=rpc(u,'eth_createAccessList',[{'from':frm,'to':t,'data':'0x'+cd('transfer(address,uint256)',to,amt)},blk])
        if 'result' not in r: rows.append((label,r)); continue
        al=r['result']['accessList']; parties={'PoolManager':pm,'recipient':to}
        desc=[]
        for e in al:
            ks=[(k,name_slot(k,parties) if e['address'].lower()==t else '') for k in e['storageKeys']]
            vals=[]
            for k,nm in ks:
                v=rpc(u,'eth_getStorageAt',[e['address'],k,blk]).get('result')
                vals.append((k,nm,v))
            desc.append((e['address'],vals))
        rows.append((label,int(r['result']['gasUsed'],16),r['result'].get('error'),desc))
    out[name]={'token':t,'balance':bal,'rows':rows}
    print('==',name,t,'PoolManager balance',bal)
    for row in rows:
        print('  ',row[0],row[1:3] if len(row)>2 else row[1])
        if len(row)>3:
            for a,vals in row[3]:
                print('      ',a)
                for k,nm,v in vals: print('          ',k[:20]+'..',nm,'=',v)
json.dump({'block':blk,'out':out},open('raw/a2_access.json','w'),indent=1,default=str)
