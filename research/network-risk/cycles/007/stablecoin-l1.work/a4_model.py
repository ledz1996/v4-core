# Arc: bounded search over a model of src/PoolManager.sol:279-297, 322-336, 349-364 and src/ProtocolFees.sol:44-57 with three ids over one balance:
# N = address(0) (base units), F = token face (K base units per face unit, balanceOf = floor(balance / K)), I = implementation address
# (same balanceOf, transfer always reverts). One caller. Extra moves that earlier models left out: fee collection through the open adapter
# (to a jar the caller does not own) and native value forced in without a call. K stands for 10^12.
import itertools, sys
K=4
def moves(st):
    B,S,R,dN,dF,dI,fN,fF,W,cN,cF,cI,ns = st   # balance, synced id, reserves, deltas, accrued fees, caller wallet (base units), claims, number of settles
    out=[]
    out.append(('sync F',(B,'F',B//K,dN,dF,dI,fN,fF,W,cN,cF,cI,ns)))
    out.append(('sync I',(B,'I',B//K,dN,dF,dI,fN,fF,W,cN,cF,cI,ns)))
    out.append(('sync N',(B,None,R,dN,dF,dI,fN,fF,W,cN,cF,cI,ns)))
    # settle
    if S is None:
        for v in (0,1,K):
            if W>=v: out.append(('settle value %d'%v,(B+v,S,R,dN+v,dF,dI,fN,fF,W-v,cN,cF,cI,ns+1)))
    else:
        now=B//K
        if now>=R:
            p=now-R
            out.append(('settle',(B,None,R,dN,dF+(p if S=='F' else 0),dI+(p if S=='I' else 0),fN,fF,W,cN,cF,cI,ns+1)))
    # take to the caller
    for a in (1,K):
        if B>=a: out.append(('take N %d'%a,(B-a,S,R,dN-a,dF,dI,fN,fF,W+a,cN,cF,cI,ns)))
    if B>=K: out.append(('take F 1',(B-K,S,R,dN,dF-1,dI,fN,fF,W+K,cN,cF,cI,ns)))
    out.append(('take F to self',(B,S,R,dN,dF-1,dI,fN,fF,W,cN,cF,cI,ns)))
    # pay through the face, and force base units in without a call
    if W>=K: out.append(('face transfer 1',(B+K,S,R,dN,dF,dI,fN,fF,W-K,cN,cF,cI,ns)))
    if W>=1: out.append(('force 1',(B+1,S,R,dN,dF,dI,fN,fF,W-1,cN,cF,cI,ns)))
    # fee collection by anyone (ProtocolFees.sol:49 exempts address(0) from the synced check)
    if fN>=1 and B>=1: out.append(('collect N 1',(B-1,S,R,dN,dF,dI,fN-1,fF,W,cN,cF,cI,ns)))
    if fF>=1 and S!='F' and B>=K: out.append(('collect F 1',(B-K,S,R,dN,dF,dI,fN,fF-1,W,cN,cF,cI,ns)))
    # claims
    out.append(('mint N 1',(B,S,R,dN-1,dF,dI,fN,fF,W,cN+1,cF,cI,ns)))
    out.append(('mint F 1',(B,S,R,dN,dF-1,dI,fN,fF,W,cN,cF+1,cI,ns)))
    out.append(('mint I 1',(B,S,R,dN,dF,dI-1,fN,fF,W,cN,cF,cI+1,ns)))
    if cN: out.append(('burn N 1',(B,S,R,dN+1,dF,dI,fN,fF,W,cN-1,cF,cI,ns)))
    if cF: out.append(('burn F 1',(B,S,R,dN,dF+1,dI,fN,fF,W,cN,cF-1,cI,ns)))
    return out
def value(st):
    B,S,R,dN,dF,dI,fN,fF,W,cN,cF,cI,ns=st
    return W+cN+K*cF            # claims under I have no payout path
best={}
def search(B0,depth,pre):
    W0=3*K
    start=(B0,None,0,0,0,0,2,2,W0,0,0,0,0)
    if pre: start=(B0,pre,B0//K,0,0,0,2,2,W0,0,0,0,0)   # a sync made before the unlock
    seen={start:()}; frontier=[start]; top=(0,None,None)
    for d in range(depth):
        nxt=[]
        for st in frontier:
            for name,s2 in moves(st):
                if abs(s2[3])>3*K or abs(s2[4])>3 or abs(s2[5])>3 or s2[9]>2 or s2[10]>2 or s2[11]>2: continue
                if s2 in seen: continue
                seen[s2]=seen[st]+(name,); nxt.append(s2)
                if s2[3]==0 and s2[4]==0 and s2[5]==0:           # unlock may return
                    g=value(s2)-W0
                    if g>top[0] or (g==top[0] and g>0 and top[1] is not None and len(seen[s2])<len(top[1])): top=(g,seen[s2],s2[12])
        frontier=nxt
    return top,len(seen)
for B0 in (40,41,43):
    for pre in (None,'F','I'):
        top,n=search(B0,int(sys.argv[1]) if len(sys.argv)>1 else 7,pre)
        print('start balance',B0,'pre-sync',pre,'states',n,'best gain',top[0],'base units (K=%d) with'%K,top[2],'settles; path',top[1])
# gain per settle at larger depth, one start balance
if len(sys.argv)>2:
    top,n=search(43,int(sys.argv[2]),None)
    print('depth',sys.argv[2],'states',n,'best gain',top[0],'settles',top[2],'path',top[1])
