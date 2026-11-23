# Python transcription of the assembly in src/libraries/ProtocolFeeLibrary.sol, LiquidityMath.sol, SwapMath.sol:20-37, TickBitmap.sol:16-29, Pool.sol:565-582
# checked against the high level statement given in the comment next to each block (Trail of Bits UNI-PROTOFEE-1/2, UNI-LIQMATH-1/2, UNI-LOWLEVEL-3/4/5/6/7/8).
import random
M=1<<256
def s(x): x%=M; return x-M if x>>255 else x
def signextend(b,x):
    bits=8*(b+1); x&=(1<<bits)-1
    return (x-(1<<bits))%M if x>>(bits-1) else x
def sdiv(a,b):
    a=s(a); b=s(b)
    if b==0: return 0
    q=abs(a)//abs(b); return (q if (a<0)==(b<0) else -q)%M
def smod(a,b):
    a=s(a); b=s(b)
    if b==0: return 0
    r=abs(a)%abs(b); return (r if a>=0 else -r)%M
def slt(a,b): return 1 if s(a)<s(b) else 0
# isValidProtocolFee over all uint24
bad=0
for v in range(1<<24):
    asm=(1 if (v&0xfff)<1001 else 0)&(1 if (v&0xfff000)<(1001<<12) else 0)
    hi=((v&0xfff)<=1000) and ((v>>12)<=1000)
    if bool(asm)!=hi: bad+=1
print('isValidProtocolFee mismatches over 2^24 inputs:',bad)
# calculateSwapFee bound and equivalence
mx=0
for p in range(0,1001):
    for l in list(range(0,2000))+list(range(999_000,1_000_001))+[random.randrange(0,1_000_001) for _ in range(200)]:
        sw=(p+l-(p*l)//1_000_000)
        ref=p+ -(-(l*(1_000_000-p))//1_000_000)   # p + ceil(l*(1e6-p)/1e6)
        assert sw==ref,(p,l)
        assert sw>=p and sw<=1_000_000
        mx=max(mx,sw)
print('calculateSwapFee max',mx)
# addDelta
def addDelta(x,y):
    z=((x&((1<<128)-1))+signextend(15,y%M))%M
    if z>>128: return None
    return z
for _ in range(200000):
    x=random.getrandbits(128); y=random.randrange(-(1<<127),1<<127)
    r=addDelta(x,y); t=x+y
    assert (r==t) if 0<=t<(1<<128) else (r is None)
for x,y in [(0,-1),((1<<128)-1,1),(0,-(1<<127)),((1<<128)-1,(1<<127)-1),(1<<127,-(1<<127))]:
    r=addDelta(x,y); t=x+y; assert (r==t) if 0<=t<(1<<128) else (r is None)
print('addDelta ok')
# getSqrtPriceTarget
for _ in range(200000):
    n=random.getrandbits(160); l=random.getrandbits(160); z=random.getrandbits(1)
    nol=(1 if n<l else 0)^(z&1); sym=n^l; t=l^(sym*nol)
    assert t==(max(n,l) if z else min(n,l))
print('getSqrtPriceTarget ok')
# compress and tickSpacingToMaxLiquidityPerTick
MIN=-887272; MAX=887272
def compress(t,sp):
    t=signextend(2,t%M); sp=signextend(2,sp%M)
    return s((sdiv(t,sp)-slt(smod(t,sp),0))%M)
import math
for _ in range(300000):
    t=random.randint(MIN,MAX); sp=random.randint(1,32767)
    assert compress(t,sp)==math.floor(t/sp) if False else compress(t,sp)==(t//sp)
def maxLiq(sp):
    sp=signextend(2,sp%M)
    mn=(sdiv(MIN%M,sp)-slt(smod(MIN%M,sp),0))%M
    mxx=sdiv(MAX%M,sp)
    n=(mxx-mn+1)%M
    return ((1<<128)-1)//n
for sp in list(range(1,3000))+[32767,16384,200,60,10]:
    n=(MAX//sp)-(MIN//sp)+1  # floor division: MIN//sp rounds toward minus infinity
    assert maxLiq(sp)==((1<<128)-1)//n
print('compress and maxLiquidityPerTick ok; cap spacing 1 =',maxLiq(1))
