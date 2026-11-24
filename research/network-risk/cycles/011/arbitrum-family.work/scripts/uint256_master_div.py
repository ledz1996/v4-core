"""Transcription of holiman/uint256 master Div and Mod (udiv, umod, rem5by4, rem4by3,
quoRem4by3, rem3by2 and the power-of-two fast path in Div), compared with Python integers.
Source: https://raw.githubusercontent.com/holiman/uint256/master/uint256.go and div.go (saved in src/uint256/)."""
import random, json, sys
M=(1<<64)-1
def limbs(x): return [(x>>(64*i))&M for i in range(4)]
def val(l): return sum(v<<(64*i) for i,v in enumerate(l))
def div64(hi,lo,d):
    assert hi<d
    n=(hi<<64)|lo; return n//d, n%d
def mul64(a,b): p=a*b; return p>>64, p&M
def add64(a,b,c): s=a+b+c; return s&M, s>>64
def sub64(a,b,bw): s=a-b-bw; return s&M, 1 if s<0 else 0
def lz(x): return 64-x.bit_length()
def tz(x): return (x & -x).bit_length()-1
def sh(a,s): return (a<<s)&M
def shr(a,s): return a>>s if s<64 else 0   # Go: x>>64 == 0 for uint64
def rem5by4(u4,u3,u2,u1,u0,v3,v2,v1,v0):
    q,_=div64(u4,u3,v3)
    h0,l0=mul64(q,v0);h1,l1=mul64(q,v1);h2,l2=mul64(q,v2);h3,l3=mul64(q,v3)
    p1,c=add64(l1,h0,0);p2,c=add64(l2,h1,c);p3,c=add64(l3,h2,c)
    u0,b=sub64(u0,l0,0);u1,b=sub64(u1,p1,b);u2,b=sub64(u2,p2,b);u3,b=sub64(u3,p3,b)
    u4=(u4-(h3+c+b))&M
    while u4!=0:
        q=(q-1)&M
        u0,c=add64(u0,v0,0);u1,c=add64(u1,v1,c);u2,c=add64(u2,v2,c);u3,c=add64(u3,v3,c);u4=(u4+c)&M
    return u3,u2,u1,u0,q
def quoRem4by3(u3,u2,u1,u0,v2,v1,v0):
    q=M
    if u3<v2: q,_=div64(u3,u2,v2)
    h0,l0=mul64(q,v0);h1,l1=mul64(q,v1);h2,l2=mul64(q,v2)
    p1,c=add64(l1,h0,0);p2,c=add64(l2,h1,c)
    u0,b=sub64(u0,l0,0);u1,b=sub64(u1,p1,b);u2,b=sub64(u2,p2,b)
    u3=(u3-(h2+c+b))&M
    while u3!=0:
        q=(q-1)&M
        u0,c=add64(u0,v0,0);u1,c=add64(u1,v1,c);u2,c=add64(u2,v2,c);u3=(u3+c)&M
    return u2,u1,u0,q
def rem4by3(*a): r=quoRem4by3(*a); return r[:3]
def rem3by2(u2,u1,u0,v1,v0):
    q=M
    if u2<v1: q,_=div64(u2,u1,v1)
    h0,l0=mul64(q,v0);h1,l1=mul64(q,v1)
    p1,c=add64(l1,h0,0)
    u0,b=sub64(u0,l0,0);u1,b=sub64(u1,p1,b)
    u2=(u2-(h1+c+b))&M
    while u2!=0:
        q=(q-1)&M
        u0,c=add64(u0,v0,0);u1,c=add64(u1,v1,c);u2=(u2+c)&M
    return u1,u0,q
def norm(x,s):  # x<<s over 4 limbs into 5 (go semantics: x>>(64-s) with s==0 gives x>>64 == 0)
    return [shr(x[3],64-s), sh(x[3],s)|shr(x[2],64-s), sh(x[2],s)|shr(x[1],64-s), sh(x[1],s)|shr(x[0],64-s), sh(x[0],s)]
def umod(x,y):
    if y[3]!=0:
        if y[3]>>63: return limbs((val(x)-val(y))%(1<<256))
        s=lz(y[3]); u=norm(x,s)
        v=[sh(y[3],s)|shr(y[2],64-s), sh(y[2],s)|shr(y[1],64-s), sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)]
        r3,r2,r1,r0,_=rem5by4(*u,*v)
        return [shr(r0,s)|sh(r1,64-s) if s else r0, shr(r1,s)|sh(r2,64-s) if s else r1, shr(r2,s)|sh(r3,64-s) if s else r2, shr(r3,s)]
    if y[2]!=0:
        s=lz(y[2]); v2,v1,v0=sh(y[2],s)|shr(y[1],64-s), sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)
        u=norm(x,s)
        r2,r1,r0=rem4by3(u[0],u[1],u[2],u[3],v2,v1,v0)
        r2,r1,r0=rem4by3(r2,r1,r0,u[4],v2,v1,v0)
        return [shr(r0,s)|(sh(r1,64-s) if s else 0), shr(r1,s)|(sh(r2,64-s) if s else 0), shr(r2,s), 0]
    if y[1]!=0:
        s=lz(y[1]); v1,v0=sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)
        u=norm(x,s)
        r1,r0,_=rem3by2(u[0],u[1],u[2],v1,v0)
        r1,r0,_=rem3by2(r1,r0,u[3],v1,v0)
        r1,r0,_=rem3by2(r1,r0,u[4],v1,v0)
        return [shr(r0,s)|(sh(r1,64-s) if s else 0), shr(r1,s),0,0]
    d=y[0]; r=x[3]%d
    _,r=div64(r,x[2],d);_,r=div64(r,x[1],d);_,r=div64(r,x[0],d)
    return [r,0,0,0]
def udiv(x,y):
    if y[3]!=0:
        if y[3]>>63: return [1,0,0,0]
        s=lz(y[3]); u=norm(x,s)
        v=[sh(y[3],s)|shr(y[2],64-s), sh(y[2],s)|shr(y[1],64-s), sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)]
        q=rem5by4(*u,*v)[4]; return [q,0,0,0]
    if y[2]!=0:
        s=lz(y[2]); v2,v1,v0=sh(y[2],s)|shr(y[1],64-s), sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)
        u=norm(x,s)
        r2,r1,r0,q1=quoRem4by3(u[0],u[1],u[2],u[3],v2,v1,v0)
        _,_,_,q0=quoRem4by3(r2,r1,r0,u[4],v2,v1,v0)
        return [q0,q1,0,0]
    if y[1]!=0:
        s=lz(y[1]); v1,v0=sh(y[1],s)|shr(y[0],64-s), sh(y[0],s)
        u=norm(x,s)
        r1,r0,q2=rem3by2(u[0],u[1],u[2],v1,v0)
        r1,r0,q1=rem3by2(r1,r0,u[3],v1,v0)
        _,_,q0=rem3by2(r1,r0,u[4],v1,v0)
        return [q0,q1,q2,0]
    d=y[0]; q3=x[3]//d
    q2,r=div64(x[3]%d,x[2],d);q1,r=div64(r,x[1],d);q0,_=div64(r,x[0],d)
    return [q0,q1,q2,q3]
def Div(x,y):
    X,Y=val(x),val(y)
    if Y==0 or Y>X: return 0
    if X==Y: return 1
    if x[3]==0 and x[2]==0 and x[1]==0 and y[3]==0 and y[2]==0 and y[1]==0: return x[0]//y[0]  # IsUint64 fast path
    if y[0]&((y[0]-1)&M)==0:
        if y[3]!=0:
            if (y[0]|y[1]|y[2]|(y[3]&((y[3]-1)&M)))==0: return X>>(192+tz(y[3]))
        elif y[2]!=0:
            if (y[0]|y[1]|(y[2]&((y[2]-1)&M)))==0: return X>>(128+tz(y[2]))
        elif y[1]!=0:
            if (y[0]|(y[1]&((y[1]-1)&M)))==0: return X>>(64+tz(y[1]))
        else: return X>>tz(y[0])
    return val(udiv(x,y))
def Mod(x,y):
    X,Y=val(x),val(y)
    if Y==0 or X==Y: return 0
    if X<Y: return X
    if x[3]==0 and x[2]==0 and x[1]==0 and y[3]==0 and y[2]==0 and y[1]==0: return x[0]%y[0]
    return val(umod(x,y))
def main(n,seed=11):
    R=random.Random(seed); bad=[]
    edges=[0,1,2,3,M,M-1,1<<63,(1<<63)-1,(1<<63)+1,1<<32,(1<<32)-1]
    def rnd():
        k=R.randrange(6)
        if k==0: return R.getrandbits(256)
        if k==1: return R.getrandbits(R.randrange(1,257))
        if k==2: return val([R.choice(edges) for _ in range(4)])
        if k==3: return (1<<R.randrange(256)) + R.choice([-1,0,0,1])
        if k==4: return ((1<<256)-1)//(R.getrandbits(R.randrange(1,200))|1)
        return val([R.choice(edges) for _ in range(R.randrange(1,4))]+[0]*0)
    cnt=0
    for i in range(n):
        X=rnd()%(1<<256); Y=rnd()%(1<<256)
        if Y==0: continue
        x,y=limbs(X),limbs(Y); cnt+=1
        d=Div(x,y); m=Mod(x,y)
        if d!=X//Y or m!=X%Y: bad.append([hex(X),hex(Y),hex(d),hex(m)])
    return cnt,bad
if __name__=='__main__':
    n=int(sys.argv[1]); out=sys.argv[2]
    cnt,bad=main(n)
    json.dump({'cases':cnt,'mismatches':len(bad),'examples':bad[:20]},open(out,'w'),indent=1)
    print('cases',cnt,'mismatches',len(bad)); print(bad[:3])
