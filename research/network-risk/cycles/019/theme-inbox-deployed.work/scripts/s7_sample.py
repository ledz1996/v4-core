import json
from rpc import *
I='0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
def first_code(url,a,lo,hi):
    # binary search block where code first appears
    while hi-lo>1:
        m=(lo+hi)//2
        c=rpc1(url,'eth_getCode',[a,hex(m)])
        if isinstance(c,str) and len(c)>2: hi=m
        elif isinstance(c,str): lo=m
        else: return ('err',str(c)[:100],m)
    return hi
out={}
for name,url,a,lo in [('ely_inbox',HYPER,'0xce59f8b65ad41c9dae4c07a0571a39824bd92cff',1),('rh_inbox','https://eth.drpc.org','0x1a07cc4bd17e0118bdb54d70990d2158abad7a2d',20000000),('ely_bridge',HYPER,'0x503d572157113faaad4dbed2647bb10b949216b6',1),('rh_bridge','https://eth.drpc.org','0xdf8755334ce7a73ccf6b581c02ea649ae3e864b3',20000000)]:
    head=int(rpc1(url,'eth_blockNumber',[]),16)
    fc=first_code(url,a,lo,head)
    d={'client':rpc1(url,'web3_clientVersion',[]),'head':head,'firstCodeBlock':fc,'samples':{}}
    if isinstance(fc,int):
        for i in range(25):
            b=fc+(head-fc)*i//24
            d['samples'][b]=addr(rpc1(url,'eth_getStorageAt',[a,I,hex(b)]))
    d['client_end']=rpc1(url,'web3_clientVersion',[])
    out[name]=d
    print(name, json.dumps(d)[:1500])
json.dump(out,open('../raw/impl_samples.json','w'),indent=1)
