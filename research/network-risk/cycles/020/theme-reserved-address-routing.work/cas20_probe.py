# Task 1 (L-907): routing of CAS20 token space addresses, with and without a Jenner block-time override,
# with and without a code override. Read-only eth_call only.
import json,sys
sys.path.insert(0,'.')
from rpc import rpc
PM='0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
EPS=['https://bsc-dataseed1.bnbchain.org','https://rpc-bsc.48.club','https://bsc-rpc.publicnode.com','https://bsc-dataseed.bnbchain.org']
def cas(ordinal,idx=1): return '0xca52'+'00'*8+'%02x'%ordinal+('%018x'%idx)
TOK=[cas(o) for o in (0x00,0x01,0x02,0xff)]+[cas(0x00,0xff),'0xca5f000000000000000000000000000000000000','0x7020000000000000000000000000000000000001','0x7020000000000000000000000000000000000002','0x0000000000000000000000000000000000000070','0xca53000000000000000000000000000000000000','0xca52000000000000000001000000000000000000']
def pad(a): return a[2:].lower().rjust(64,'0')
CALLS={'balanceOf(PM)':'0x70a08231'+pad(PM),'transfer(dead,0)':'0xa9059cbb'+pad('0x000000000000000000000000000000000000dead')+'0'*64,'empty':'0x'}
STUB='0x602a60005260206000f3'  # returns word 42
JT=hex(1796697600)
out={'seed':None,'jennerTimeOverride':JT,'records':[]}
for u in EPS:
    v0=rpc(u,'web3_clientVersion',[])
    for mode in ('pre','jenner'):
        for code in (None,STUB):
            for t in TOK:
                for n,d in CALLS.items():
                    p=[{'from':PM,'to':t,'data':d,'gas':'0x1e8480'},'latest']
                    so={t:{'code':code}} if code else {}
                    p.append(so)
                    if mode=='jenner': p.append({'time':JT})
                    j=rpc(u,'eth_call',p)
                    res=j.get('result',j.get('error',j))
                    eg=None
                    if n=='empty':
                        e=rpc(u,'eth_estimateGas',p[:1]+['latest']+p[2:])
                        eg=e.get('result',e.get('error',e))
                    out['records'].append({'ep':u,'mode':mode,'codeOverride':bool(code),'to':t,'call':n,'result':res,'estimateGas':eg})
                    print(u.split('/')[2][:16],mode,'code' if code else '----',t,n,str(res)[:70],eg if eg is None or isinstance(eg,str) else str(eg)[:60])
    v1=rpc(u,'web3_clientVersion',[])
    out['records'].append({'ep':u,'clientVersionBefore':v0,'clientVersionAfter':v1})
    print(u,v0.get('result'),v1.get('result'))
json.dump(out,open('raw/cas20_probe.json','w'),indent=1)
