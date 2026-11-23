# Group the runtime code of every Universal Router and PositionManager by a hash taken after zeroing PUSH20..PUSH32 operands
# (immutables are PUSH32 operands). A deployment without verified source that falls in a group with a verified one runs the same code.
import json, hashlib, concurrent.futures as cf
from lib import *
ver={ (r[0],r[3].lower()): isinstance(r[4],list) for r in json.load(open('routers_fetched.json'))}
jobs=[]
for n in NETS:
    for k,v in n['contracts'].items():
        kk=k.replace(' ',' ')
        if kk.startswith('Universal Router') or kk=='PositionManager': jobs.append((n['chainId'],n['name'],kk,v,n['rpc']))
def mask(code):
    b=bytearray(code); i=0
    while i<len(b):
        op=b[i]
        if 0x60<=op<=0x7f:
            n=op-0x5f
            if n>=20:
                for j in range(i+1,min(i+1+n,len(b))): b[j]=0
            i+=n
        i+=1
    return bytes(b)
SEL={s:sel(s) for s in ['sync(address)','settle()','settleFor(address)','exttload(bytes32)','exttload(bytes32[])','unlock(bytes)','take(address,address,uint256)']}
def f(j):
    cid,name,k,a,u=j
    try:
        c=bytes.fromhex(rpc(u,'eth_getCode',[a,'latest'])[2:])
    except Exception as e: return (cid,name,k,a,'ERR '+repr(e)[:100])
    return (cid,name,k,a,len(c),hashlib.sha256(mask(c)).hexdigest()[:12],{s:(bytes.fromhex(h) in c) for s,h in SEL.items()})
if __name__=='__main__':
    with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(f,jobs))
    json.dump(res,open('code_groups.json','w'),indent=1)
    g={}
    for r in res:
        if isinstance(r[4],str): print(r); continue
        g.setdefault((r[4],r[5]),[]).append(r)
    for (ln,h),mem in sorted(g.items(),key=lambda x:-len(x[1])):
        print('len',ln,'masked',h,'n',len(mem),'verified in group:',sum(ver[(m[0],m[3].lower())] for m in mem), mem[0][6])
        for m in mem: print('    %s %s %s %s %s'%(m[0],m[1],m[2],m[3],'verified' if ver[(m[0],m[3].lower())] else 'UNVERIFIED'))
