# Python transcription of src/libraries/TickMath.sol, BitMath.sol, FullMath.sol and Pool.tickSpacingToMaxLiquidityPerTick,
# written from the text of this repo (line numbers in comments), checked against exact integer or high precision arithmetic.
import random, sys, time
from decimal import Decimal, getcontext
M=(1<<256)-1
def u(x): return x & M
def s(x):
    x&=M
    return x-(1<<256) if x>>255 else x
def sdiv(a,b):
    a=s(a);b=s(b)
    if b==0: return 0
    q=abs(a)//abs(b)
    return u(-q if (a<0)!=(b<0) else q)
def smod(a,b):
    a=s(a);b=s(b)
    if b==0: return 0
    r=abs(a)%abs(b)
    return u(-r if a<0 else r)
def slt(a,b): return 1 if s(a)<s(b) else 0
def byte(i,x): return (x>>(8*(31-i)))&0xff if i<32 else 0
def shr(n,x): return (x>>n) if n<256 else 0
def shl(n,x): return u(x<<n) if n<256 else 0

# BitMath.sol:12-25
def msb(x):
    assert x>0
    r=shl(7, 1 if 0xffffffffffffffffffffffffffffffff<x else 0)
    r|=shl(6, 1 if 0xffffffffffffffff<shr(r,x) else 0)
    r|=shl(5, 1 if 0xffffffff<shr(r,x) else 0)
    r|=shl(4, 1 if 0xffff<shr(r,x) else 0)
    r|=shl(3, 1 if 0xff<shr(r,x) else 0)
    r|=byte(0x1f & shr(shr(r,x),0x8421084210842108cc6318c6db6d54be), 0x0706060506020500060203020504000106050205030304010505030400000000)
    return r & 0xff
# BitMath.sol:31-48
def lsb(x):
    assert x>0
    x=x & u(0-x)
    r=shl(5, shr(252, shl(shl(2, shr(250, u(x*0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff))), 0x8040405543005266443200005020610674053026020000107506200176117077)))
    r|=byte((0xd76453e0 // shr(r,x)) & 0x1f, 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405)
    return r & 0xff

MIN_TICK=-887272; MAX_TICK=887272
MIN_SQRT_PRICE=4295128739; MAX_SQRT_PRICE=1461446703485210103287273052203988822378723970342
C=[0xfff97272373d413259a46990580e213a,0xfff2e50f5f656932ef12357cf3c7fdcc,0xffe5caca7e10e4e61c3624eaa0941cd0,0xffcb9843d60f6159c9db58835c926644,0xff973b41fa98c081472e6896dfb254c0,0xff2ea16466c96a3843ec78b326b52861,0xfe5dee046a99a2a811c461f1969c3053,0xfcbe86c7900a88aedcffc83b479aa3a4,0xf987a7253ac413176f2b074cf7815e54,0xf3392b0822b70005940c7a398e4b70f3,0xe7159475a2c29b7443b29c7fa6e889d9,0xd097f3bdfd2022b8845ad8f792aa5825,0xa9f746462d870fdf8a65dc1f90e061e5,0x70d869a156d2a1b890bb3df62baf32f7,0x31be135f97d08fd981231505542fcfa6,0x9aa508b5b7a84e1c677de54f3e99bc9,0x5d6af8dedb81196699c329225ee604,0x2216e584f5fa1ea926041bedfe98,0x48a170391f7dc42444e8fa2]
# TickMath.sol:57-114
def sqrtAt(tick):
    a=abs(tick)
    if a>MAX_TICK: raise ValueError('InvalidTick')
    price = 0xfffcb933bd6fad37aa2d162d1a594001 if a&1 else 1<<128
    for i,c in enumerate(C):
        if a & (2<<i): price=u(price*c)>>128
    if tick>0: price=M//price
    return (price + (1<<32)-1)>>32
# TickMath.sol:121-237
def tickAt(p):
    if ((p-MIN_SQRT_PRICE) % (1<<160)) > MAX_SQRT_PRICE-MIN_SQRT_PRICE-1: raise ValueError('InvalidSqrtPrice')
    price=p<<32
    r=price; m=msb(r)
    r = price>>(m-127) if m>=128 else u(price<<(127-m))
    log_2=u((m-128)<<64)
    for k in range(63,49,-1):
        r=shr(127,u(r*r)); f=shr(128,r); log_2|=shl(k,f)
        if k>50: r=shr(f,r)
    log_sqrt=u(s(log_2)*255738958999603826347141)
    def i24(x):
        x=(s(x)>>128)&0xffffff
        return x-(1<<24) if x>>23 else x
    lo=i24(u(s(log_sqrt)-3402992956809132418596140100660247210)); hi=i24(u(s(log_sqrt)+291339464771989622907027621153398088495))
    return lo if lo==hi else (hi if sqrtAt(hi)<=p else lo)

# FullMath.sol:14-102
def mulDiv(a,b,d):
    prod0=u(a*b); mm=(a*b)%M
    prod1=u(u(mm-prod0)-(1 if mm<prod0 else 0))
    if not d>prod1: raise ValueError('require')
    if prod1==0: return prod0//d
    rem=(a*b)%d
    prod1=u(prod1-(1 if rem>prod0 else 0)); prod0=u(prod0-rem)
    twos=u(0-d)&d
    d//=twos; prod0//=twos
    twos=u(u(0-twos)//twos+1)
    prod0|=u(prod1*twos)
    inv=u(3*d)^2
    for _ in range(6): inv=u(inv*u(2-u(d*inv)))
    return u(prod0*inv)
# Pool.sol:565-582
def maxLiqPerTick(ts):
    minTick=u(sdiv(u(MIN_TICK),u(ts))-slt(smod(u(MIN_TICK),u(ts)),0)); maxTick=sdiv(u(MAX_TICK),u(ts))
    numTicks=u(u(maxTick-minTick)+1)
    return ((1<<128)-1)//numTicks

if __name__=='__main__':
    t0=time.time(); rnd=random.Random(7)
    # BitMath, every bit position with random lower and higher bits
    bad=0
    for k in range(256):
        for _ in range(400):
            x=(1<<k)|rnd.getrandbits(k) if k else 1
            if msb(x)!=k: bad+=1
            y=((rnd.getrandbits(256-k-1)<<(k+1)) if k<255 else 0)|(1<<k)
            if lsb(y)!=k: bad+=1
        if msb(1<<k)!=k or lsb(1<<k)!=k or msb((1<<(k+1))-1)!=k: bad+=1
    print('BitMath mismatches over 256 positions x 400 samples:',bad)
    # bounds
    print('sqrtAt(MIN_TICK)==MIN_SQRT_PRICE',sqrtAt(MIN_TICK)==MIN_SQRT_PRICE,'sqrtAt(MAX_TICK)==MAX_SQRT_PRICE',sqrtAt(MAX_TICK)==MAX_SQRT_PRICE)
    # exact comparison of sqrtAt with 1.0001^(t/2)*2^96 at sample ticks
    getcontext().prec=120
    worst=0
    for t in [MIN_TICK,MIN_TICK+1,-500000,-123457,-1,0,1,2,3,7,60,200,123457,500000,MAX_TICK-1,MAX_TICK]+[rnd.randint(MIN_TICK,MAX_TICK) for _ in range(300)]:
        exact=(Decimal(10001)/Decimal(10000))**(Decimal(t)/2)*Decimal(1<<96)
        rel=abs(Decimal(sqrtAt(t))-exact)/exact
        worst=max(worst,float(rel))
    print('largest relative error of sqrtAt against 1.0001^(t/2)*2^96 on 316 ticks: %.3e'%worst)
    # full sweep: monotone, and tickAt inverts at both sides of every boundary
    prev=None; bad=0; n=0
    for t in range(MIN_TICK,MAX_TICK+1):
        p=sqrtAt(t)
        if prev is not None and not p>prev: bad+=1
        if t<MAX_TICK:
            if tickAt(p)!=t: bad+=1
        if t>MIN_TICK:
            if tickAt(p-1)!=t-1: bad+=1
        prev=p; n+=1
    print('full sweep ticks',n,'violations (monotone, tickAt(sqrtAt(t))==t, tickAt(sqrtAt(t)-1)==t-1):',bad)
    for p in (MIN_SQRT_PRICE-1,MAX_SQRT_PRICE,0,(1<<160)-1):
        try: tickAt(p); print('tickAt accepted out of range',p)
        except ValueError as e: print('tickAt rejects',p)
    # FullMath
    bad=0
    for _ in range(200000):
        a=rnd.getrandbits(rnd.choice([8,64,128,160,200,256])); b=rnd.getrandbits(rnd.choice([8,64,128,160,200,256])); d=rnd.getrandbits(rnd.choice([8,64,128,160,200,256]))
        try: r=mulDiv(a,b,d); ok=True
        except ValueError: ok=False
        exp_ok = d!=0 and (a*b)//d < (1<<256)
        if ok!=exp_ok or (ok and r!=(a*b)//d): bad+=1
    print('FullMath.mulDiv mismatches over 200000 random cases:',bad)
    # max liquidity per tick
    bad=0
    for ts in range(1,32768):
        mn=MIN_TICK//ts  # python floors toward negative infinity
        mx=MAX_TICK//ts
        if maxLiqPerTick(ts)!=((1<<128)-1)//(mx-mn+1): bad+=1
    print('tickSpacingToMaxLiquidityPerTick mismatches for spacing 1..32767 against floor compression:',bad, 'value at 1:',maxLiqPerTick(1),'bits',maxLiqPerTick(1).bit_length())
    print('seconds',round(time.time()-t0))
