# Check the interpreter's outputs of selected micro programs against the EVM specification in Python
import subprocess,sys,re
M=(1<<256)-1
def s(x): return x-(1<<256) if x>>255 else x
def u(x): return x&M
def spec(op,a,b,c=None):
    if op=='SHL': return u(b<<a) if a<256 else 0
    if op=='SHR': return b>>a if a<256 else 0
    if op=='SAR': return u(s(b)>>min(a,256))
    if op=='BYTE': return (b>>(8*(31-a)))&0xff if a<32 else 0
    if op=='SIGNEXTEND':
        if a>=31: return b
        bit=8*a+7; m=(1<<bit)
        return u((b&(m*2-1))-((b&m)<<1)) if True else 0
    if op=='SDIV':
        if b==0: return 0
        q=abs(s(a))//abs(s(b)); return u(q if (s(a)<0)==(s(b)<0) else -q)
    if op=='SMOD':
        if b==0: return 0
        r=abs(s(a))%abs(s(b)); return u(-r if s(a)<0 else r)
    if op=='MULMOD': return (a*b)%c if c else 0
    if op=='ADDMOD': return (a+b)%c if c else 0
PR=[(l.split()[0],bytes.fromhex(l.split()[2])) for l in open('micro/progs.txt') if l.strip()]
names=[n for n,_ in PR]
want=re.compile(sys.argv[1])
src=open('micro/scen.txt').read().split('SCEN ')
idx=[i for i,(n,_) in enumerate(PR) if want.search(n)]
sel=set(names[i] for i in idx)
sub=''.join('SCEN '+src[1+i] for i in idx)
open('micro/_sel.txt','w').write(sub)
out=subprocess.run(['./hx','micro/world.txt','micro/_sel.txt','-v'],capture_output=True,text=True).stdout
# map scenario -> list of calldata
CDS=[[l.split()[5] if len(l.split())>5 else '' for l in src[1+i].split('\n')[1:] if l.startswith('TX')] for i in idx]
k=-1;cur=None;mode=None;bad=0;n=0
for l in out.split('\n'):
    if l.startswith(('SAME ','DIFF ')): cur=l.split()[1]; k+=1
    elif l.startswith('--- '): mode=l[4:]
    elif l.startswith('tx ') and mode=='interp':
        f=l.split(); i=int(f[1]); o=int(f[4][4:] or '0',16)
        parts=cur.split('-'); op=parts[0]; forms=parts[1]
        cd=bytes.fromhex(CDS[k][i]); w=[int.from_bytes(cd[k:k+32],'big') for k in (0,32,64)]
        if op in ('MULMOD','ADDMOD'):
            c=PR[idx[k]][1]; m=int.from_bytes(c[1:33],'big')
            fb,fa=parts[2][0],parts[2][1]
            bb=int(parts[3]) if fb=='A' else w[1]; aa=int(parts[4]) if fa=='A' else w[2]
            exp=spec(op,aa,bb,m)
        else:
            fv,ft=forms[0],forms[1]
            v=int(parts[2]) if fv=='A' else w[0]; t=int(parts[3]) if ft=='A' else w[1]
            exp=spec(op,t,v) if op not in ('SDIV','SMOD') else spec(op,t,v)
        n+=1
        if f[2]!='status=success' or o!=exp: bad+=1; 
        if bad and bad<4 and (f[2]!='status=success' or o!=exp): print('BAD',cur,i,hex(o),hex(exp))
print('checked',n,'against the specification, wrong',bad)
