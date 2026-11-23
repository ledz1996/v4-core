import sys,pickle
from stubs import *
chain=int(sys.argv[1]); mode=sys.argv[2]  # full | lite
targets=[l.split()[0] for l in open(sys.argv[3]) if l.strip()]
out=sys.argv[4]
pm=PM[chain]
REC='0x00000000000000000000000000000000000ec1e0'
POOLKEY=w(0)+w(int(REC,16))+w(3000)+w(60)+w(0)
def hk(sig,args): return sel(sig)+args
PK='(address,address,uint24,int24,address)'
MLP='(int24,int24,int256,bytes32)'; SP='(bool,int256,uint160)'
mlp=w(0)+w(60)+w(0)+w(0); sp=w(1)+w(1)+w(4295128740)
emptyb=lambda off: w(off)+w(0)
hooks={
 'beforeInitialize':hk(f'beforeInitialize(address,{PK},uint160)',w(int(A,16))+POOLKEY+w(2**96)),
 'afterInitialize':hk(f'afterInitialize(address,{PK},uint160,int24)',w(int(A,16))+POOLKEY+w(2**96)+w(0)),
 'beforeAddLiquidity':hk(f'beforeAddLiquidity(address,{PK},{MLP},bytes)',w(int(A,16))+POOLKEY+mlp+emptyb(0x160)),
 'afterAddLiquidity':hk(f'afterAddLiquidity(address,{PK},{MLP},int256,int256,bytes)',w(int(A,16))+POOLKEY+mlp+w(0)+w(0)+emptyb(0x1a0)),
 'beforeRemoveLiquidity':hk(f'beforeRemoveLiquidity(address,{PK},{MLP},bytes)',w(int(A,16))+POOLKEY+mlp+emptyb(0x160)),
 'afterRemoveLiquidity':hk(f'afterRemoveLiquidity(address,{PK},{MLP},int256,int256,bytes)',w(int(A,16))+POOLKEY+mlp+w(0)+w(0)+emptyb(0x1a0)),
 'beforeSwap':hk(f'beforeSwap(address,{PK},{SP},bytes)',w(int(A,16))+POOLKEY+sp+emptyb(0x140)),
 'afterSwap':hk(f'afterSwap(address,{PK},{SP},int256,bytes)',w(int(A,16))+POOLKEY+sp+w(0)+emptyb(0x160)),
 'beforeDonate':hk(f'beforeDonate(address,{PK},uint256,uint256,bytes)',w(int(A,16))+POOLKEY+w(1)+w(1)+emptyb(0x120)),
 'afterDonate':hk(f'afterDonate(address,{PK},uint256,uint256,bytes)',w(int(A,16))+POOLKEY+w(1)+w(1)+emptyb(0x120)),
 'unlockCallback':sel('unlockCallback(bytes)')+w(0x20)+w(0),
}
V=10**12
shapes=[('empty','',0),('empty+value','',V),
        ('transfer0',sel('transfer(address,uint256)')+w(int(REC,16))+w(0),0),
        ('transfer1',sel('transfer(address,uint256)')+w(int(REC,16))+w(1),0),
        ('transfer1e18',sel('transfer(address,uint256)')+w(int(REC,16))+w(10**18),0),
        ('balanceOf',sel('balanceOf(address)')+w(int(pm,16)),0)]
if mode=='full': shapes+=[(n,d,0) for n,d in hooks.items()]
else: shapes+=[('beforeSwap',hooks['beforeSwap'],0),('afterInitialize',hooks['afterInitialize'],0)]
jobs=[]  # (target,frame,kind,shape,req,inh)
for t in targets:
    for name,data,val in shapes:
        # direct: the PoolManager address issues the call
        jobs.append((t,'direct','CALL',name,direct_req(chain,t,data,0,value=val),False))
        if val==0:
            jobs.append((t,'direct','STATICCALL',name,direct_req(chain,t,data,1),False))
        # inherited: PM -> A (value V), A -> target by each kind
        if val==0:
            jobs.append((t,'inh','CALL',name,inherited_req(chain,t,data,0,v_pm_to_a=V),True))
            jobs.append((t,'inh','STATICCALL',name,inherited_req(chain,t,data,1,v_pm_to_a=V),True))
            jobs.append((t,'inh','DELEGATECALL',name,inherited_req(chain,t,data,2,v_pm_to_a=V),True))
            jobs.append((t,'inh','CALLCODE',name,inherited_req(chain,t,data,3,v_pm_to_a=V),True))
            # callcode with a stated value that no balance backs (A has no balance, PM sends none)
            jobs.append((t,'inh','CALLCODE-unbacked',name,inherited_req(chain,t,data,3,v_pm_to_a=0,v_a_to_t=V),True))
            # delegatecall when the PoolManager sent no value
            jobs.append((t,'inh','DELEGATECALL-novalue',name,inherited_req(chain,t,data,2,v_pm_to_a=0),True))
        else:
            jobs.append((t,'inh','CALL+value',name,inherited_req(chain,t,data,0,v_pm_to_a=V,v_a_to_t=V),True))
            jobs.append((t,'inh','CALLCODE+value',name,inherited_req(chain,t,data,3,v_pm_to_a=V,v_a_to_t=V),True))
print('jobs',len(jobs),file=sys.stderr)
res=[]
BS=int(sys.argv[5]) if len(sys.argv)>5 else 40
for i in range(0,len(jobs),BS):
    chunk=jobs[i:i+BS]
    rs=batch([j[4] for j in chunk],URL[chain])
    for j,r in zip(chunk,rs):
        res.append((j[0],j[1],j[2],j[3],parse(r,j[5])))
    if (i//BS)%20==0: print(i,file=sys.stderr)
    time.sleep(0.15)
pickle.dump(res,open(out,'wb'))
