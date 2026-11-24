import re,random
from decimal import Decimal,getcontext
getcontext().prec=120
R='/home/user/v4-core/src/libraries/'
t=open(R+'TickMath.sol').read()
U=(1<<256)-1
first=int(re.search(r'xor\(shl\(128, 1\), (0x[0-9a-f]+)\), and\(absTick, 0x1\)',t).group(1),16)
rest=[(int(a,16),int(b,16)) for a,b in re.findall(r'if \(absTick & (0x[0-9a-f]+) != 0\) price = \(price \* (0x[0-9a-f]+)\) >> 128;',t)]
consts=[(1,first)]+rest
assert [c[0] for c in consts]==[1<<i for i in range(20)], [hex(c[0]) for c in consts]
bad=0
for i,(bit,c) in enumerate(consts):
    exact=(Decimal(2)**128)/(Decimal('1.0001').sqrt()**(1<<i))
    d=abs(Decimal(c)-exact)
    if d>Decimal('0.5001'): bad+=1; print('BAD const',i,hex(c),d)
print('tick multipliers within 0.5 of exact:', 20-bad,'of 20')
MIN_TICK=int(re.search(r'MIN_TICK = (-?\d+);',t).group(1)); MAX_TICK=int(re.search(r'MAX_TICK = (-?\d+);',t).group(1))
MIN_P=int(re.search(r'MIN_SQRT_PRICE = (\d+);',t).group(1)); MAX_P=int(re.search(r'MAX_SQRT_PRICE = (\d+);',t).group(1))
m=re.search(r'MAX_SQRT_PRICE_MINUS_MIN_SQRT_PRICE_MINUS_ONE =\s*(\d+) - (\d+) - 1;',t)
THR=int(m.group(1))-int(m.group(2))-1
assert int(m.group(1))==MAX_P and int(m.group(2))==MIN_P
LOGMUL=int(re.search(r'log_2 \* (\d+);',t).group(1))
LOW=int(re.search(r'log_sqrt10001 - (\d+)\) >> 128',t).group(1)); HI=int(re.search(r'log_sqrt10001 \+ (\d+)\) >> 128',t).group(1))
shifts=[int(x) for x in re.findall(r'log_2 := or\(log_2, shl\((\d+), f\)\)',t)]
assert shifts==list(range(63,49,-1)), shifts
assert t.count('r := shr(127, mul(r, r))')==14 and t.count('let f := shr(128, r)')==14 and t.count('r := shr(f, r)')==13
def sqrtAt(tick):
    a=abs(tick)
    assert a<=MAX_TICK
    price=first if a&1 else 1<<128
    for bit,c in rest:
        if a&bit: price=(price*c)>>128
    if tick>0: price=U//price
    return (price+(1<<32)-1)>>32
def msb(x): return x.bit_length()-1
def tickAt(p):
    assert ((p-MIN_P)%(1<<160))<=THR   # uint160 unchecked subtraction
    price=p<<32
    m_=msb(price)
    r=price>>(m_-127) if m_>=128 else price<<(127-m_)
    log2=(m_-128)<<64   # python int signed
    for s in range(63,49,-1):
        r=(r*r)>>127
        f=r>>128
        log2|=f<<s
        if s!=50: r>>=f
    ls=log2*LOGMUL
    lo=(ls-LOW)>>128; hi=(ls+HI)>>128
    return lo if lo==hi else (hi if sqrtAt(hi)<=p else lo)
print('MIN', sqrtAt(MIN_TICK)==MIN_P, 'MAX', sqrtAt(MAX_TICK)==MAX_P, MIN_TICK==-887272, MAX_TICK==887272)
# log multiplier: 2^64 * 2^128... log_sqrt10001 = log2 * (2^64/ log2(sqrt(1.0001)))
exact=(Decimal(2)**64)/(Decimal('1.0001').sqrt().ln()/Decimal(2).ln())
print('log multiplier diff', Decimal(LOGMUL)-exact)
# full monotonic scan
prev=0;mono=True
for tk in range(MIN_TICK,MAX_TICK+1):
    p=sqrtAt(tk)
    if p<=prev: mono=False;print('non mono',tk);break
    prev=p
print('strictly increasing over all ticks:',mono)
# roundtrip samples incl. boundaries
random.seed(8)
ticks=[MIN_TICK,MIN_TICK+1,-1,0,1,MAX_TICK-1]+[random.randint(MIN_TICK,MAX_TICK-1) for _ in range(60000)]
bad=0
for tk in ticks:
    p=sqrtAt(tk)
    if tickAt(p)!=tk: bad+=1
    if tk>MIN_TICK and tickAt(p-1)!=tk-1: bad+=1
    q=sqrtAt(tk+1)-1
    if tickAt(q)!=tk: bad+=1
print('roundtrip failures:',bad,'of',len(ticks)*3)
for p in (MIN_P-1,MAX_P,0,(1<<160)-1):
    try: tickAt(p); print('accepted out of range',p)
    except AssertionError: print('rejects',p)
# dense scan around each power of two tick and low ticks
bad=0
for c in [0]+[s*(1<<i) for i in range(20) for s in (1,-1)]:
    for tk in range(max(MIN_TICK,c-300),min(MAX_TICK-1,c+300)+1):
        p=sqrtAt(tk)
        if tickAt(p)!=tk or tickAt(sqrtAt(tk+1)-1)!=tk: bad+=1
print('dense boundary scan failures:',bad)
