# Task 1: does each tag-honouring endpoint honour the tag on every request (load balancers may mix backends)?
import json, time
from rpch import rpc1, PM
SLOT='0x3560a660714f0d0c98e12a3b78ac746a58a70fa1b2a2bc710b3e8f7bb8570687'
B1=hex(52099613)
OLD='0x00000000000000000002615400000000000009863e430ca554c8e389c887919f'
out={}
for u in ['https://hyperliquid.drpc.org','https://rpc.hyperlend.finance','https://rpc.purroofgroup.com']:
    rows=[]
    for i in range(20):
        r=rpc1(u,'eth_getStorageAt',[PM,SLOT,B1])
        rows.append(r if isinstance(r,list) else [None,str(r)[:100],None])
        time.sleep(1.5)
    ok=sum(1 for r in rows if r[1]==OLD); err=sum(1 for r in rows if not (isinstance(r[1],str) and r[1].startswith('0x')))
    out[u]={'rows':rows,'historical':ok,'errors':err,'latestValue':sum(1 for r in rows if isinstance(r[1],str) and r[1].startswith('0x') and r[1]!=OLD)}
    print(u,'historical',ok,'errors',err,'other',out[u]['latestValue'],set(r[0] for r in rows))
json.dump(out,open('../out/t1d_repeat.json','w'),indent=1)
