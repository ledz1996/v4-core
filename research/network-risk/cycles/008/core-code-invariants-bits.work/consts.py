import re,sys
from keccak import keccak256
from decimal import Decimal, getcontext
getcontext().prec=200
R='/home/user/v4-core/src/'
def src(p): return open(R+p).read()
ok=True
def chk(name,cond,extra=''):
    global ok
    print(('OK  ' if cond else 'BAD ')+name, extra)
    if not cond: ok=False
# 1 transient slots
for f,cn,s in [('libraries/Lock.sol','IS_UNLOCKED_SLOT','Unlocked'),('libraries/CurrencyReserves.sol','RESERVES_OF_SLOT','ReservesOf'),('libraries/CurrencyReserves.sol','CURRENCY_SLOT','Currency'),('libraries/NonzeroDeltaCount.sol','NONZERO_DELTA_COUNT_SLOT','NonzeroDeltaCount')]:
    t=src(f)
    m=re.search(cn+r'\s*=\s*(0x[0-9a-fA-F]+)',t)
    v=int(m.group(1),16)
    exp=int.from_bytes(keccak256(s.encode()),'big')-1
    chk(f'{cn} == keccak({s})-1', v==exp, hex(v))
    chk(f'{cn} literal has 64 hex digits', len(m.group(1))==66)
# 2 selectors
sels={'TickMisaligned(int24,int24)':('libraries/TickBitmap.sol','d4d8f3e6'),
'SafeCastOverflow()':('libraries/LiquidityMath.sol','93dafdf1'),
'PriceOverflow()':('libraries/SqrtPriceMath.sol','f5c787f1'),
'NotEnoughLiquidity()':('libraries/SqrtPriceMath.sol','4323a555'),
'InvalidPriceOrLiquidity()':('libraries/SqrtPriceMath.sol','4f2461b8'),
'InvalidPrice()':('libraries/SqrtPriceMath.sol','00bfc921'),
'transfer(address,uint256)':('types/Currency.sol','a9059cbb')}
for sig,(f,h) in sels.items():
    got=keccak256(sig.encode()).hex()[:8]
    chk(f'selector {sig} = {got}', got==h and ('0x'+h) in src(f))
# erc165
x=0
for s in ['balanceOf(address,uint256)','allowance(address,address,uint256)','isOperator(address,address)','transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)']:
    x^=int(keccak256(s.encode()).hex()[:8],16)
chk('ERC6909 interface id 0x0f632fb3', x==0x0f632fb3, hex(x))
chk('ERC165 id', keccak256(b'supportsInterface(bytes4)').hex()[:8]=='01ffc9a7')
# 3 Slot0
t=src('types/Slot0.sol')
m160=int(re.search(r'MASK_160_BITS = (0x[0-9A-Fa-f]+)',t).group(1),16)
m24=int(re.search(r'MASK_24_BITS = (0x[0-9A-Fa-f]+)',t).group(1),16)
chk('MASK_160', m160==(1<<160)-1); chk('MASK_24', m24==(1<<24)-1)
offs={k:int(re.search(k+r' = (\d+)',t).group(1)) for k in ['TICK_OFFSET','PROTOCOL_FEE_OFFSET','LP_FEE_OFFSET']}
chk('Slot0 offsets 160/184/208', offs=={'TICK_OFFSET':160,'PROTOCOL_FEE_OFFSET':184,'LP_FEE_OFFSET':208}, offs)
fields=[(0,160),(offs['TICK_OFFSET'],24),(offs['PROTOCOL_FEE_OFFSET'],24),(offs['LP_FEE_OFFSET'],24)]
masks=[((1<<w)-1)<<o for o,w in fields]
chk('Slot0 fields disjoint', all(masks[i]&masks[j]==0 for i in range(4) for j in range(i)))
chk('Slot0 fields fit 256', max(o+w for o,w in fields)<=256, max(o+w for o,w in fields))
# address masks: every 0xfff.. literal in src (non test) list distinct lengths
import os,glob
lits={}
for p in glob.glob(R+'**/*.sol',recursive=True):
    if '/test/' in p: continue
    for i,l in enumerate(open(p).read().split('\n'),1):
        code=l.split('//')[0]
        for m in re.finditer(r'0x[fF]{6,}\b',code):
            lits.setdefault(len(m.group(0))-2,[]).append(f'{p[len(R):]}:{i}')
for k in sorted(lits): print('  all-f literal of',k,'hex digits (',k*4,'bits ):',len(lits[k]),'uses', lits[k] if len(lits[k])<8 else lits[k][:3]+['...'])
chk('all-f literal widths are 16/32/40/64 only', set(lits)<= {6,8,16,32,40,64}, sorted(lits))
# 4 fee constants
t=src('libraries/LPFeeLibrary.sol')
chk('DYNAMIC_FEE_FLAG 0x800000', 'DYNAMIC_FEE_FLAG = 0x800000;' in t)
chk('OVERRIDE_FEE_FLAG 0x400000', 'OVERRIDE_FEE_FLAG = 0x400000;' in t)
chk('REMOVE_OVERRIDE_MASK', 'REMOVE_OVERRIDE_MASK = 0xBFFFFF;' in t and 0xBFFFFF==(0xFFFFFF^0x400000))
chk('MAX_LP_FEE', 'MAX_LP_FEE = 1000000;' in t)
t=src('libraries/ProtocolFeeLibrary.sol')
chk('protocol fee thresholds', 'FEE_0_THRESHOLD = 1001;' in t and 'FEE_1_THRESHOLD = 1001 << 12;' in t and 'MAX_PROTOCOL_FEE = 1000;' in t and 'PIPS_DENOMINATOR = 1_000_000;' in t)
# brute force isValidProtocolFee over all uint24
bad=0
for s in range(1<<24):
    v=((s&0xfff)<1001) and ((s&0xfff000)<(1001<<12))
    e=((s&0xfff)<=1000) and ((s>>12)<=1000)
    if v!=e: bad+=1
chk('isValidProtocolFee == both halves <= 1000 for all uint24', bad==0, bad)
# calculateSwapFee max
mx=max(((p+l) - (p*l)//10**6) for p in (0,1,1000) for l in (0,1,999999,10**6))
chk('swap fee <= 1e6 at bounds', mx<=10**6, mx)
worst=max((p+l-(p*l)//10**6) for p in range(0,1001) for l in (10**6,10**6-1,10**6-1000,500000))
chk('swap fee <= 1e6 for all protocol fees at top lp fees', worst<=10**6, worst)
# 5 hook flags
t=src('libraries/Hooks.sol')
flags=dict((m.group(1),int(m.group(2))) for m in re.finditer(r'uint160 internal constant (\w+_FLAG) = 1 << (\d+);',t))
print('  flags',flags)
chk('14 distinct flags 0..13', sorted(flags.values())==list(range(14)))
chk('ALL_HOOK_MASK', 'ALL_HOOK_MASK = uint160((1 << 14) - 1);' in t)
# FixedPoint
chk('Q128', int(re.search(r'Q128 = (0x[0-9a-f]+)',src('libraries/FixedPoint128.sol')).group(1),16)==1<<128)
chk('Q96', int(re.search(r'Q96 = (0x[0-9a-f]+)',src('libraries/FixedPoint96.sol')).group(1),16)==1<<96)
chk('RESOLUTION 96','RESOLUTION = 96;' in src('libraries/FixedPoint96.sol'))
chk('MAX_SWAP_FEE','MAX_SWAP_FEE = 1e6;' in src('libraries/SwapMath.sol'))
# StateLibrary
t=src('libraries/StateLibrary.sol')
chk('POOLS_SLOT 6','POOLS_SLOT = bytes32(uint256(6));' in t)
print('ALL OK' if ok else 'SOME BAD')
