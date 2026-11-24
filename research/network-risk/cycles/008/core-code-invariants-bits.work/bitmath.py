import re,random
t=open('/home/user/v4-core/src/libraries/BitMath.sol').read()
U=(1<<256)-1
hx=[int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',t.split('library BitMath')[1])]
print([hex(h) for h in hx])
A,B,C,D,E_,F_,G,H,I,J,K=None,None,None,None,None,None,None,None,None,None,None
def byte(i,x): return (x>>(8*(31-i)))&0xff if i<32 else 0
# read constants by position in the text
m1=re.search(r'shr\(shr\(r, x\), (0x[0-9a-f]+)\)\),\s*(0x[0-9a-f]+)\)\)',t); MS1,MS2=int(m1.group(1),16),int(m1.group(2),16)
m2=re.search(r'mul\(x,\s*(0x[0-9a-f]+)\)\)\),\s*(0x[0-9a-f]+)\)\)\)',t); LS1,LS2=int(m2.group(1),16),int(m2.group(2),16)
m3=re.search(r'div\((0x[0-9a-f]+), shr\(r, x\)\), 0x1f\),\s*(0x[0-9a-f]+)\)\)',t); LS3,LS4=int(m3.group(1),16),int(m3.group(2),16)
def shl(s,x): return (x<<s)&U if s<256 else 0
def shr(s,x): return x>>s if s<256 else 0
def msb(x):
    assert x>0
    r=(1 if 0xffffffffffffffffffffffffffffffff<x else 0)<<7
    r|=(1 if 0xffffffffffffffff<shr(r,x) else 0)<<6
    r|=(1 if 0xffffffff<shr(r,x) else 0)<<5
    r|=(1 if 0xffff<shr(r,x) else 0)<<4
    r|=(1 if 0xff<shr(r,x) else 0)<<3
    r|=byte(0x1f & shr(shr(r,x),MS1), MS2)
    return r & 0xff
def lsb(x):
    assert x>0
    x=x&((0-x)&U)
    r=shl(5, shr(252, shl(shl(2, shr(250,(x*LS1)&U)), LS2)))
    r|=byte((LS3//shr(r,x))&0x1f, LS4)
    return r & 0xff
bad=0
for i in range(256):
    if msb(1<<i)!=i or lsb(1<<i)!=i: bad+=1
    if msb((1<<(i+1))-1)!=i: bad+=1
    if lsb(U^((1<<i)-1))!=i: bad+=1
random.seed(1)
for _ in range(300000):
    n=random.randint(1,256); x=random.getrandbits(n)|1<<(n-1)
    x&=U
    if msb(x)!=x.bit_length()-1: bad+=1
    if lsb(x)!=(x&-x).bit_length()-1: bad+=1
# r is uint8 returned from assembly: check no value above 255 before masking
print('BitMath failures:',bad)
# literal check of the fixed thresholds in msb
assert 'lt(0xffffffffffffffffffffffffffffffff, x)' in t and 'lt(0xffffffffffffffff, shr(r, x))' in t and 'lt(0xffffffff, shr(r, x))' in t and 'lt(0xffff, shr(r, x))' in t and 'lt(0xff, shr(r, x))' in t
print('threshold literals ok')
