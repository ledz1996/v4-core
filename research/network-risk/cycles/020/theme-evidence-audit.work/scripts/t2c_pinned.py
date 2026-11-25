# Task 2: battery.py and targeted.py vectors on forno, every chunk answered by each backend with a pinned
# bracket [web3_clientVersion, eth_call, web3_clientVersion]; a chunk counts for a backend only when both
# client strings name that backend. Vector sets are the tools' own (battery seed 20261124, targeted seed 681).
import sys, json, time, threading, concurrent.futures as cf
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
import battery as B, targeted as T
from evm import STUB
from rpch import rpcb
U='https://forno.celo.org'
RETH='reth/v2.2.0-74cc8bb'; GETH='Geth/v0.1.0-untagged-c7ed55b8'
def fam(s):
    if not isinstance(s,str): return None
    if s.startswith('reth/'): return s
    if s.startswith('Geth/'): return s
    return None
def chunks(mod):
    code=B.dispatcher(); V=mod.vectors(); out=[]
    for i in range(0,len(V),600):
        b=V[i:i+600]; d=B.encode(b); out.append((i,b,d,B.expected(b,d)))
    return code,out
jobs=[]
for name,mod in (('battery',B),('targeted',T)):
    code,ch=chunks(mod)
    for (i,b,d,e) in ch: jobs.append((name,i,code,b,d,e))
print('chunks',len(jobs),flush=True)
lock=threading.Lock(); stats={'requests':0,'unpinned':0,'errors':0}
res={}  # (name,i) -> {client: {'mismatch':[...]} }
def attempt(job):
    name,i,code,b,d,e=job
    tx={'to':STUB,'data':'0x'+d.hex()}
    r=rpcb(U,[('web3_clientVersion',[]),('eth_call',[tx,'latest',{STUB:{'code':'0x'+code.hex()}}]),('web3_clientVersion',[])])
    with lock: stats['requests']+=1
    if not isinstance(r,list) or not isinstance(r[1],str):
        with lock: stats['errors']+=1
        return None
    c0,c1=fam(r[0]),fam(r[2])
    if c0 is None or c0!=c1:
        with lock: stats['unpinned']+=1
        return None
    got=bytes.fromhex(r[1][2:])
    if len(got)!=32*len(b): return (c0,[{'short':len(got)}])
    bad=[]
    for k,(t,w) in enumerate(zip(b,e)):
        g=int.from_bytes(got[32*k:32*k+32],'big')
        if g!=w: bad.append({'op':t[0],'a':hex(t[1]),'b':hex(t[2]),'c':hex(t[3]),'got':hex(g),'want':hex(w)})
    return (c0,bad)
def need(job):
    k=(job[0],job[1]); have=res.get(k,{})
    return not (any(c.startswith('reth/') for c in have) and any(c.startswith('Geth/') for c in have))
def worker(job):
    for n in range(80):
        if not need(job): return
        a=attempt(job)
        if a:
            with lock: res.setdefault((job[0],job[1]),{}).setdefault(a[0],a[1])
        time.sleep(0.3)
t0=time.time()
with cf.ThreadPoolExecutor(6) as ex: list(ex.map(worker,jobs))
summary={'url':U,'chunks':len(jobs),'stats':stats,'seconds':round(time.time()-t0)}
per={}
for (name,i),d in res.items():
    for c,bad in d.items():
        p=per.setdefault(f'{name} | {c}',{'chunks':0,'vectors':0,'mismatches':0})
        p['chunks']+=1; p['vectors']+=600 if True else 0; p['mismatches']+=len(bad)
# exact vector counts
VB=len(B.vectors()); VT=len(T.vectors())
summary['vectorTotals']={'battery':VB,'targeted':VT}
summary['perSetAndClient']=per
summary['chunksMissingGeth']=[f'{n}:{i}' for (n,i,*_) in jobs if not any(c.startswith('Geth/') for c in res.get((n,i),{}))]
summary['chunksMissingReth']=[f'{n}:{i}' for (n,i,*_) in jobs if not any(c.startswith('reth/') for c in res.get((n,i),{}))]
summary['allMismatches']=[[n,i,c,bad] for (n,i),d in res.items() for c,bad in d.items() if bad]
json.dump(summary,open('../out/t2c_pinned.json','w'),indent=1)
print(json.dumps({k:v for k,v in summary.items() if k!='allMismatches'},indent=1)[:3000]); print('mismatch records',len(summary['allMismatches']))
