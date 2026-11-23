from lib import *
import concurrent.futures as cf
d=json.load(open('raw/pm_logs.json'))
pm=PM.lower()
txs={}
for l in d['logs']: txs[l['transactionHash']]=(int(l['blockNumber'],16),int(l['transactionIndex'],16))
def flat(c,out,ok=True):
    ok = ok and not c.get('error')
    if (c.get('to') or '').lower()==pm and ok and c.get('type')=='CALL':
        out.append((c.get('input','')[:74],int(c.get('value','0x0'),16)))
    for s in c.get('calls',[]): flat(s,out,ok)
def summarize(seq):
    synced=None; seen=False; nat=False
    for inp,val in seq:
        s=inp[:10]
        if s=='0xa5841194':
            a=int(inp[10:74] or '0',16); synced=a if a else None; seen=True
        elif s in('0x11da60b4','0x3dd45adb'):
            if val>0 and not seen: nat=True
            synced=None
    return synced,nat
def analyse(h):
    try: r=rpc('debug_traceTransaction',[h,{'tracer':'callTracer'}],url=ARCH)
    except Exception as e: return h,None
    seq=[]; flat(r,seq); return h,summarize(seq)
res={}
with cf.ThreadPoolExecutor(6) as ex:
    for h,a in ex.map(analyse,list(txs)): res[h]=a
err=[h for h,a in res.items() if a is None]
stale=[h for h,a in res.items() if a and a[0]]
native=[h for h,a in res.items() if a and a[1]]
print('PM txs traced',len(res),'errors',len(err),'ending with stale token sync',len(stale),'native settle without own sync',len(native))
cand=sorted({txs[h] for h in native if txs[h][1]>0})
print('native settles not first in block:',len(cand))
found=[]; checked=0
def blocktrace(bi):
    b,i=bi
    try: r=rpc('debug_traceBlockByNumber',[hex(b),{'tracer':'callTracer'}],url=ARCH)
    except Exception as e: return bi,None
    out=[]
    for k,t in enumerate(r[:i]):
        seq=[]; flat(t.get('result',{}),seq)
        if seq: out.append((k,summarize(seq)[0],len(seq)))
    return bi,out
with cf.ThreadPoolExecutor(4) as ex:
    for bi,out in ex.map(blocktrace,cand):
        checked+=1
        if out is None: print('block trace failed',bi); continue
        st=[o for o in out if o[1]]
        if out: found.append((bi,out))
        if st: print('HIT block',bi,'earlier tx with stale sync',st)
print('blocks checked',checked,'blocks where an earlier tx called the PoolManager at all',len(found),'with a stale sync',sum(1 for bi,o in found if any(x[1] for x in o)))
json.dump({'stale':stale,'native':native,'cand':cand,'found':found,'errors':err},open('raw/l415b.json','w'))
