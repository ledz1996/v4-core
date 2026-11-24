# Generic go1.25.9 math/bits Mul64, Add64, Sub64, Div64 (the code GOARCH=wasm runs, and Div64 on mips64)
# against exact integer arithmetic on edge and random inputs. Usage: python3 -I prims.py <workdir> <out.json>
import sys,random,json; sys.path.insert(0,sys.argv[1]); import u256py as U
U.PRIM='generic'; M=U.M64; rnd=random.Random(7)
E=[0,1,2,3,(1<<32)-1,1<<32,(1<<32)+1,(1<<63)-1,1<<63,(1<<63)+1,M-1,M,0xffffffff00000000,0x00000000ffffffff,0x8000000000000001,0xfffffffeffffffff]
bad={'Mul64':0,'Add64':0,'Sub64':0,'Div64':0,'reciprocal2by1':0}; n=dict.fromkeys(bad,0)
def chk(name,cond):
    n[name]+=1
    if not cond: bad[name]+=1
for x in E:
    for y in E:
        h,l=U.Mul64(x,y); chk('Mul64',(h<<64|l)==x*y)
        for c in (0,1):
            s,co=U.Add64(x,y,c); chk('Add64',(co<<64|s)==x+y+c)
            d,b=U.Sub64(x,y,c); chk('Sub64',d==(x-y-c)&M and b==int(x-y-c<0))
for _ in range(400000):
    x=rnd.choice([rnd.getrandbits(64),rnd.choice(E)^rnd.getrandbits(rnd.choice((1,8,32))),rnd.getrandbits(rnd.randrange(1,65))]); y=rnd.choice([rnd.getrandbits(64),rnd.choice(E),rnd.getrandbits(rnd.randrange(1,65))])
    h,l=U.Mul64(x,y); chk('Mul64',(h<<64|l)==x*y)
    c=rnd.getrandbits(1); s,co=U.Add64(x,y,c); chk('Add64',(co<<64|s)==x+y+c)
    d,b=U.Sub64(x,y,c); chk('Sub64',d==(x-y-c)&M and b==int(x-y-c<0))
    yy=y or 1; hi=rnd.choice([0,rnd.randrange(yy),yy-1]) ; lo=x
    q,r=U.Div64(hi,lo,yy); chk('Div64',q==((hi<<64)|lo)//yy and r==((hi<<64)|lo)%yy)
for d in [1<<63,(1<<63)+1,M,M-1]+[rnd.getrandbits(63)|(1<<63) for _ in range(400000)]:
    rec=U.reciprocal2by1(d); chk('reciprocal2by1',rec==((((~d)&M)<<64)|M)//d)
json.dump({'cases':n,'mismatch':bad},open(sys.argv[2],'w'),indent=1); print(n,bad)
