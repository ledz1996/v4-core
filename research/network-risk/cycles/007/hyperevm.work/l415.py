from lib import *
import concurrent.futures as cf
mb=json.load(open('raw/multi_blocks.json'))
pm=PM.lower()
def flat(c,out,ok=True):
    ok = ok and not c.get('error')
    if (c.get('to') or '').lower()==pm and ok and c.get('type')=='CALL':
        out.append((c.get('input','')[:74],int(c.get('value','0x0'),16)))
    for s in c.get('calls',[]): flat(s,out,ok)
def analyse(h):
    try: r=rpc('debug_traceTransaction',[h,{'tracer':'callTracer'}],url=ARCH)
    except Exception as e: return h,None,str(e)[:100]
    seq=[]; flat(r,seq)
    synced=None; native_wo_sync=False; seen_sync=False; nsync=0
    for inp,val in seq:
        s=inp[:10]
        if s=='0xa5841194':
            a=int(inp[10:74] or '0',16); synced=a if a else None; seen_sync=True; nsync+=1
        elif s in('0x11da60b4','0x3dd45adb'):
            if val>0 and synced is None: native_wo_sync = native_wo_sync or (not seen_sync)
            synced=None
    return h,{'leftover':hex(synced) if synced else None,'native_settle_without_prior_sync':native_wo_sync,'nsync':nsync,'ncalls':len(seq),'failed':bool(r.get('error'))},None
jobs=[(b,h,i) for b,t in mb.items() for h,i in t]
res={}
with cf.ThreadPoolExecutor(6) as ex:
    for (b,h,i),(hh,a,err) in zip(jobs,ex.map(lambda j:analyse(j[1]),jobs)):
        res.setdefault(b,[]).append((i,h,a,err))
json.dump(res,open('raw/l415.json','w'))
tot=sum(len(v) for v in res.values()); errs=sum(1 for v in res.values() for x in v if x[2] is None)
left=[(b,x) for b,v in res.items() for x in v if x[2] and x[2]['leftover']]
nat=[(b,x) for b,v in res.items() for x in v if x[2] and x[2]['native_settle_without_prior_sync']]
print('traced',tot,'errors',errs,'txs ending with a stale token sync',len(left),'txs with native settle and no sync of their own',len(nat))
hit=0
for b,v in res.items():
    v=sorted(v)
    for k,x in enumerate(v):
        if x[2] and x[2]['leftover']:
            later=[y for y in v[k+1:] if y[2] and y[2]['native_settle_without_prior_sync']]
            print('block',b,'stale sync in tx index',x[0],x[1],'later native settles:',[(y[0],y[1],y[2]['failed']) for y in later]); hit+=len(later)
print('pairs found',hit)
# also same-block pairs where an earlier tx used the PM and a later one settled native without sync (shows nothing about sync, listed for count)
print('blocks where a later tx settles native without its own sync after any earlier PM tx:',sum(1 for b,v in res.items() if any(y[2] and y[2]['native_settle_without_prior_sync'] for y in sorted(v)[1:])))
