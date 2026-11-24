# Run targeted.py and battery.py arithmetic vectors, and v4math.py's pool math, through the Python
# transcription of holiman/uint256 v1.3.2 + go1.25.9 math/bits generic paths (u256py.py), using the
# opcode wrappers of go-ethereum v1.16.4 core/vm/instructions.go (opSHL/opSHR/opSAR bounds checks).
# Usage: python3 -I run_vectors.py <tools/opdiff dir> <out.json> [prim ...]
import sys,json,random,time,os
here=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,here); sys.path.insert(1,sys.argv[1])
import u256py as U
from evm import REF, MASK
import targeted, battery
def I(v): return U.toI(v)
def F(z): return U.frI(z)
def evm(op,a,b,c):
    A,B,C=I(a),I(b),I(c)
    if op=='ADD': return F(U.Add(A,B))
    if op=='SUB': return F(U.Sub(A,B))
    if op=='MUL': return F(U.Mul(A,B))
    if op=='DIV': return F(U.Div(A,B))
    if op=='SDIV': return F(U.SDiv(A,B))
    if op=='MOD': return F(U.Mod(A,B))
    if op=='SMOD': return F(U.SMod(A,B))
    if op=='ADDMOD': return F(U.AddMod(A,B,C))
    if op=='MULMOD': return F(U.MulMod(A,B,C))
    if op=='LT': return int(U.Lt(A,B))
    if op=='GT': return int(U.Gt(A,B))
    if op=='SLT':
        zs,xs=U.Sign(A),U.Sign(B)
        return int(False if (zs>=0 and xs<0) else True if (zs<0 and xs>=0) else U.Lt(A,B))
    if op=='SGT':
        zs,xs=U.Sign(A),U.Sign(B)
        return int(True if (zs>=0 and xs<0) else False if (zs<0 and xs>=0) else U.Gt(A,B))
    if op=='EQ': return int(a==b)
    if op=='ISZERO': return int(a==0)
    if op in('AND','OR','XOR','NOT'): return REF[op](a,b,c)
    if op=='BYTE': return F(U.Byte(A,B))
    if op=='SIGNEXTEND': return F(U.ExtendSign(B,A))
    if op=='SHL': return F(U.Lsh(B,a)) if a<256 else 0
    if op=='SHR': return F(U.Rsh(B,a)) if a<256 else 0
    if op=='SAR':
        if a>256: return 0 if U.Sign(B)>=0 else MASK
        return F(U.SRsh(B,a))
    if op=='DIVUP':
        return (F(U.Div(A,B))+int(F(U.Mod(A,B))>0))&MASK
    if op=='MULDIV512':
        mm=F(U.MulMod(A,B,I(MASK))); p0=F(U.Mul(A,B))
        p1=(mm-p0-int(mm<p0))&MASK; r=F(U.MulMod(A,B,C))
        return ((p1^r)+p0)&MASK
    if op=='EXP': return None
    return None
def run(V,prim,limit=None):
    U.PRIM=prim; bad=[]; n=0; per={}
    for t in V[:limit]:
        op,a,b,c=t[0],t[1],t[2],t[3]
        try: got=evm(op,a,b,c)
        except Exception as e: got='exc:'+type(e).__name__
        if got is None: continue
        exp=battery.reference(op,a,b,c,b'')
        n+=1; per[op]=per.get(op,0)+1
        if got!=exp: bad.append([op,hex(a),hex(b),hex(c),str(got),hex(exp)])
    return {'prim':prim,'ran':n,'perOp':per,'mismatch':len(bad),'first':bad[:5]}
def v4(prim,nrand=20000,tickstep=97):
    import v4math as V4
    U.PRIM=prim
    V4.mul=lambda a,b: evm('MUL',a,b,0); V4.add=lambda a,b: evm('ADD',a,b,0); V4.sub=lambda a,b: evm('SUB',a,b,0)
    V4.div=lambda a,b: evm('DIV',a,b,0); V4.shl=lambda n,x: evm('SHL',n,x,0); V4.shr=lambda n,x: evm('SHR',n,x,0)
    V4.mulmod=lambda a,b,c: evm('MULMOD',a,b,c); V4.lt=lambda a,b: evm('LT',a,b,0); V4.gt=lambda a,b: evm('GT',a,b,0)
    V4.ref_byte=lambda i,x: evm('BYTE',i,x,0); V4.ref_signextend=lambda i,x: evm('SIGNEXTEND',i,x,0); V4.ref_sar=lambda n,x: evm('SAR',n,x,0)
    R=dict(REF); R['MOD']=lambda a,b,c: evm('MOD',a,b,0); R['SGT']=lambda a,b,c: evm('SGT',a,b,0); V4.REF=R
    rnd=random.Random(1); bad=0; cnt=0
    for _ in range(nrand):
        a=rnd.getrandbits(rnd.choice((64,128,200,256))); b=rnd.getrandbits(rnd.choice((64,128,200,256))); d=rnd.getrandbits(rnd.choice((64,128,200,256))) or 1
        if (a*b)//d>MASK: continue
        cnt+=1
        if V4.mul_div(a,b,d)!=(a*b)//d or V4.mul_div_rounding_up(a,b,d)!=-((-a*b)//d): bad+=1
    for _ in range(nrand//2):
        x=rnd.getrandbits(rnd.randrange(1,257)) or 1; cnt+=1
        if V4.most_significant_bit(x)!=x.bit_length()-1 or V4.least_significant_bit(x)!=(x&-x).bit_length()-1: bad+=1
    ticks=list(range(V4.MIN_TICK,V4.MAX_TICK+1,tickstep))+list(range(-300,301))+list(range(V4.MAX_TICK-300,V4.MAX_TICK+1))+list(range(V4.MIN_TICK,V4.MIN_TICK+301))
    tb=0
    for t in ticks:
        p=V4.get_sqrt_price_at_tick(t)
        if p!=getattr(v4ref,'cache',{}).get(t,p): tb+=1
        if p<V4.MAX_SQRT_PRICE and V4.get_tick_at_sqrt_price(p)!=t: tb+=1
        if t>V4.MIN_TICK and V4.get_tick_at_sqrt_price(p-1)!=t-1: tb+=1
    return {'prim':prim,'mulDivAndBitScanCases':cnt,'bad':bad,'ticks':len(ticks),'tickBad':tb}
class v4ref: pass
if __name__=='__main__':
    out=sys.argv[2]; prims=sys.argv[3:] or ['generic','mips64','fault_mul','fault_shift']
    VT=targeted.vectors(); VB=battery.vectors()
    VB=[t for t in VB if t[0] not in ('JUMPI','KECCAK','MCOPY','CDLOAD','SIGNEXT_CHAIN','EXP')]
    # reference tick prices from v4math with EVM reference semantics (before monkeypatching)
    import v4math as V4r
    v4ref.cache={t:V4r.get_sqrt_price_at_tick(t) for t in list(range(V4r.MIN_TICK,V4r.MAX_TICK+1,97))+list(range(-300,301))+list(range(V4r.MAX_TICK-300,V4r.MAX_TICK+1))+list(range(V4r.MIN_TICK,V4r.MIN_TICK+301))}
    res={'targetedVectors':len(VT),'batteryArithVectors':len(VB),'runs':[]}
    for p in prims:
        t0=time.time()
        lim=None if not p.startswith('fault') else None
        r1=run(VT,p,lim); r2=run(VB,p,lim)
        r3=v4(p, 20000 if not p.startswith('fault') else 2000, 97 if not p.startswith('fault') else 997)
        res['runs'].append({'targeted':r1,'battery':r2,'v4math':r3,'seconds':round(time.time()-t0)})
        print(p,'targeted',r1['ran'],r1['mismatch'],'battery',r2['ran'],r2['mismatch'],'v4math',r3,flush=True)
        json.dump(res,open(out,'w'),indent=1)
