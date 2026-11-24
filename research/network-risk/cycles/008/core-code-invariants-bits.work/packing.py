# Python transcription of the packing code as written in src/, with 256 bit EVM word semantics.
import random
from keccak import keccak256
U=(1<<256)-1
def s(x): x&=U; return x-(1<<256) if x>>255 else x          # to signed
def u(x): return x&U
def shl(n,x): return (x<<n)&U if n<256 else 0
def shr(n,x): return (x&U)>>n if n<256 else 0
def sar(n,x): return u(s(x)>>min(n,255))
def signextend(b,x):
    bits=8*(b+1); x&=(1<<bits)-1
    return u(x-(1<<bits)) if x>>(bits-1) else x
def sdiv(a,b):
    a,b=s(a),s(b)
    if b==0: return 0
    q=abs(a)//abs(b); return u(-q if (a<0)!=(b<0) else q)
def smod(a,b):
    a,b=s(a),s(b)
    if b==0: return 0
    r=abs(a)%abs(b); return u(-r if a<0 else r)
def slt(a,b): return 1 if s(a)<s(b) else 0
random.seed(88)
def dirty(v,bits): return (random.getrandbits(256-bits)<<bits)|(v&((1<<bits)-1))
bad=0
M128=(1<<128)-1
# --- BalanceDelta / BeforeSwapDelta (same layout) ---
def toBD(a0,a1): return shl(128,a0)|(M128&a1)
def amount0(d): return sar(128,d)
def amount1(d): return signextend(15,d)
I128=[-(1<<127),-(1<<127)+1,-1,0,1,(1<<127)-1]
for _ in range(200000):
    a=random.choice(I128+[random.randint(-(1<<127),(1<<127)-1)]); b=random.choice(I128+[random.randint(-(1<<127),(1<<127)-1)])
    d=toBD(dirty(u(a),128),dirty(u(b),128))
    if s(amount0(d))!=a or s(amount1(d))!=b: bad+=1
    # add/sub with checked int128 results
    c=random.choice(I128+[random.randint(-(1<<127),(1<<127)-1)]); e=random.choice(I128+[random.randint(-(1<<127),(1<<127)-1)])
    d2=toBD(u(c),u(e))
    r0=s(amount0(d))+s(amount0(d2)); r1=s(amount1(d))+s(amount1(d2))
    if (r0,r1)!=(a+c,b+e): bad+=1
print('BalanceDelta pack/unpack failures',bad)
# --- Slot0 ---
M160=(1<<160)-1;M24=(1<<24)-1
def setP(p,v): return (U^M160)&p | (M160&v)
def setT(p,v): return (U^shl(160,M24))&p | shl(160,M24&v)
def setPF(p,v): return (U^shl(184,M24))&p | shl(184,M24&v)
def setLF(p,v): return (U^shl(208,M24))&p | shl(208,M24&v)
getP=lambda p:M160&p; getT=lambda p:signextend(2,shr(160,p)); getPF=lambda p:M24&shr(184,p); getLF=lambda p:M24&shr(208,p)
bad=0
for _ in range(200000):
    P=random.getrandbits(160); T=random.randint(-(1<<23),(1<<23)-1); PF=random.getrandbits(24); LF=random.getrandbits(24)
    p=0
    order=[0,1,2,3]; random.shuffle(order)
    for o in order:
        if o==0: p=setP(p,dirty(P,160))
        if o==1: p=setT(p,dirty(u(T),24))
        if o==2: p=setPF(p,dirty(PF,24))
        if o==3: p=setLF(p,dirty(LF,24))
    if (getP(p),s(getT(p)),getPF(p),getLF(p))!=(P,T,PF,LF) or p>>232: bad+=1
    # overwrite one field leaves the rest
    P2=random.getrandbits(160); q=setP(p,P2)
    if (getP(q),s(getT(q)),getPF(q),getLF(q))!=(P2,T,PF,LF): bad+=1
    T2=random.randint(-(1<<23),(1<<23)-1); q=setT(p,u(T2))
    if (getP(q),s(getT(q)),getPF(q),getLF(q))!=(P,T2,PF,LF): bad+=1
print('Slot0 failures',bad)
# --- tick info slot packing (Pool.updateTick) ---
bad=0
for _ in range(100000):
    g=random.getrandbits(128); n=random.randint(-(1<<127),(1<<127)-1)
    w=(dirty(g,128)&M128)|shl(128,dirty(u(n),128))
    if w&M128!=g or s(sar(128,w))!=n: bad+=1
print('tick slot failures',bad)
# --- LiquidityMath.addDelta ---
bad=0
for _ in range(200000):
    x=random.choice([0,1,M128,M128-1,random.getrandbits(128)]); y=random.choice(I128+[random.randint(-(1<<127),(1<<127)-1)])
    z=u((dirty(x,128)&M128)+signextend(15,dirty(u(y),128)))
    rev=bool(shr(128,z))
    exp=x+y
    if rev!=(exp<0 or exp>M128) or (not rev and z!=exp): bad+=1
print('addDelta failures',bad)
# --- TickBitmap ---
def compress(t,sp):
    t=signextend(2,t); sp=signextend(2,sp)
    return s(u(sdiv(t,sp)-slt(smod(t,sp),0)))
def position(t): return s(sar(8,signextend(2,u(t)))), u(t)&0xff
def msb(x): return x.bit_length()-1
def lsb(x): return (x&-x).bit_length()-1
def int24(x):
    x&=M24; return x-(1<<24) if x>>23 else x
class BM:
    def __init__(self): self.w={}
    def flip(self,t,sp):
        assert smod(u(t),u(sp))==0
        c=s(sdiv(u(t),u(sp)))
        key=s(sar(8,u(c)))            # mapping key as stored by the assembly (sign extended word)
        self.w[key]=self.w.get(key,0)^shl(u(c)&0xff,1)
    def nxt(self,t,sp,lte):
        c=compress(u(t),u(sp))
        if lte:
            wp,bp=position(c); mask=U>>(255-bp); m=self.w.get(wp,0)&mask
            init=m!=0
            n=int24(int24(c-int24((bp-msb(m))&0xff))*sp) if init else int24(int24(c-bp)*sp)
        else:
            c=int24(c+1); wp,bp=position(c); mask=U^((1<<bp)-1); m=self.w.get(wp,0)&mask
            init=m!=0
            n=int24(int24(c+int24((lsb(m)-bp)&0xff))*sp) if init else int24(int24(c+(255-bp))*sp)
        return n,init
bad=0
MINT,MAXT=-887272,887272
for sp in [1,2,7,10,60,200,255,256,257,4095,32767]:
    b=BM(); lo=-(-MINT//sp)*-1  # placeholder
    lo=(abs(MINT)//sp)*-sp; hi=(MAXT//sp)*sp
    ticks=set(random.randrange(lo,hi+1,sp) for _ in range(400))|{lo,hi,0}
    for t in ticks: b.flip(t,sp)
    st=sorted(ticks)
    import bisect
    for _ in range(4000):
        t=random.choice([random.randint(MINT,MAXT-1),random.choice(st),random.choice(st)-1,random.choice(st)+1])
        t=max(MINT,min(MAXT-1,t))
        n,init=b.nxt(t,sp,True)
        i=bisect.bisect_right(st,t)-1
        true_next=st[i] if i>=0 else None
        c=compress(u(t),u(sp)); wordlo=(c - (c & 0xff))*sp
        if init:
            if n!=true_next: bad+=1
        else:
            if n!=wordlo or (true_next is not None and true_next>=wordlo): bad+=1
        n,init=b.nxt(t,sp,False)
        i=bisect.bisect_right(st,t)
        true_next=st[i] if i<len(st) else None
        c1=compress(u(t),u(sp))+1; wordhi=(c1 + (255-(c1&0xff)))*sp
        if init:
            if n!=true_next: bad+=1
        else:
            if n!=wordhi or (true_next is not None and true_next<=wordhi): bad+=1
    # flip twice clears
    for t in ticks: b.flip(t,sp)
    if any(v for v in b.w.values()): bad+=1
print('TickBitmap failures',bad)
# int24 range of the unchecked products
mx=0
for sp in [1,32767]:
    for t in [MINT,MAXT]:
        c=compress(u(t),u(sp)); 
        for cc,lte in ((c,True),(c+1,False)):
            bp=cc&0xff
            v=(cc-bp)*sp if lte else (cc+255-bp)*sp
            mx=max(mx,abs(v))
print('largest |next| before clamp',mx,'int24 max',(1<<23)-1, mx<(1<<23))
# --- tickSpacingToMaxLiquidityPerTick for every spacing ---
bad=0
for sp in range(1,32768):
    spw=signextend(2,dirty(sp,24))
    minT=u(sdiv(u(MINT),spw)-slt(smod(u(MINT),spw),0)); maxT=sdiv(u(MAXT),spw)
    num=u(maxT-minT+1)
    res=(shl(128,1)-1)//num
    # reference
    import math
    mn=math.floor(MINT/sp); mxx=MAXT//sp
    if res!=M128//(mxx-mn+1) or res>M128: bad+=1
print('maxLiquidityPerTick failures',bad)
for sp,exp in [(1,191757530477355301479181766273477),(10,1917559095893846719543856547154045),(60,11505354575363080317263139282924270),(200,38345995821606768476828330790147420)]:
    spw=sp; minT=u(sdiv(u(MINT),spw)-slt(smod(u(MINT),spw),0)); maxT=sdiv(u(MAXT),spw)
    print(' spacing',sp, M128//u(maxT-minT+1)==exp)
# --- hook flag validity for all 2^14 flag combinations ---
F={'BI':13,'AI':12,'BAL':11,'AAL':10,'BRL':9,'ARL':8,'BS':7,'AS':6,'BD':5,'AD':4,'BSRD':3,'ASRD':2,'AALRD':1,'ARLRD':0}
def has(a,b): return a&(1<<b)!=0
def valid(a,fee):
    if not has(a,F['BS']) and has(a,F['BSRD']): return False
    if not has(a,F['AS']) and has(a,F['ASRD']): return False
    if not has(a,F['AAL']) and has(a,F['AALRD']): return False
    if not has(a,F['ARL']) and has(a,F['ARLRD']): return False
    dyn=fee==0x800000
    return (not dyn) if a==0 else ((a&((1<<14)-1))>0 or dyn)
cnt=sum(valid((0xABCDEF<<14)|x,3000) for x in range(1<<14))
print('valid flag sets for a static fee pool',cnt,'of',1<<14, '(expected 3^4*2^6-1 =',3**4*2**6-1,')')
print('zero flags, nonzero address, static fee valid:',valid(1<<14,3000),' dynamic:',valid(1<<14,0x800000),' address 0 dynamic:',valid(0,0x800000),' address 0 static:',valid(0,3000))
# --- position key layout ---
bad=0
for _ in range(20000):
    owner=random.getrandbits(160); tl=random.randint(-(1<<23),(1<<23)-1); tu=random.randint(-(1<<23),(1<<23)-1); salt=random.getrandbits(256)
    mem=bytearray(random.getrandbits(8) for _ in range(0x80))
    def mstore(off,v): mem[off:off+32]=u(v).to_bytes(32,'big')
    mstore(0x26,salt); mstore(0x06,dirty(u(tu),24)); mstore(0x03,dirty(u(tl),24)); mstore(0,dirty(owner,160))
    got=keccak256(bytes(mem[0x0c:0x0c+0x3a]))
    exp=keccak256(owner.to_bytes(20,'big')+(tl&M24).to_bytes(3,'big')+(tu&M24).to_bytes(3,'big')+salt.to_bytes(32,'big'))
    if got!=exp: bad+=1
print('position key failures',bad)
# --- delta slot: masked inputs, 64 byte preimage ---
bad=0
for _ in range(2000):
    t=random.getrandbits(160); c=random.getrandbits(160)
    a=keccak256((dirty(t,160)&M160).to_bytes(32,'big')+(dirty(c,160)&M160).to_bytes(32,'big'))
    if a!=keccak256(t.to_bytes(32,'big')+c.to_bytes(32,'big')): bad+=1
print('delta slot failures',bad)
# --- getSqrtPriceTarget ---
bad=0
for _ in range(100000):
    n=random.getrandbits(160); l=random.getrandbits(160); z=random.getrandbits(1)
    nn=dirty(n,160)&M160; ll=dirty(l,160)&M160
    f=(1 if nn<ll else 0)^(z&1); r=ll^u((nn^ll)*f)
    if r!=(max(n,l) if z else min(n,l)): bad+=1
print('getSqrtPriceTarget failures',bad)
# --- absDiff ---
bad=0
for _ in range(100000):
    a=random.getrandbits(160); b=random.getrandbits(160)
    d=u((dirty(a,160)&M160)-(dirty(b,160)&M160)); m=sar(255,d); r=m^u(m+d)
    if r!=abs(a-b): bad+=1
print('absDiff failures',bad)
# --- ERC-6909 id round trip ---
bad=0
for _ in range(10000):
    i=random.getrandbits(256); cur=i&M160
    if cur!=(i%(1<<160)): bad+=1
print('fromId keeps low 160 bits:',bad==0)
# --- SafeCast bounds ---
print('toInt128(uint) rejects >= 2^127:', all(((x>=1<<127)) for x in [1<<127,(1<<128)-1,U]) and not ((1<<127)-1>=1<<127))
