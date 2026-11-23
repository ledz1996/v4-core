from lib import *
import concurrent.futures as cf,sys
head=int(rpc('eth_blockNumber',[],url=ARCH),16)
T={'Received':'0x88a5966d370b9919b20f3e2c13ff65706f196a4e32cc2c12bf57088f88525874','RawAction':'0x8c7f585fb295f7eb1e6aeb8fba61b23a4fe60beda405f0045073b185c74412e3'}
SYS={'Received':'0x2222222222222222222222222222222222222222','RawAction':'0x3333333333333333333333333333333333333333'}
def scan(args):
    name,a,b=args
    try:
        r=rpc('eth_getLogs',[{'fromBlock':hex(a),'toBlock':hex(b),'topics':[T[name]]}],url=ARCH,raw=True)
    except Exception as e: return (name,a,b,None,str(e)[:100])
    if 'error' in r:
        if b-a>2000:
            m=(a+b)//2; x=scan((name,a,m)); y=scan((name,m+1,b))
            if x[3] is None or y[3] is None: return (name,a,b,None,'sub')
            return (name,a,b,x[3]+y[3],x[4]+y[4])
        return (name,a,b,None,str(r['error'])[:100])
    L=r['result']
    return (name,a,b,[l for l in L if l['address'].lower()!=SYS[name]],len(L))
jobs=[('Received',a,min(a+49999,head)) for a in range(0,head+1,50000)]+[('RawAction',a,min(a+9999,head)) for a in range(head-600000,head+1,10000)]
out={'Received':[],'RawAction':[]};tot={'Received':0,'RawAction':0};bad=[]
with cf.ThreadPoolExecutor(6) as ex:
    for name,a,b,L,cnt in ex.map(scan,jobs):
        if L is None: bad.append((name,a,b,cnt)); continue
        out[name]+=L; tot[name]+=cnt
json.dump({'head':head,'foreign':out,'total':tot,'failed':bad},open('raw/forged_logs.json','w'))
print('head',head,'totals',tot,'failed windows',len(bad))
for n in out:
    em={}
    for l in out[n]: em[l['address']]=em.get(l['address'],0)+1
    print(n,'foreign logs',len(out[n]),em)
