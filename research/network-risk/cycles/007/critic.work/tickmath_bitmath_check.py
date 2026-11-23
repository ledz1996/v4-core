import re, random
from decimal import Decimal, getcontext
getcontext().prec = 120
src=open('/home/user/v4-core/src/libraries/TickMath.sol').read()
M=(1<<256)-1
consts=[int(x,16) for x in re.findall(r'price \* (0x[0-9a-f]+)\) >> 128', src)]
first=int(re.search(r'xor\(shl\(128, 1\), (0x[0-9a-f]+)\)', src).group(1),16)
allc=[first]+consts
print(len(allc))
bad=0
for i,c in enumerate(allc):
    exact = (Decimal(2)**128) / (Decimal('1.0001')**(Decimal(2**i)/2))
    diff = Decimal(c)-exact
    if abs(diff) > 1: bad+=1; print('const',i,hex(c),'diff',diff)
print('bad consts',bad)
MIN_TICK=-887272; MAX_TICK=887272
def sp(tick):
    a=abs(tick); assert a<=MAX_TICK
    price = first if a&1 else 1<<128
    for i,c in enumerate(consts):
        if a & (2<<i): price=(price*c)>>128
    if tick>0: price=M//price
    return (price+(1<<32)-1)>>32
print(sp(MIN_TICK), sp(MAX_TICK))
print(sp(MIN_TICK)==4295128739, sp(MAX_TICK)==1461446703485210103287273052203988822378723970342)
bm=open('/home/user/v4-core/src/libraries/BitMath.sol').read()
def byte(i,x): return (x>>(8*(31-i)))&0xff if i<32 else 0
def msb(x):
    r=(1 if 0xffffffffffffffffffffffffffffffff<x else 0)<<7
    r|=(1 if 0xffffffffffffffff<(x>>r) else 0)<<6
    r|=(1 if 0xffffffff<(x>>r) else 0)<<5
    r|=(1 if 0xffff<(x>>r) else 0)<<4
    r|=(1 if 0xff<(x>>r) else 0)<<3
    r|=byte(0x1f & (0x8421084210842108cc6318c6db6d54be >> (x>>r)), 0x0706060506020500060203020504000106050205030304010505030400000000)
    return r
def lsb(x):
    x = x & ((-x)&M)
    r = ((0x8040405543005266443200005020610674053026020000107506200176117077 << ((((x*0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff)&M)>>250)<<2))&M)>>252
    r <<=5
    r |= byte((0xd76453e0 // (x>>r)) & 0x1f, 0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405)
    return r
ok=True
for i in range(256):
    for _ in range(20):
        x=(1<<i)|random.getrandbits(i) if i else 1
        if msb(x)!=i: ok=False; print('msb bad',i); break
        y=(random.getrandbits(256)|1)<<i & M
        if y and lsb(y)!=i: ok=False; print('lsb bad',i); break
print('bitmath ok',ok)
def tick_at(s):
    assert 4295128739<=s<1461446703485210103287273052203988822378723970342
    price=s<<32; m=msb(price)
    r = price>>(m-127) if m>=128 else price<<(127-m)
    log2=((m-128)<<64)
    for k in range(63,49,-1):
        r=(r*r)>>127; f=r>>128; log2|=f<<k
        if k>50: r>>=f
    l=log2*255738958999603826347141
    lo=(l-3402992956809132418596140100660247210)>>128
    hi=(l+291339464771989622907027621153398088495)>>128
    return lo if lo==hi else (hi if sp(hi)<=s else lo)
bad=0
ts=[MIN_TICK,MIN_TICK+1,-1,0,1,MAX_TICK-1]+[random.randint(MIN_TICK,MAX_TICK-1) for _ in range(20000)]
for t in ts:
    s=sp(t)
    if tick_at(s)!=t: bad+=1
    if s-1>=4295128739 and tick_at(s-1)!=t-1: bad+=1
    exact=(Decimal('1.0001')**(Decimal(t)/2))*(Decimal(2)**96)
    if abs(Decimal(s)-exact) > 2 + exact*Decimal('1e-17'): bad+=1; print('price off',t, s, exact)
print('roundtrip bad',bad)
