# Python model of src/libraries/TickMath.sol and BitMath.sol as written in this repo (constants copied by regex from the files)
import re, random
from decimal import Decimal, getcontext
getcontext().prec=120
M=(1<<256)-1
src=open('../../../../../src/libraries/TickMath.sol').read()
consts=[int(x,16) for x in re.findall(r'price \* (0x[0-9a-f]+)\) >> 128',src)]
first=int(re.search(r'xor\(shl\(128, 1\), (0x[0-9a-f]+)\)',src).group(1),16)
assert len(consts)==19
MIN_TICK=-887272; MAX_TICK=887272
MIN_SQRT=4295128739; MAX_SQRT=1461446703485210103287273052203988822378723970342
def sqrtAt(tick):
    a=abs(tick); assert a<=MAX_TICK
    price = first if a&1 else 1<<128
    for i,c in enumerate(consts):
        if a & (2<<i): price=(price*c)>>128
    if tick>0: price=M//price
    return (price + (1<<32)-1)>>32
bm=open('../../../../../src/libraries/BitMath.sol').read()
def msb(x):
    assert x>0
    r=(1 if x>0xffffffffffffffffffffffffffffffff else 0)<<7
    r|=(1 if (x>>r)>0xffffffffffffffff else 0)<<6
    r|=(1 if (x>>r)>0xffffffff else 0)<<5
    r|=(1 if (x>>r)>0xffff else 0)<<4
    r|=(1 if (x>>r)>0xff else 0)<<3
    sh=(0x8421084210842108cc6318c6db6d54be >> (x>>r)) if (x>>r)<256 else 0
    idx=sh&0x1f
    tbl=0x0706060506020500060203020504000106050205030304010505030400000000
    r|=(tbl>>(8*(31-idx)))&0xff
    return r
def lsb(x):
    assert x>0
    x=x&((0-x)&M)
    k1=0xb6db6db6ddddddddd34d34d349249249210842108c6318c639ce739cffffffff
    k2=0x8040405543005266443200005020610674053026020000107506200176117077
    a=((x*k1)&M)>>250
    b=((k2<<(a<<2))&M)>>252
    r=b<<5
    q=(0xd76453e0//(x>>r)) & 0x1f
    tbl=0x001f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405
    r|=(tbl>>(8*(31-q)))&0xff
    return r
for i in range(256):
    assert msb(1<<i)==i and lsb(1<<i)==i, i
    assert msb((1<<i)|1)==i
    assert lsb((1<<255)|(1<<i))==i
for _ in range(200000):
    x=random.getrandbits(random.randint(1,256))|1<<random.randint(0,255)
    assert msb(x)==x.bit_length()-1
    assert lsb(x)==(x&-x).bit_length()-1
print('bitmath ok')
def tickAt(sp):
    assert MIN_SQRT<=sp<MAX_SQRT
    price=sp<<32; r=price; m=msb(r)
    r = price>>(m-127) if m>=128 else price<<(127-m)
    log2=(m-128)<<64   # python int signed
    for i in range(63,49,-1):
        r=((r*r)&M)>>127
        f=r>>128
        log2|= f<<i
        if i!=50: r>>=f
    ls=log2*255738958999603826347141
    lo=(ls-3402992956809132418596140100660247210)>>128
    hi=(ls+291339464771989622907027621153398088495)>>128
    return lo if lo==hi else (hi if sqrtAt(hi)<=sp else lo)
print('min',sqrtAt(MIN_TICK)==MIN_SQRT,'max',sqrtAt(MAX_TICK)==MAX_SQRT)
# accuracy vs true value
worst=0
for t in list(range(-20,21))+[MIN_TICK,MAX_TICK,MIN_TICK+1,MAX_TICK-1]+[random.randint(MIN_TICK,MAX_TICK) for _ in range(3000)]:
    true=(Decimal('1.0001')**(Decimal(t)/2))*(Decimal(2)**96)
    got=Decimal(sqrtAt(t))
    rel=abs(got-true)/true
    worst=max(worst,rel)
    if t<MAX_TICK:
        assert tickAt(sqrtAt(t))==t, t
        if t>MIN_TICK: assert tickAt(sqrtAt(t)-1)==t-1, t
        assert sqrtAt(t+1)>sqrtAt(t)
print('worst rel err',worst)
# each single-bit constant vs true
for i in range(20):
    t=-(1<<i)
    true=(Decimal('1.0001')**(Decimal(t)/2))*(Decimal(2)**128)
    c = first if i==0 else consts[i-1]
    print(i, hex(c), float((Decimal(c)-true)))
