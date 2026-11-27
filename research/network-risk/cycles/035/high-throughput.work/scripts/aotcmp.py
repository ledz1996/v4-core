import random, subprocess, json, sys
M=1<<256; MX=M-1; H=1<<255
def s(x): return x-M if x>=H else x
def u(x): return x%M
def ref(op,a,b,c):
    if op=='DIV': return 0 if b==0 else a//b
    if op=='SDIV':
        if b==0: return 0
        q=abs(s(a))//abs(s(b)); return u(-q if (s(a)<0)!=(s(b)<0) else q)
    if op=='MOD': return 0 if b==0 else a%b
    if op=='SMOD':
        if b==0: return 0
        r=abs(s(a))%abs(s(b)); return u(-r if s(a)<0 else r)
    if op=='ADDMOD': return 0 if c==0 else (a+b)%c
    if op=='MULMOD': return 0 if c==0 else (a*b)%c
    if op=='EXP': return pow(a,b,M)
    if op=='SIGNEXTEND':
        if a>=31: return b
        bit=8*a+7; v=b&((1<<(bit+1))-1)
        return u(v-(1<<(bit+1))) if (v>>bit)&1 else v
    if op=='LT': return int(a<b)
    if op=='GT': return int(a>b)
    if op=='SLT': return int(s(a)<s(b))
    if op=='SGT': return int(s(a)>s(b))
    if op=='BYTE': return 0 if a>=32 else (b>>(8*(31-a)))&0xff
    if op=='SHL': return 0 if a>=256 else (b<<a)%M
    if op=='SHR': return 0 if a>=256 else b>>a
    if op=='SAR': return u(s(b)>>min(a,256)) if a<256 else (MX if s(b)<0 else 0)
random.seed(35)
edges=[0,1,2,3,7,8,15,16,30,31,32,33,127,128,191,192,254,255,256,257,1<<64,(1<<128)-1,1<<128,(1<<160)-1,H-1,H,H+1,MX-1,MX]
def rnd():
    k=random.randrange(6)
    if k==0: return random.choice(edges)
    if k==1: return random.getrandbits(random.randrange(1,257))
    if k==2: return u(-random.getrandbits(random.randrange(1,200)))
    return random.getrandbits(256)
ops=['DIV','SDIV','MOD','SMOD','ADDMOD','MULMOD','EXP','SIGNEXTEND','LT','GT','SLT','SGT','BYTE','SHL','SHR','SAR']
cases=[]
for op in ops:
    for a in edges:
        for b in edges: cases.append((op,a,b,random.choice(edges)))
    for _ in range(3000):
        a,b,c=rnd(),rnd(),rnd()
        if op in('SIGNEXTEND','BYTE') and random.random()<0.7: a=random.randrange(40)
        if op in('SHL','SHR','SAR') and random.random()<0.7: a=random.randrange(300)
        cases.append((op,a,b,c))
# PoolManager shapes
for _ in range(2000):
    t=random.randrange(-887272,887273); cases.append(('SIGNEXTEND',2,u(t),0)); cases.append(('SAR',255,u(t),0))
    d=u(random.randrange(-(1<<127),1<<127)); cases.append(('SIGNEXTEND',15,d,0)); cases.append(('SAR',128,u(random.randrange(-(1<<200),1<<200)),0))
    cases.append(('SAR',8,u(t),0)); cases.append(('BYTE',random.randrange(32),random.getrandbits(256),0))
inp=''.join('%s %x %x %x\n'%c for c in cases)
out={}
for b in ['h_O0','h_O2']:
    r=subprocess.run(['./aot/'+b],input=inp,capture_output=True,text=True).stdout.split()
    per={}
    ex={}
    for (op,a,bb,c),w in zip(cases,r):
        ok=int(w,16)==ref(op,a,bb,c)
        p=per.setdefault(op,[0,0]); p[0]+=1; p[1]+= (not ok)
        if not ok and len(ex.setdefault(op,[]))<3: ex[op].append({'a':hex(a),'b':hex(bb),'c':hex(c),'got':'0x'+w.lstrip('0') if w.strip('0') else '0x0','want':hex(ref(op,a,bb,c))})
    # PoolManager-shape subsets
    out[b]={'perOp':per,'examples':ex}
json.dump({'cases':len(cases),'results':out},open('out/aot-handlers.json','w'),indent=1)
for b in out: print(b,{k:v for k,v in out[b]['perOp'].items()})
