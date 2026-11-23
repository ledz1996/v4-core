from lib import *
import pickle
chain=4326; pm=PM[chain]
T0='0x'+keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
head=int(rpc('eth_blockNumber',[],MEGA),16)
logs=[]; step=50000; b=head
lo=head-6_000_000
while b>lo:
    a=max(lo,b-step+1)
    r=rpc('eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(a),'toBlock':hex(b)}],MEGA,raw=True)
    if 'error' in r:
        print('err',a,b,str(r['error'])[:150]); step//=2
        if step<500: break
        continue
    logs+=r['result']; b=a-1
print('ModifyLiquidity logs',len(logs),'blocks',lo,head)
pickle.dump(logs,open('raw/mega_modliq_logs.pkl','wb'))
