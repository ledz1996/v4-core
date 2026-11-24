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
    a2h, a2l = Mul64(r1, r1)  # mod.go:79
    b2h, _ = Mul64(a2l, y[2])  # mod.go:82
    c2h, c2l = Mul64(a2l, y[3])  # mod.go:83
    d2h, d2l = Mul64(a2h, y[2])  # mod.go:84
    e2h, e2l = Mul64(a2h, y[3])  # mod.go:85
    b2h, c = Add64(b2h, c2l, 0)  # mod.go:87
    e2l, c = Add64(e2l, c2h, c)  # mod.go:88
    e2h, _ = Add64(e2h,   0, c)  # mod.go:89
    _,   c = Add64(b2h, d2l, 0)  # mod.go:91
    e2l, c = Add64(e2l, d2h, c)  # mod.go:92
    e2h, _ = Add64(e2h,   0, c)  # mod.go:93
    t2l, b = Sub64( 0, e2l, 0)  # mod.go:96
    t2h, _ = Sub64(r1, e2h, b)  # mod.go:97
    r2l, c = Add64(t2l, t2l, 0)  # mod.go:100
    r2h, _ = Add64(t2h, t2h, c)  # mod.go:101
    if (r2h|r2l|gshl(y[3],1))==0:
        r2h=M64; r2l=M64
    a3h, a3l = Mul64(r2l, r2l)  # mod.go:111
    b3h, b3l = Mul64(r2l, r2h)  # mod.go:112
    c3h, c3l = Mul64(r2h, r2h)  # mod.go:113
    a3h, c = Add64(a3h, b3l, 0)  # mod.go:115
    c3l, c = Add64(c3l, b3h, c)  # mod.go:116
    c3h, _ = Add64(c3h,   0, c)  # mod.go:117
    a3h, c = Add64(a3h, b3l, 0)  # mod.go:119
    c3l, c = Add64(c3l, b3h, c)  # mod.go:120
    c3h, _ = Add64(c3h,   0, c)  # mod.go:121
    x0=a3l; x1=a3h; x2=c3l; x3=c3h
    q0=q1=q2=q3=q4=t0=0
    q0, _ = Mul64(x2, y[0])  # mod.go:132
    q1, t0 = Mul64(x3, y[0])  # mod.go:133
    q0, c = Add64(q0, t0, 0)  # mod.go:133
    q1, _ = Add64(q1,  0, c)  # mod.go:133
    t1, _ = Mul64(x1, y[1])  # mod.go:136
    q0, c = Add64(q0, t1, 0)  # mod.go:136
    q2, t0 = Mul64(x3, y[1])  # mod.go:137
    q1, c = Add64(q1, t0, c)  # mod.go:137
    q2, _ = Add64(q2,  0, c)  # mod.go:137
    t1, t0 = Mul64(x2, y[1])  # mod.go:139
    q0, c = Add64(q0, t0, 0)  # mod.go:139
    q1, c = Add64(q1, t1, c)  # mod.go:139
    q2, _ = Add64(q2, 0, c)  # mod.go:139
    t1, t0 = Mul64(x1, y[2])  # mod.go:142
    q0, c = Add64(q0, t0, 0)  # mod.go:142
    q1, c = Add64(q1, t1, c)  # mod.go:142
    q3, t0 = Mul64(x3, y[2])  # mod.go:143
    q2, c = Add64(q2, t0, c)  # mod.go:143
    q3, _ = Add64(q3,  0, c)  # mod.go:143
    t1, _ = Mul64(x0, y[2])  # mod.go:145
    q0, c = Add64(q0, t1, 0)  # mod.go:145
    t1, t0 = Mul64(x2, y[2])  # mod.go:146
    q1, c = Add64(q1, t0, c)  # mod.go:146
    q2, c = Add64(q2, t1, c)  # mod.go:146
    q3, _ = Add64(q3, 0, c)  # mod.go:146
    t1, t0 = Mul64(x1, y[3])  # mod.go:149
    q1, c = Add64(q1, t0, 0)  # mod.go:149
    q2, c = Add64(q2, t1, c)  # mod.go:149
    q4, t0 = Mul64(x3, y[3])  # mod.go:150
    q3, c = Add64(q3, t0, c)  # mod.go:150
    q4, _ = Add64(q4,  0, c)  # mod.go:150
    t1, t0 = Mul64(x0, y[3])  # mod.go:152
    q0, c = Add64(q0, t0, 0)  # mod.go:152
    q1, c = Add64(q1, t1, c)  # mod.go:152
    t1, t0 = Mul64(x2, y[3])  # mod.go:153
    q2, c = Add64(q2, t0, c)  # mod.go:153
    q3, c = Add64(q3, t1, c)  # mod.go:153
    q4, _ = Add64(q4, 0, c)  # mod.go:153
    _,   b = Sub64(  0, q0, 0)  # mod.go:156
    _,   b = Sub64(  0, q1, b)  # mod.go:157
    t3l, b = Sub64(  0, q2, b)  # mod.go:158
    t3m, b = Sub64(r2l, q3, b)  # mod.go:159
    t3h, _ = Sub64(r2h, q4, b)  # mod.go:160
    r3l, c = Add64(t3l, t3l, 0)  # mod.go:163
    r3m, c = Add64(t3m, t3m, c)  # mod.go:164
    r3h, _ = Add64(t3h, t3h, c)  # mod.go:165
    a4h, a4l = Mul64(r3l, r3l)  # mod.go:171
    b4h, b4l = Mul64(r3l, r3m)  # mod.go:172
    c4h, c4l = Mul64(r3l, r3h)  # mod.go:173
    d4h, d4l = Mul64(r3m, r3m)  # mod.go:174
    e4h, e4l = Mul64(r3m, r3h)  # mod.go:175
    f4h, f4l = Mul64(r3h, r3h)  # mod.go:176
    b4h, c = Add64(b4h, c4l, 0)  # mod.go:178
    e4l, c = Add64(e4l, c4h, c)  # mod.go:179
    e4h, _ = Add64(e4h,   0, c)  # mod.go:180
    a4h, c = Add64(a4h, b4l, 0)  # mod.go:182
    d4l, c = Add64(d4l, b4h, c)  # mod.go:183
    d4h, c = Add64(d4h, e4l, c)  # mod.go:184
    f4l, c = Add64(f4l, e4h, c)  # mod.go:185
    f4h, _ = Add64(f4h,   0, c)  # mod.go:186
    a4h, c = Add64(a4h, b4l, 0)  # mod.go:188
    d4l, c = Add64(d4l, b4h, c)  # mod.go:189
    d4h, c = Add64(d4h, e4l, c)  # mod.go:190
    f4l, c = Add64(f4l, e4h, c)  # mod.go:191
    f4h, _ = Add64(f4h,   0, c)  # mod.go:192
    x1, x0 = Mul64(d4h, y[0])  # mod.go:196
    x3, x2 = Mul64(f4h, y[0])  # mod.go:197
    t1, t0 = Mul64(f4l, y[0])  # mod.go:198
    x1, c = Add64(x1, t0, 0)  # mod.go:198
    x2, c = Add64(x2, t1, c)  # mod.go:198
    x3, _ = Add64(x3,  0, c)  # mod.go:199
    t1, t0 = Mul64(d4h, y[1])  # mod.go:201
    x1, c = Add64(x1, t0, 0)  # mod.go:201
    x2, c = Add64(x2, t1, c)  # mod.go:201
    x4, t0 = Mul64(f4h, y[1])  # mod.go:202
    x3, c = Add64(x3, t0, c)  # mod.go:202
    x4, _ = Add64(x4,  0, c)  # mod.go:202
    t1, t0 = Mul64(d4l, y[1])  # mod.go:203
    x0, c = Add64(x0, t0, 0)  # mod.go:203
    x1, c = Add64(x1, t1, c)  # mod.go:203
    t1, t0 = Mul64(f4l, y[1])  # mod.go:204
    x2, c = Add64(x2, t0, c)  # mod.go:204
    x3, c = Add64(x3, t1, c)  # mod.go:204
    x4, _ = Add64(x4,  0, c)  # mod.go:205
    t1, t0 = Mul64(a4h, y[2])  # mod.go:207
    x0, c = Add64(x0, t0, 0)  # mod.go:207
    x1, c = Add64(x1, t1, c)  # mod.go:207
    t1, t0 = Mul64(d4h, y[2])  # mod.go:208
    x2, c = Add64(x2, t0, c)  # mod.go:208
    x3, c = Add64(x3, t1, c)  # mod.go:208
    x5, t0 = Mul64(f4h, y[2])  # mod.go:209
    x4, c = Add64(x4, t0, c)  # mod.go:209
    x5, _ = Add64(x5,  0, c)  # mod.go:209
    t1, t0 = Mul64(d4l, y[2])  # mod.go:210
    x1, c = Add64(x1, t0, 0)  # mod.go:210
    x2, c = Add64(x2, t1, c)  # mod.go:210
    t1, t0 = Mul64(f4l, y[2])  # mod.go:211
    x3, c = Add64(x3, t0, c)  # mod.go:211
    x4, c = Add64(x4, t1, c)  # mod.go:211
    x5, _ = Add64(x5,  0, c)  # mod.go:212
    t1, t0 = Mul64(a4h, y[3])  # mod.go:214
    x1, c = Add64(x1, t0, 0)  # mod.go:214
    x2, c = Add64(x2, t1, c)  # mod.go:214
    t1, t0 = Mul64(d4h, y[3])  # mod.go:215
    x3, c = Add64(x3, t0, c)  # mod.go:215
    x4, c = Add64(x4, t1, c)  # mod.go:215
    x6, t0 = Mul64(f4h, y[3])  # mod.go:216
    x5, c = Add64(x5, t0, c)  # mod.go:216
    x6, _ = Add64(x6,  0, c)  # mod.go:216
    t1, t0 = Mul64(a4l, y[3])  # mod.go:217
    x0, c = Add64(x0, t0, 0)  # mod.go:217
    x1, c = Add64(x1, t1, c)  # mod.go:217
    t1, t0 = Mul64(d4l, y[3])  # mod.go:218
    x2, c = Add64(x2, t0, c)  # mod.go:218
    x3, c = Add64(x3, t1, c)  # mod.go:218
    t1, t0 = Mul64(f4l, y[3])  # mod.go:219
    x4, c = Add64(x4, t0, c)  # mod.go:219
    x5, c = Add64(x5, t1, c)  # mod.go:219
    x6, _ = Add64(x6,  0, c)  # mod.go:220
    _,   b = Sub64(  0, x0, 0)  # mod.go:223
    _,   b = Sub64(  0, x1, b)  # mod.go:224
    r4l, b = Sub64(  0, x2, b)  # mod.go:225
    r4k, b = Sub64(  0, x3, b)  # mod.go:226
    r4j, b = Sub64(r3l, x4, b)  # mod.go:227
    r4i, b = Sub64(r3m, x5, b)  # mod.go:228
    r4h, _ = Sub64(r3h, x6, b)  # mod.go:229
    x0=r4l; x1=r4k; x2=r4j; x3=r4i; x4=r4h
    q1, q0 = Mul64(x0, y[0])  # mod.go:239
    q3, q2 = Mul64(x2, y[0])  # mod.go:240
    q5, q4 = Mul64(x4, y[0])  # mod.go:241
    t1, t0 = Mul64(x1, y[0])  # mod.go:243
    q1, c = Add64(q1, t0, 0)  # mod.go:243
    q2, c = Add64(q2, t1, c)  # mod.go:243
    t1, t0 = Mul64(x3, y[0])  # mod.go:244
    q3, c = Add64(q3, t0, c)  # mod.go:244
    q4, c = Add64(q4, t1, c)  # mod.go:244
    q5, _ = Add64(q5, 0, c)  # mod.go:244
    t1, t0 = Mul64(x0, y[1])  # mod.go:246
    q1, c = Add64(q1, t0, 0)  # mod.go:246
    q2, c = Add64(q2, t1, c)  # mod.go:246
    t1, t0 = Mul64(x2, y[1])  # mod.go:247
    q3, c = Add64(q3, t0, c)  # mod.go:247
    q4, c = Add64(q4, t1, c)  # mod.go:247
    q6, t0 = Mul64(x4, y[1])  # mod.go:248
    q5, c = Add64(q5, t0, c)  # mod.go:248
    q6, _ = Add64(q6,  0, c)  # mod.go:248
    t1, t0 = Mul64(x1, y[1])  # mod.go:250
    q2, c = Add64(q2, t0, 0)  # mod.go:250
    q3, c = Add64(q3, t1, c)  # mod.go:250
    t1, t0 = Mul64(x3, y[1])  # mod.go:251
    q4, c = Add64(q4, t0, c)  # mod.go:251
    q5, c = Add64(q5, t1, c)  # mod.go:251
    q6, _ = Add64(q6, 0, c)  # mod.go:251
    t1, t0 = Mul64(x0, y[2])  # mod.go:253
    q2, c = Add64(q2, t0, 0)  # mod.go:253
    q3, c = Add64(q3, t1, c)  # mod.go:253
    t1, t0 = Mul64(x2, y[2])  # mod.go:254
    q4, c = Add64(q4, t0, c)  # mod.go:254
    q5, c = Add64(q5, t1, c)  # mod.go:254
    q7, t0 = Mul64(x4, y[2])  # mod.go:255
    q6, c = Add64(q6, t0, c)  # mod.go:255
    q7, _ = Add64(q7,  0, c)  # mod.go:255
    t1, t0 = Mul64(x1, y[2])  # mod.go:257
    q3, c = Add64(q3, t0, 0)  # mod.go:257
    q4, c = Add64(q4, t1, c)  # mod.go:257
    t1, t0 = Mul64(x3, y[2])  # mod.go:258
    q5, c = Add64(q5, t0, c)  # mod.go:258
    q6, c = Add64(q6, t1, c)  # mod.go:258
    q7, _ = Add64(q7, 0, c)  # mod.go:258
    t1, t0 = Mul64(x0, y[3])  # mod.go:260
    q3, c = Add64(q3, t0, 0)  # mod.go:260
    q4, c = Add64(q4, t1, c)  # mod.go:260
    t1, t0 = Mul64(x2, y[3])  # mod.go:261
    q5, c = Add64(q5, t0, c)  # mod.go:261
    q6, c = Add64(q6, t1, c)  # mod.go:261
    q8, t0 = Mul64(x4, y[3])  # mod.go:262
    q7, c = Add64(q7, t0, c)  # mod.go:262
    q8, _ = Add64(q8,  0, c)  # mod.go:262
    t1, t0 = Mul64(x1, y[3])  # mod.go:264
    q4, c = Add64(q4, t0, 0)  # mod.go:264
    q5, c = Add64(q5, t1, c)  # mod.go:264
    t1, t0 = Mul64(x3, y[3])  # mod.go:265
    q6, c = Add64(q6, t0, c)  # mod.go:265
    q7, c = Add64(q7, t1, c)  # mod.go:265
    q8, _ = Add64(q8, 0, c)  # mod.go:265
    _, b = Sub64(0, q0, 0)  # mod.go:270
    _, b = Sub64(0, q1, b)  # mod.go:271
    _, b = Sub64(0, q2, b)  # mod.go:272
    _, b = Sub64(0, q3, b)  # mod.go:273
    _, b = Sub64(0, q4, b)  # mod.go:274
    _, b = Sub64(0, q5, b)  # mod.go:275
    _, b = Sub64(0, q6, b)  # mod.go:276
    _, b = Sub64(0, q7, b)  # mod.go:277
    _, b = Sub64((1<<62), q8, b)  # mod.go:278
    x0, t = Sub64(r4l, 1, 0)  # mod.go:281
    x1, t = Sub64(r4k, 0, t)  # mod.go:282
    x2, t = Sub64(r4j, 0, t)  # mod.go:283
    x3, t = Sub64(r4i, 0, t)  # mod.go:284
    x4, _ = Sub64(r4h, 0, t)  # mod.go:285
    if b!=0:
        r4h,r4i,r4j,r4k,r4l=x4,x3,x2,x1,x0
    p=(p&63)-1
    x0, c = Add64(r4l, r4l, 0)  # mod.go:296
    x1, c = Add64(r4k, r4k, c)  # mod.go:297
    x2, c = Add64(r4j, r4j, c)  # mod.go:298
    x3, c = Add64(r4i, r4i, c)  # mod.go:299
    x4, _ = Add64(r4h, r4h, c)  # mod.go:300
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
    q0, _ = Mul64(x3, mu[0])  # mod.go:351
    q1, t0 = Mul64(x4, mu[0])  # mod.go:352
    q0, c = Add64(q0, t0, 0)  # mod.go:352
    q1, _ = Add64(q1,  0, c)  # mod.go:352
    t1, _ = Mul64(x2, mu[1])  # mod.go:355
    q0, c = Add64(q0, t1, 0)  # mod.go:355
    q2, t0 = Mul64(x4, mu[1])  # mod.go:356
    q1, c = Add64(q1, t0, c)  # mod.go:356
    q2, _ = Add64(q2,  0, c)  # mod.go:356
    t1, t0 = Mul64(x3, mu[1])  # mod.go:358
    q0, c = Add64(q0, t0, 0)  # mod.go:358
    q1, c = Add64(q1, t1, c)  # mod.go:358
    q2, _ = Add64(q2, 0, c)  # mod.go:358
    t1, t0 = Mul64(x2, mu[2])  # mod.go:361
    q0, c = Add64(q0, t0, 0)  # mod.go:361
    q1, c = Add64(q1, t1, c)  # mod.go:361
    q3, t0 = Mul64(x4, mu[2])  # mod.go:362
    q2, c = Add64(q2, t0, c)  # mod.go:362
    q3, _ = Add64(q3,  0, c)  # mod.go:362
    t1, _ = Mul64(x1, mu[2])  # mod.go:364
    q0, c = Add64(q0, t1, 0)  # mod.go:364
    t1, t0 = Mul64(x3, mu[2])  # mod.go:365
    q1, c = Add64(q1, t0, c)  # mod.go:365
    q2, c = Add64(q2, t1, c)  # mod.go:365
    q3, _ = Add64(q3, 0, c)  # mod.go:365
    t1, _ = Mul64(x0, mu[3])  # mod.go:368
    q0, c = Add64(q0, t1, 0)  # mod.go:368
    t1, t0 = Mul64(x2, mu[3])  # mod.go:369
    q1, c = Add64(q1, t0, c)  # mod.go:369
    q2, c = Add64(q2, t1, c)  # mod.go:369
    q4, t0 = Mul64(x4, mu[3])  # mod.go:370
    q3, c = Add64(q3, t0, c)  # mod.go:370
    q4, _ = Add64(q4,  0, c)  # mod.go:370
    t1, t0 = Mul64(x1, mu[3])  # mod.go:372
    q0, c = Add64(q0, t0, 0)  # mod.go:372
    q1, c = Add64(q1, t1, c)  # mod.go:372
    t1, t0 = Mul64(x3, mu[3])  # mod.go:373
    q2, c = Add64(q2, t0, c)  # mod.go:373
    q3, c = Add64(q3, t1, c)  # mod.go:373
    q4, _ = Add64(q4, 0, c)  # mod.go:373
    t1, t0 = Mul64(x0, mu[4])  # mod.go:376
    _,  c = Add64(q0, t0, 0)  # mod.go:376
    q1, c = Add64(q1, t1, c)  # mod.go:376
    t1, t0 = Mul64(x2, mu[4])  # mod.go:377
    q2, c = Add64(q2, t0, c)  # mod.go:377
    q3, c = Add64(q3, t1, c)  # mod.go:377
    q5, t0 = Mul64(x4, mu[4])  # mod.go:378
    q4, c = Add64(q4, t0, c)  # mod.go:378
    q5, _ = Add64(q5,  0, c)  # mod.go:378
    t1, t0 = Mul64(x1, mu[4])  # mod.go:380
    q1, c = Add64(q1, t0, 0)  # mod.go:380
    q2, c = Add64(q2, t1, c)  # mod.go:380
    t1, t0 = Mul64(x3, mu[4])  # mod.go:381
    q3, c = Add64(q3, t0, c)  # mod.go:381
    q4, c = Add64(q4, t1, c)  # mod.go:381
    q5, _ = Add64(q5, 0, c)  # mod.go:381
    q0=q1; q1=q2; q2=q3; q3=q4; q4=q5
    x0=x[0]; x1=x[1]; x2=x[2]; x3=x[3]; x4=x[4]
    r0=r1=r2=r3=r4=0
    r4, r3 = Mul64(q0, m[3])  # mod.go:403
    _,  t0 = Mul64(q1, m[3])  # mod.go:404
    r4, _ = Add64(r4, t0, 0)  # mod.go:404
    t1, r2 = Mul64(q0, m[2])  # mod.go:407
    r3, c = Add64(r3, t1, 0)  # mod.go:407
    _,  t0 = Mul64(q2, m[2])  # mod.go:408
    r4, _ = Add64(r4, t0, c)  # mod.go:408
    t1, t0 = Mul64(q1, m[2])  # mod.go:410
    r3, c = Add64(r3, t0, 0)  # mod.go:410
    r4, _ = Add64(r4, t1, c)  # mod.go:410
    t1, r1 = Mul64(q0, m[1])  # mod.go:413
    r2, c = Add64(r2, t1, 0)  # mod.go:413
    t1, t0 = Mul64(q2, m[1])  # mod.go:414
    r3, c = Add64(r3, t0, c)  # mod.go:414
    r4, _ = Add64(r4, t1, c)  # mod.go:414
    t1, t0 = Mul64(q1, m[1])  # mod.go:416
    r2, c = Add64(r2, t0, 0)  # mod.go:416
    r3, c = Add64(r3, t1, c)  # mod.go:416
    _,  t0 = Mul64(q3, m[1])  # mod.go:417
    r4, _ = Add64(r4, t0, c)  # mod.go:417
    t1, r0 = Mul64(q0, m[0])  # mod.go:420
    r1, c = Add64(r1, t1, 0)  # mod.go:420
    t1, t0 = Mul64(q2, m[0])  # mod.go:421
    r2, c = Add64(r2, t0, c)  # mod.go:421
    r3, c = Add64(r3, t1, c)  # mod.go:421
    _,  t0 = Mul64(q4, m[0])  # mod.go:422
    r4, _ = Add64(r4, t0, c)  # mod.go:422
    t1, t0 = Mul64(q1, m[0])  # mod.go:424
    r1, c = Add64(r1, t0, 0)  # mod.go:424
    r2, c = Add64(r2, t1, c)  # mod.go:424
    t1, t0 = Mul64(q3, m[0])  # mod.go:425
    r3, c = Add64(r3, t0, c)  # mod.go:425
    r4, _ = Add64(r4, t1, c)  # mod.go:425
    b=0
    r0, b = Sub64(x0, r0, 0)  # mod.go:432
    r1, b = Sub64(x1, r1, b)  # mod.go:433
    r2, b = Sub64(x2, r2, b)  # mod.go:434
    r3, b = Sub64(x3, r3, b)  # mod.go:435
    r4, b = Sub64(x4, r4, b)  # mod.go:436
    if b!=0:
        r0, c = Add64(r0, m[0], 0)  # mod.go:441
        r1, c = Add64(r1, m[1], c)  # mod.go:442
        r2, c = Add64(r2, m[2], c)  # mod.go:443
        r3, c = Add64(r3, m[3], c)  # mod.go:444
        r4, _ = Add64(r4,    0, c)  # mod.go:445
    while True:
        q0, b = Sub64(r0, m[0], 0)  # mod.go:452
        q1, b = Sub64(r1, m[1], b)  # mod.go:453
        q2, b = Sub64(r2, m[2], b)  # mod.go:454
        q3, b = Sub64(r3, m[3], b)  # mod.go:455
        q4, b = Sub64(r4,    0, b)  # mod.go:456
        if b!=0: break
        r4,r3,r2,r1,r0=q4,q3,q2,q1,q0
    return [r0,r1,r2,r3]
