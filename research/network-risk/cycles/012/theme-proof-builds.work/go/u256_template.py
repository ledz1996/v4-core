# Python transcription of holiman/uint256 v1.3.2 (uint256.go, div.go, mod.go) on top of a
# transcription of Go math/bits (go1.25.9 bits.go, generic code paths, as compiled for GOARCH=wasm,
# where intrinsics.go:1222-1252 intrinsify Mul64/Add64/Sub64/Div64 for other architectures only).
# Straight-line bits.* statements of mod.go are machine-translated by gen_mod.py (comment names the
# mod.go line); control flow is translated by hand. PRIM selects the primitive set:
#   'generic'  : bits.go generic code with Go shift semantics (what wasm runs; Wasm.rules:105,120
#                lower an unbounded shift to Select(shift, 0, y<64), identical to Go semantics)
#   'exact'    : Python big-int exact primitives (what an intrinsic computes)
#   'mips64'   : Mul64 as DMULTU of MIPS64Instructions.sol:794-798, Div64 generic (as op-program)
#   'fault_*'  : planted faults to show the vectors can see a wrong lowering
M64=(1<<64)-1; M32=(1<<32)-1
PRIM='generic'
def gshr(x,s): return 0 if s>=64 else (x>>s)                 # Go x>>s, uint64
def gshl(x,s): return 0 if s>=64 else ((x<<s)&M64)            # Go x<<s, uint64
def wshr_unguarded(x,s): return x>>(s&63)                     # raw i64.shr_u (planted fault)
def wshl_unguarded(x,s): return (x<<(s&63))&M64
len8tab=[0]+[ (i).bit_length() for i in range(1,256)]
def Len64(x):
    n=0
    if x>=1<<32: x>>=32; n=32
    if x>=1<<16: x>>=16; n+=16
    if x>=1<<8: x>>=8; n+=8
    return n+len8tab[x]
def LeadingZeros64(x): return 64-Len64(x)
def Add64(x,y,c):
    if PRIM in('exact',): s=x+y+c; return s&M64, s>>64
    s=(x+y+c)&M64
    co=((x&y)|((x|y)&(~s&M64)))>>63
    return s,co
def Sub64(x,y,b):
    if PRIM in('exact',): d=x-y-b; return d&M64, 1 if d<0 else 0
    d=(x-y-b)&M64
    bo=(((~x&M64)&y)|((~(x^y)&M64)&d))>>63
    return d,bo
def Mul64(x,y):
    if PRIM in('exact','mips64'):
        r=x*y; return r>>64, r&M64        # DMULTU: uint128(rs)*uint128(rt); hi=res>>64, lo=uint64(res)
    if PRIM=='fault_mul':
        r=x*y
        if (x>>32)==M32 and (y>>32)==M32: return ((r>>64)-1)&M64, r&M64
        return r>>64,r&M64
    x0=x&M32; x1=x>>32; y0=y&M32; y1=y>>32
    w0=(x0*y0)&M64
    t=(x1*y0+(w0>>32))&M64
    w1=t&M32; w2=t>>32
    w1=(w1+x0*y1)&M64
    hi=(x1*y1+w2+(w1>>32))&M64
    lo=(x*y)&M64
    return hi,lo
def Div32(hi,lo,y):
    assert not (y!=0 and y<=hi)
    z=(hi<<32)|lo
    return (z//y)&M32,(z%y)&M32
def Div64(hi,lo,y):
    if y==0: raise ZeroDivisionError
    if y<=hi: raise OverflowError
    if PRIM=='exact':
        z=(hi<<64)|lo; return z//y, z%y
    if hi==0: return lo//y, lo%y
    shr = wshr_unguarded if PRIM=='fault_shift' else gshr
    s=LeadingZeros64(y)
    y=gshl(y,s)
    two32=1<<32; mask32=two32-1
    yn1=y>>32; yn0=y&mask32
    un32=(gshl(hi,s)|shr(lo,64-s))&M64
    un10=gshl(lo,s)
    un1=un10>>32; un0=un10&mask32
    q1=un32//yn1
    rhat=(un32-q1*yn1)&M64
    while q1>=two32 or ((q1*yn0)&M64)>((two32*rhat+un1)&M64):
        q1=(q1-1)&M64; rhat=(rhat+yn1)&M64
        if rhat>=two32: break
    un21=(un32*two32+un1-q1*y)&M64
    q0=un21//yn1
    rhat=(un21-q0*yn1)&M64
    while q0>=two32 or ((q0*yn0)&M64)>((two32*rhat+un0)&M64):
        q0=(q0-1)&M64; rhat=(rhat+yn1)&M64
        if rhat>=two32: break
    return (q1*two32+q0)&M64, (((un21*two32+un0-q0*y)&M64)>>s)

# ---- div.go ----
def reciprocal2by1(d):
    r,_=Div64((~d)&M64, M64, d); return r
def udivrem2by1(uh,ul,d,rec):
    qh,ql=Mul64(rec,uh)
    ql,c=Add64(ql,ul,0)
    qh,_=Add64(qh,uh,c)
    qh=(qh+1)&M64
    r=(ul-qh*d)&M64
    if r>ql:
        qh=(qh-1)&M64; r=(r+d)&M64
    if r>=d:
        qh=(qh+1)&M64; r=(r-d)&M64
    return qh,r

# ---- uint256.go (Int is a list of 4 limbs, little endian) ----
def toI(v): return [(v>>(64*i))&M64 for i in range(4)]
def frI(z): return z[0]|(z[1]<<64)|(z[2]<<128)|(z[3]<<192)
def isZero(z): return (z[0]|z[1]|z[2]|z[3])==0
def Add(x,y):
    z=[0]*4; c=0
    for i in range(4): z[i],c=Add64(x[i],y[i],c)
    return z
def AddOverflow(x,y):
    z=[0]*4; c=0
    for i in range(4): z[i],c=Add64(x[i],y[i],c)
    return z,c!=0
def Sub(x,y):
    z=[0]*4; b=0
    for i in range(4): z[i],b=Sub64(x[i],y[i],b)
    return z
def Neg(x): return Sub([0]*4,x)
def Sign(z):
    if isZero(z): return 0
    return 1 if z[3]<0x8000000000000000 else -1
def Cmp(x,y):
    for i in (3,2,1,0):
        if x[i]!=y[i]: return 1 if x[i]>y[i] else -1
    return 0
def Gt(z,x): return Cmp(z,x)>0
def Lt(z,x): return Cmp(z,x)<0
def Eq(z,x): return Cmp(z,x)==0
def IsUint64(z): return (z[1]|z[2]|z[3])==0
def umulStep(z,x,y,carry):
    hi,lo=Mul64(x,y)
    lo,carry=Add64(lo,carry,0)
    hi,_=Add64(hi,0,carry)
    lo,carry=Add64(lo,z,0)
    hi,_=Add64(hi,0,carry)
    return hi,lo
def umulHop(z,x,y):
    hi,lo=Mul64(x,y)
    lo,carry=Add64(lo,z,0)
    hi,_=Add64(hi,0,carry)
    return hi,lo
def umul(x,y):
    res=[0]*8
    carry,res[0]=Mul64(x[0],y[0])
    carry,res1=umulHop(carry,x[1],y[0])
    carry,res2=umulHop(carry,x[2],y[0])
    carry4,res3=umulHop(carry,x[3],y[0])
    carry,res[1]=umulHop(res1,x[0],y[1])
    carry,res2=umulStep(res2,x[1],y[1],carry)
    carry,res3=umulStep(res3,x[2],y[1],carry)
    carry5,res4=umulStep(carry4,x[3],y[1],carry)
    carry,res[2]=umulHop(res2,x[0],y[2])
    carry,res3=umulStep(res3,x[1],y[2],carry)
    carry,res4=umulStep(res4,x[2],y[2],carry)
    carry6,res5=umulStep(carry5,x[3],y[2],carry)
    carry,res[3]=umulHop(res3,x[0],y[3])
    carry,res[4]=umulStep(res4,x[1],y[3],carry)
    carry,res[5]=umulStep(res5,x[2],y[3],carry)
    res[7],res[6]=umulStep(carry6,x[3],y[3],carry)
    return res
def Mul(x,y):
    z=[0]*4
    x0,x1,x2,x3=x; y0,y1,y2,y3=y
    carry0,z[0]=Mul64(x0,y0)
    carry0,res1=umulHop(carry0,x1,y0)
    carry0,res2=umulHop(carry0,x2,y0)
    carry1,z[1]=umulHop(res1,x0,y1)
    carry1,res2=umulStep(res2,x1,y1,carry1)
    carry2,z[2]=umulHop(res2,x0,y2)
    z[3]=(x3*y0+x2*y1+x0*y3+x1*y2+carry0+carry1+carry2)&M64
    return z
def addTo(x,off,y):
    carry=0
    for i in range(len(y)): x[off+i],carry=Add64(x[off+i],y[i],carry)
    return carry
def subMulTo(x,off,y,mult):
    borrow=0
    for i in range(len(y)):
        s,c1=Sub64(x[off+i],borrow,0)
        ph,pl=Mul64(y[i],mult)
        t,c2=Sub64(s,pl,0)
        x[off+i]=t
        borrow=(ph+c1+c2)&M64
    return borrow
def udivremBy1(quot,u,d):
    rec=reciprocal2by1(d)
    rem=u[len(u)-1]
    for j in range(len(u)-2,-1,-1):
        quot[j],rem=udivrem2by1(rem,u[j],d,rec)
    return rem
def udivremKnuth(quot,u,d):
    dh=d[-1]; dl=d[-2]
    rec=reciprocal2by1(dh)
    for j in range(len(u)-len(d)-1,-1,-1):
        u2=u[j+len(d)]; u1=u[j+len(d)-1]; u0=u[j+len(d)-2]
        if u2>=dh:
            qhat=M64
        else:
            qhat,rhat=udivrem2by1(u2,u1,dh,rec)
            ph,pl=Mul64(qhat,dl)
            if ph>rhat or (ph==rhat and pl>u0): qhat=(qhat-1)&M64
        borrow=subMulTo(u,j,d,qhat)
        u[j+len(d)]=(u2-borrow)&M64
        if u2<borrow:
            qhat=(qhat-1)&M64
            u[j+len(d)]=(u[j+len(d)]+addTo(u,j,d))&M64
        quot[j]=qhat
def udivrem(quot,u,d,want_rem):
    shr = wshr_unguarded if PRIM=='fault_shift' else gshr
    dLen=0
    for i in range(3,-1,-1):
        if d[i]!=0: dLen=i+1; break
    shift=LeadingZeros64(d[dLen-1])
    dn=[0]*dLen
    for i in range(dLen-1,0,-1): dn[i]=gshl(d[i],shift)|shr(d[i-1],64-shift)
    dn[0]=gshl(d[0],shift)
    uLen=0
    for i in range(len(u)-1,-1,-1):
        if u[i]!=0: uLen=i+1; break
    rem=[0]*4
    if uLen<dLen:
        for i in range(4): rem[i]=u[i]
        return rem
    un=[0]*(uLen+1)
    un[uLen]=shr(u[uLen-1],64-shift)
    for i in range(uLen-1,0,-1): un[i]=gshl(u[i],shift)|shr(u[i-1],64-shift)
    un[0]=gshl(u[0],shift)
    if dLen==1:
        r=udivremBy1(quot,un,dn[0])
        return [gshr(r,shift),0,0,0]
    udivremKnuth(quot,un,dn)
    for i in range(dLen-1): rem[i]=gshr(un[i],shift)|gshl(un[i+1],64-shift)
    rem[dLen-1]=gshr(un[dLen-1],shift)
    return rem
def Div(x,y):
    if isZero(y) or Gt(y,x): return [0]*4
    if Eq(x,y): return [1,0,0,0]
    if IsUint64(x): return [x[0]//y[0],0,0,0]
    quot=[0]*4; udivrem(quot,list(x),y,False); return quot
def Mod(x,y):
    if isZero(y) or Eq(x,y): return [0]*4
    if Lt(x,y): return list(x)
    if IsUint64(x): return [x[0]%y[0],0,0,0]
    quot=[0]*4; return udivrem(quot,list(x),y,True)
def SMod(x,y):
    ys=Sign(y); xs=Sign(x)
    if xs==-1: x=Neg(x)
    if ys==-1: y=Neg(y)
    z=Mod(x,y)
    if xs==-1: z=Neg(z)
    return z
def SDiv(n,d):
    if Sign(n)>0:
        if Sign(d)>0: return Div(n,d)
        return Neg(Div(n,Neg(d)))
    if Sign(d)<0: return Div(Neg(n),Neg(d))
    return Neg(Div(Neg(n),d))
def AddMod(x,y,m):
    if m[3]!=0 and x[3]<=m[3] and y[3]<=m[3]:
        tmpX=[0]*4; tmpY=[0]*4; res=[0]*4; tmp=[0]*4; g1=0; g2=0
        for i in range(4): tmpX[i],g1=Sub64(x[i],m[i],g1)
        for i in range(4): tmpY[i],g2=Sub64(y[i],m[i],g2)
        if g1==0: x=tmpX
        if g2==0: y=tmpY
        c1=0; c2=0
        for i in range(4): res[i],c1=Add64(x[i],y[i],c1)
        for i in range(4): tmp[i],c2=Sub64(res[i],m[i],c2)
        if c1==0 and c2!=0: return res
        return tmp
    if isZero(m): return [0]*4
    z,ov=AddOverflow(x,y)
    if ov:
        s=[z[0],z[1],z[2],z[3],1]; quot=[0]*5
        return udivrem(quot,s,m,True)
    return Mod(z,m)
def MulMod(x,y,m):
    if isZero(x) or isZero(y) or isZero(m): return [0]*4
    p=umul(x,y)
    if m[3]!=0:
        mu=Reciprocal(m); return reduce4(p,m,mu)
    pl=p[0:4]; ph=p[4:8]
    if isZero(ph): return Mod(pl,m)
    quot=[0]*8
    return udivrem(quot,p,m,True)
def Lsh(x,n):
    # uint256.go:1042-1072
    if n==0: return list(x)
    if n>=192:
        z=[0,0,0,x[0]]; n-=192; z[3]=gshl(z[3],n); return z
    if n>=128:
        z=[0,0,x[0],x[1]]; n-=128
        z[3]=gshl(z[3],n)|SHR(z[2],64-n); z[2]=gshl(z[2],n); return z
    if n>=64:
        z=[0,x[0],x[1],x[2]]; n-=64
        z[3]=gshl(z[3],n)|SHR(z[2],64-n); z[2]=gshl(z[2],n)|SHR(z[1],64-n); z[1]=gshl(z[1],n); return z
    z=list(x)
    z[3]=gshl(z[3],n)|SHR(z[2],64-n); z[2]=gshl(z[2],n)|SHR(z[1],64-n)
    z[1]=gshl(z[1],n)|SHR(z[0],64-n); z[0]=gshl(z[0],n); return z
def Rsh(x,n):
    # uint256.go:1075-1104
    if n==0: return list(x)
    if n>=192:
        z=[x[3],0,0,0]; n-=192; z[0]=gshr(z[0],n); return z
    if n>=128:
        z=[x[2],x[3],0,0]; n-=128
        z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n); return z
    if n>=64:
        z=[x[1],x[2],x[3],0]; n-=64
        z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n)|SHL(z[2],64-n); z[2]=gshr(z[2],n); return z
    z=list(x)
    z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n)|SHL(z[2],64-n)
    z[2]=gshr(z[2],n)|SHL(z[3],64-n); z[3]=gshr(z[3],n); return z
def SRsh(x,n):
    # uint256.go:1110-1149
    if not (x[3]>>63)&1: return Rsh(x,n)
    a=SHL(M64,64-n%64)
    if n==0: return list(x)
    if n>=256: return [M64]*4
    if n>=192:
        z=[x[3],M64,M64,M64]; n-=192; z[0]=gshr(z[0],n)|a; return z
    if n>=128:
        z=[x[2],x[3],M64,M64]; n-=128
        z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n)|a; return z
    if n>=64:
        z=[x[1],x[2],x[3],M64]; n-=64
        z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n)|SHL(z[2],64-n); z[2]=gshr(z[2],n)|a; return z
    z=list(x)
    z[0]=gshr(z[0],n)|SHL(z[1],64-n); z[1]=gshr(z[1],n)|SHL(z[2],64-n)
    z[2]=gshr(z[2],n)|SHL(z[3],64-n); z[3]=gshr(z[3],n)|a; return z
def SHR(x,s): return wshr_unguarded(x,s) if PRIM=='fault_shift' else gshr(x,s)
def SHL(x,s): return wshl_unguarded(x,s) if PRIM=='fault_shift' else gshl(x,s)
def Byte(n,z):
    # uint256.go:1187-1198
    if (n[1]|n[2]|n[3])!=0 or n[0]>=32: return [0]*4
    index=n[0]; number=z[4-1-index//8]; offset=(index&7)<<3
    return [gshr(number,56-offset)&0xff,0,0,0]
def ExtendSign(x,b):
    # uint256.go:1260-1299
    if (b[1]|b[2]|b[3])!=0 or b[0]>30: return list(x)
    e=b[0]; z=list(x); wi=e>>3; bi=e&7; sw=z[wi]; off=bi<<3; sb=gshr(sw,off)
    sb8=sb&0xff; sextByte=(sb8-256 if sb8>=128 else sb8)&M64
    sext=gshl(sextByte,off); mask=gshl(M64,off); value=sw&(~mask&M64)
    z[wi]=sext|value
    s=sextByte-(1<<64) if sextByte>>63 else sextByte
    signEx=(s>>8)&M64
    if wi==2: z[3]=signEx
    elif wi==1: z[3]=z[2]=signEx
    elif wi==0: z[3]=z[2]=z[1]=signEx
    return z

# ---- mod.go ----
def Reciprocal(m):
    mu=[0]*5
    if m[3]==0: return mu
    s=LeadingZeros64(m[3])
    p=255-s
    if (m[0]|m[1]|m[2]|(m[3]&((m[3]-1)&M64)))==0:
        mu[4]=gshr(M64,p&63); mu[3]=M64; mu[2]=M64; mu[1]=M64; mu[0]=M64
        return mu
    y=Lsh(m,s)
    yh=(y[3]>>32)&M32
    if yh==0x80000000: r0=0xffffffff
    else: r0,_=Div32(0x80000000,0,yh)
    t1=r0
    t1=(t1*t1)&M64
    t1,_=Mul64(t1,y[3])
    r1=gshl(r0,32)
    r1=(r1-t1)&M64
    r1=(r1*2)&M64
    if (r1|gshl(y[3],1))==0: r1=M64
@@SEG 78 101 4@@
    if (r2h|r2l|gshl(y[3],1))==0:
        r2h=M64; r2l=M64
@@SEG 108 123 4@@
    x0=a3l; x1=a3h; x2=c3l; x3=c3h
    q0=q1=q2=q3=q4=t0=0
@@SEG 132 231 4@@
    x0=r4l; x1=r4k; x2=r4j; x3=r4i; x4=r4h
@@SEG 239 286 4@@
    if b!=0:
        r4h,r4i,r4j,r4k,r4l=x4,x3,x2,x1,x0
    p=(p&63)-1
@@SEG 296 300 4@@
    if p<0:
        r4h,r4i,r4j,r4k,r4l=x4,x3,x2,x1,x0
        p=0
    r=p; l=64-r
    x0=gshr(r4l,r)|gshl(r4k,l)
    x1=gshr(r4k,r)|gshl(r4j,l)
    x2=gshr(r4j,r)|gshl(r4i,l)
    x3=gshr(r4i,r)|gshl(r4h,l)
    x4=gshr(r4h,r)
    if p>0:
        r4h,r4i,r4j,r4k,r4l=x4,x3,x2,x1,x0
    return [r4l,r4k,r4j,r4i,r4h]
def reduce4(x,m,mu):
    x0=x[3]; x1=x[4]; x2=x[5]; x3=x[6]; x4=x[7]
    q0=q1=q2=q3=q4=q5=t0=t1=c=0
@@SEG 351 383 4@@
    q0=q1; q1=q2; q2=q3; q3=q4; q4=q5
    x0=x[0]; x1=x[1]; x2=x[2]; x3=x[3]; x4=x[4]
    r0=r1=r2=r3=r4=0
@@SEG 403 428 4@@
    b=0
@@SEG 432 438 4@@
    if b!=0:
@@SEG 441 445 8@@
    while True:
@@SEG 452 456 8@@
        if b!=0: break
        r4,r3,r2,r1,r0=q4,q3,q2,q1,q0
    return [r0,r1,r2,r3]
