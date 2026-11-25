# pc -> file:line for the build of this checkout, from solc's deployed source map
import json,os
R='/home/user/v4-core'
b=json.load(open(os.path.join(os.path.dirname(__file__),'build/solc/PoolManager.srcmap.json')))
code=bytes.fromhex(b['runtime']); ids=b['sourceIds']
pcs=[];i=0
while i<len(code):
    pcs.append(i); o=code[i]; i+=1+(o-0x5f if 0x60<=o<=0x7f else 0)
ent=[];s=l=f=-1;j='-'
for e in b['sourceMap'].split(';'):
    p=e.split(':')
    if len(p)>0 and p[0]!='': s=int(p[0])
    if len(p)>1 and p[1]!='': l=int(p[1])
    if len(p)>2 and p[2]!='': f=int(p[2])
    ent.append((s,l,f))
cache={}
def line_of(file,off):
    if file not in cache:
        try: cache[file]=open(os.path.join(R,file),'rb').read()
        except Exception: cache[file]=None
    t=cache[file]
    return None if t is None else t[:off].count(b'\n')+1
M={}
for k,pc in enumerate(pcs):
    if k>=len(ent): break
    s,l,f=ent[k]
    fn=ids.get(str(f))
    if fn is None or s<0: M[pc]=None; continue
    a=line_of(fn,s); z=line_of(fn,s+l)
    M[pc]=(fn,a,z)
def where(pc):
    r=M.get(pc)
    return f'{r[0]}:{r[1]}' + (f'-{r[2]}' if r and r[2]!=r[1] else '') if r else '?'
if __name__=='__main__':
    import sys
    for a in sys.argv[1:]: print(a, where(int(a)))
def near(pc,win=80):
    """the nearest pc with a source range narrower than the whole contract"""
    best=None
    for d in range(0,win):
        for q in (pc-d,pc+d):
            r=M.get(q)
            if r and not (r[0]=='src/PoolManager.sol' and r[1]==80): return f'{r[0]}:{r[1]}'+(f'-{r[2]}' if r[2]!=r[1] else '')+f' (pc {q})'
    return '?'
