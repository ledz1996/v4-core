import json, random, subprocess, sys
M=(1<<256)-1
U={99901:'https://rpc.elysium.kinetiq.xyz'}
C='0x00000000000000000000000000000000c0dec0de'
# code: load a(0),b(0x20),c(0x40); op; return
def code(op,n):
    if n==2: return '602035600035'+op+'60005260206000f3'
    return '6040356020356000356000'[:0]+'604035602035600035'+op+'60005260206000f3'
OPS={'DIV':('04',2),'MOD':('06',2),'SDIV':('05',2),'SMOD':('07',2),'MULMOD':('09',3),'ADDMOD':('08',3)}
def s(x): return x-(1<<256) if x>>255 else x
def ref(op,a,b,c):
    if op=='DIV': return a//b if b else 0
    if op=='MOD': return a%b if b else 0
    if op=='SDIV':
        if b==0: return 0
        q=abs(s(a))//abs(s(b)); return (q if (s(a)<0)==(s(b)<0) else -q)&M
    if op=='SMOD':
        if b==0: return 0
        r=abs(s(a))%abs(s(b)); return (-r if s(a)<0 else r)&M
    if op=='MULMOD': return (a*b)%c if c else 0
    if op=='ADDMOD': return (a+b)%c if c else 0
rnd=random.Random(20261127)
V=[]
for i in range(240):
    op=['DIV','MOD','SDIV','SMOD'][i%4]
    db=rnd.choice((128,192))-rnd.randrange(0,64); d=rnd.getrandbits(db)|(1<<(db-1))|((1<<64)-1 if rnd.random()<.5 else 0)
    Q=rnd.randrange(1,M//d+1); u=(Q*d-rnd.choice((1,2,rnd.getrandbits(64)+1)))
    if u<=0 or u>>255: u&=(1<<255)-1
    if op in('SDIV','SMOD'):
        a=(-u)&M if rnd.random()<.5 else u; b=(-d)&M if rnd.random()<.5 else d
    else: a,b=u,d
    V.append((op,a,b,0))
for i in range(120):
    mb=rnd.choice((128,192))-rnd.randrange(0,64); m=rnd.getrandbits(mb)|(1<<(mb-1))|((1<<64)-1)
    a=rnd.getrandbits(256)|(1<<255); T=rnd.getrandbits(510)|(1<<509); T=T-T%m+m-rnd.choice((1,2,3)); b=min(T//a,M) or 1
    V.append(('MULMOD',a,b,m))
for i in range(60):
    mb=rnd.choice((64,128,192))-rnd.randrange(0,64); m=rnd.getrandbits(mb)|(1<<(mb-1))
    V.append(('ADDMOD',M-rnd.getrandbits(64),M-rnd.getrandbits(200),m))
out={}
for cid,url in U.items():
    batch=[]
    for i,(op,a,b,c) in enumerate(V):
        h,n=OPS[op]; data='0x'+''.join('%064x'%x for x in (a,b,c))
        batch.append({"jsonrpc":"2.0","id":i,"method":"eth_call","params":[{"to":C,"data":data},"latest",{C:{"code":"0x"+code(h,n)}}]})
    res=[]
    import time
    for k in range(0,len(batch),5):
        time.sleep(0.3); r=subprocess.run(['curl','-s','--max-time','60','-X','POST','-H','content-type: application/json','--data',json.dumps(batch[k:k+5]),url],capture_output=True,text=True).stdout
        try: res+=json.loads(r)
        except Exception: res+=[{'id':j,'error':r[:100]} for j in range(k,k+5)]
    mm=[];err=0
    for r in res:
        op,a,b,c=V[r['id']]
        if 'result' not in r: err+=1; continue
        if int(r['result'],16)!=ref(op,a,b,c): mm.append(r['id'])
    out[cid]={'n':len(V),'returned':len(res),'errors':err,'mismatches':mm}
    print(cid,out[cid])
json.dump(out,open(sys.argv[1],'w'),indent=1)
