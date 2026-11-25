import json, random, urllib.request
U='https://polygon.api.onfinality.io/public'; A='0x00000000000000000000000000000000000c0de1'
M=(1<<256)-1
def s(x): return x-(1<<256) if x>>255 else x
def run(op, a, b, c=None):
    # push operands then op, mstore result, return 32
    code=''
    if c is not None: code+='7f'+c.to_bytes(32,'big').hex()
    code+='7f'+b.to_bytes(32,'big').hex()+'7f'+a.to_bytes(32,'big').hex()+op+'60005260206000f3'
    d=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':A,'data':'0x'},'latest',{A:{'code':'0x'+code}}]}).encode()
    import time
    for k in range(12):
        try:
            r=json.load(urllib.request.urlopen(urllib.request.Request(U,data=d,headers={'content-type':'application/json','user-agent':'curl/8'}),timeout=30)); break
        except Exception as e:
            time.sleep(3+3*k)
    time.sleep(1.2)
    return int(r['result'],16)
random.seed(15); bad=0; n=0
def ref_sdiv(a,b):
    a,b=s(a),s(b)
    if b==0: return 0
    q=abs(a)//abs(b); q=-q if (a<0)!=(b<0) else q
    return q & M
def ref_smod(a,b):
    a,b=s(a),s(b)
    if b==0: return 0
    r=abs(a)%abs(b); r=-r if a<0 else r
    return r & M
def ref_sar(sh,v):
    return (s(v)>>min(sh,256)) & M if sh<256 else (M if s(v)<0 else 0)
cases=[]
for _ in range(10):
    a=random.getrandbits(256); b=random.getrandbits(random.choice([8,64,128,192,256])) or 1; m=random.choice([M, random.getrandbits(256)|1<<255, random.getrandbits(128)|1, 1<<96, 1<<128])
    cases.append(('09',a,b,m,(a*b)%m))   # MULMOD a b m
    cases.append(('05',a,b,None,ref_sdiv(a,b)))
    cases.append(('07',a,b,None,ref_smod(a,b)))
    sh=random.choice([0,1,8,128,255,256,300,random.getrandbits(256)])
    cases.append(('1d',sh,a,None,ref_sar(sh,a)))
for op,a,b,c,exp in cases:
    # stack order: for MULMOD top is a, then b, then m: pushes c,b,a -> a on top
    got=run(op,a,b,c); n+=1; print(n, op, got==exp, flush=True)
    if got!=exp: bad+=1; print('MISMATCH',op,hex(a),hex(b),c,hex(got),hex(exp))
print('onfinality bor v2.11.2 probes',n,'mismatches',bad)
