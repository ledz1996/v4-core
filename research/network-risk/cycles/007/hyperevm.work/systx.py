from lib import *
import concurrent.futures as cf,sys
head=int(rpc('eth_blockNumber',[],url=ARCH),16)
N=int(sys.argv[1]) if len(sys.argv)>1 else 3000
def get(a):
    calls=[('eth_getBlockByNumber',[hex(b),True]) for b in range(a,min(a+25,head+1))]
    for i in range(4):
        try: return batch(calls,url=ARCH)
        except Exception as e: err=e
    return []
stats={}; firstsigned_before_sys=0; nblk=0; examples={}
with cf.ThreadPoolExecutor(5) as ex:
    for js in ex.map(get,range(head-N+1,head+1,25)):
        for j in js:
            b=j.get('result')
            if not b: continue
            nblk+=1; seen_signed=False
            for t in b['transactions']:
                if int(t.get('gasPrice','0x1'),16)==0:
                    if seen_signed: firstsigned_before_sys+=1
                    k=(t['from'],t['to'],t['input'][:10],int(t['gas'],16),'value' if int(t['value'],16) else 'novalue')
                    stats[k]=stats.get(k,0)+1; examples.setdefault(k,t['hash'])
                else: seen_signed=True
print('blocks',nblk,'from',head-N+1,'to',head,'system txs',sum(stats.values()),'placed after a signed tx',firstsigned_before_sys)
agg={}
for (f,to,sel,gas,v),n in stats.items():
    fk='bridge 0x2222' if f.startswith('0x2222') else ('system 0x20..' if f.startswith('0x20000000000000000000000000000000') else f)
    k=(fk,sel,gas,v, to if sel=='0x' and False else ('linked '+to if not fk.startswith('bridge') else 'recipient'))
    agg[k]=agg.get(k,0)+n
for k,n in sorted(agg.items(),key=lambda x:-x[1])[:40]: print(n,k)
json.dump({'head':head,'N':N,'stats':[[list(k),n,examples[k]] for k,n in stats.items()]},open('raw/systx_census.json','w'))
