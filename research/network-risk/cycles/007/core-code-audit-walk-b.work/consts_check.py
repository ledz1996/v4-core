# Independent checks of numeric constants named by the Spearbit and ABDK reports, against the text of src/.
import re, sys, os, random
from decimal import Decimal, getcontext
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak, sel
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../..'))
def rd(p): return open(os.path.join(ROOT,p)).read()
getcontext().prec=200
M=(1<<256)-1
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); out.append(s); print(s)

# 1. hex literal lengths in every non-test src file
P('== hex literals of 0xff.. form and their bit widths')
import glob
for f in sorted(glob.glob(os.path.join(ROOT,'src/**/*.sol'),recursive=True)):
    if '/test/' in f: continue
    for n,line in enumerate(open(f),1):
        for m in re.finditer(r'0x[0-9a-fA-F]+',line):
            h=m.group(0)[2:]
            if len(h)>=6 and set(h.lower())<=set('f0'):
                P(' ',os.path.relpath(f,ROOT)+':'+str(n), 'digits',len(h),'f-digits',h.lower().count('f'),'value-bits',int(h,16).bit_length(), h[:6]+'..' if len(h)>12 else h)

# 2. slots and selectors
P('== transient slots')
def slot(s): return '0x%064x'%(int.from_bytes(keccak(s.encode()),'big')-1)
for name,f,pat in [('Unlocked','src/libraries/Lock.sol',r'IS_UNLOCKED_SLOT = (0x[0-9a-f]+)'),('NonzeroDeltaCount','src/libraries/NonzeroDeltaCount.sol',r'NONZERO_DELTA_COUNT_SLOT =\s+(0x[0-9a-f]+)'),('ReservesOf','src/libraries/CurrencyReserves.sol',r'RESERVES_OF_SLOT = (0x[0-9a-f]+)'),('Currency','src/libraries/CurrencyReserves.sol',r'CURRENCY_SLOT = (0x[0-9a-f]+)')]:
    v=re.search(pat,rd(f)).group(1); P(' ',name,v==slot(name),v)
for f in ['src/libraries/TransientStateLibrary.sol','src/libraries/StateLibrary.sol']:
    for m in re.finditer(r'(\w+)\s*=\s*\n?\s*(0x[0-9a-f]{64})',rd(f)): P('  lib const',f,m.group(1),m.group(2))
P('== selectors in assembly')
for sig,f in [('TickMisaligned(int24,int24)','src/libraries/TickBitmap.sol'),('SafeCastOverflow()','src/libraries/LiquidityMath.sol'),('PriceOverflow()','src/libraries/SqrtPriceMath.sol'),('NotEnoughLiquidity()','src/libraries/SqrtPriceMath.sol'),('InvalidPriceOrLiquidity()','src/libraries/SqrtPriceMath.sol'),('InvalidPrice()','src/libraries/SqrtPriceMath.sol'),('transfer(address,uint256)','src/types/Currency.sol')]:
    s=sel(sig); P(' ',sig,s, ('0x'+s) in rd(f) or ('0x'+s.lstrip('0')) in rd(f) or s in rd(f))
x=0
for s in ['transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)','balanceOf(address,uint256)','allowance(address,address,uint256)','isOperator(address,address)']: x^=int(sel(s),16)
P('  erc6909 interface id',hex(x),'0x0f632fb3' in rd('src/ERC6909.sol'), 'erc165',sel('supportsInterface(bytes4)'))

# 3. TickMath ratio constants against exact values
P('== TickMath ratio constants: exact 2^128/sqrt(1.0001)^(2^i), nearest and ceil')
src=rd('src/libraries/TickMath.sol')
first=int(re.search(r'xor\(shl\(128, 1\), (0x[0-9a-f]+)\)',src).group(1),16)
consts=[first]+[int(x,16) for x in re.findall(r'price \* (0x[0-9a-f]+)\) >> 128',src)]
masks=[int(x,16) for x in re.findall(r'absTick & (0x[0-9a-f]+) != 0',src)]
P('  masks ok',masks==[2<<i for i in range(19)], len(consts))
getcontext().prec=400
base=Decimal(10001)/Decimal(10000)
for i,c in enumerate(consts):
    exact=Decimal(1<<128)/(base.sqrt()**(2**i))
    near=int(exact.to_integral_value(rounding='ROUND_HALF_EVEN')); ce=int(exact.to_integral_value(rounding='ROUND_CEILING'))
    P('  h%d'%i,hex(c),'nearest' if c==near else 'NOT-nearest','ceil' if c==ce else 'not-ceil','diff from exact %.3f'%float(Decimal(c)-exact))
