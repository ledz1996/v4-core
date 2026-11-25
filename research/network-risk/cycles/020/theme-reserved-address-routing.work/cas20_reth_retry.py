# One paced pass on bsc-rpc.publicnode.com (reth-bsc) for the Jenner + code-override cells; 403 answers are recorded as refusals.
import json,sys,time
sys.path.insert(0,'.')
from rpc import rpc
U='https://bsc-rpc.publicnode.com'
PM='0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
def cas(o,i=1): return '0xca52'+'00'*8+'%02x'%o+('%018x'%i)
T=[cas(0),cas(1),cas(2),cas(0xff),'0xca5f000000000000000000000000000000000000','0x7020000000000000000000000000000000000001','0x7020000000000000000000000000000000000002','0x0000000000000000000000000000000000000070']
STUB='0x602a60005260206000f3'
out=[]
out.append({'clientVersion':rpc(U,'web3_clientVersion',[])})
for t in T:
  for code in (None,STUB):
    p=[{'from':PM,'to':t,'data':'0x','gas':'0x1e8480'},'latest',({t:{'code':code}} if code else {}),{'time':hex(1796697600)}]
    time.sleep(2.0)
    j=rpc(U,'eth_call',p); r=j.get('result',j.get('error',j))
    if isinstance(r,dict) and 'httperror' in r: r={'httperror':r['httperror']}
    out.append({'to':t,'code':bool(code),'result':r}); print(t,bool(code),r)
out.append({'clientVersion':rpc(U,'web3_clientVersion',[])})
print(out[0],out[-1])
json.dump(out,open('raw/cas20_reth_retry.json','w'),indent=1)
