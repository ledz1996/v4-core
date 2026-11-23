from lib import *
from asm import asm
import time
d=json.load(open('raw/pools.json')); cur=[c for c in d['currencies'] if int(c,16)!=0]
blk=hex(int(rpc('eth_blockNumber',[],url=ARCH),16)-5)
def bt(calls,u=ARCH):
    out=[]
    for i in range(0,len(calls),50):
        out+=batch(calls[i:i+50],url=u)
    return out
pm64=PM[2:].lower().rjust(64,'0')
res=bt([('eth_call',[{'to':c,'data':'0x70a08231'+pm64},blk]) for c in cur])
bal={}
for c,r in zip(cur,res):
    v=r.get('result'); bal[c]=int(v,16) if v and len(v)>=66 else None
nz={c:b for c,b in bal.items() if b}
print('erc20 currencies',len(cur),'nonzero',len(nz),'no answer',[c for c,b in bal.items() if b is None])
groups={}
for c,b in nz.items(): groups.setdefault(b,[]).append(c)
eq={b:g for b,g in groups.items() if len(g)>1}
print('groups of equal nonzero balance:',len(eq))
# measuring stub at PM: for each member of group: call token.transfer(dead,1) then read balances of all members
DEAD='0x00000000000000000000000000000000000dead1'
def stub(tokens,target):
    # transfer 1 unit of target; then return balanceOf(PM) for each token
    t=[0xa9059cbb,224,'SHL',0,'MSTORE',int(DEAD,16),4,'MSTORE',1,36,'MSTORE',
       0,0,68,0,0,int(target,16),'GAS','CALL',0x400,'MSTORE']
    for i,tk in enumerate(tokens):
        t+=[0x70a08231,224,'SHL',0,'MSTORE','ADDRESS',4,'MSTORE',32,0x420+32*i,36,0,int(tk,16),'GAS','STATICCALL','POP']
    t+=[32*(len(tokens)+1),0x400,'RETURN']
    return asm(t)
out=[]
for b,g in eq.items():
    info=[]
    for c in g:
        nm=rpc('eth_call',[{'to':c,'data':'0x95d89b41'},blk],url=ARCH,raw=True).get('result','0x')
        try: s=bytes.fromhex(nm[2:])[64:].rstrip(b'\0').decode(errors='replace')[:20]
        except: s='?'
        info.append(s)
    print('balance',b,'members',list(zip(g,info)))
    for c in g:
        r=rpc('eth_call',[{'from':'0xe0a0000000000000000000000000000000000e0a','to':PM,'data':'0x','gas':hex(3000000)},blk,{PM:{'code':stub(g,c)}}],url=ARCH,raw=True)
        if 'error' in r: print('   transfer of',c,'ERR',r['error']); out.append((b,c,'err')); continue
        bb=bytes.fromhex(r['result'][2:]); ok=int.from_bytes(bb[:32],'big'); after=[int.from_bytes(bb[32+32*i:64+32*i],'big') for i in range(len(g))]
        moved=[g[i] for i in range(len(g)) if after[i]!=b]
        print('   transfer 1 unit of',c,'ok',ok,'balances changed at',moved,[after[i]-b for i in range(len(g))])
        out.append((b,c,ok,[after[i]-b for i in range(len(g))]))
json.dump({'block':blk,'balances':{c:str(b) for c,b in bal.items()},'groups':{str(b):g for b,g in eq.items()},'tests':out},open('raw/equalbal.json','w'))
