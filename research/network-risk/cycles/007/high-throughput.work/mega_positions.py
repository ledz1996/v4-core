from mc import *
import pickle,collections,os
chain=4326; pm=PM[chain]
T0='0x'+keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
head=int(rpc('eth_blockNumber',[],MEGA),16)
if not os.path.exists('raw/mega_modliq_all.pkl'):
    logs=[]; step=100000; a=7009653
    while a<=head:
        b=min(head,a+step-1)
        r=rpc('eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(a),'toBlock':hex(b)}],MEGA,raw=True)
        if 'error' in r:
            step//=2; print('err',str(r['error'])[:100],'step',step); 
            if step<1000: raise SystemExit
            continue
        logs+=r['result']; a=b+1
    pickle.dump((head,logs),open('raw/mega_modliq_all.pkl','wb'))
head,logs=pickle.load(open('raw/mega_modliq_all.pkl','rb'))
print('logs',len(logs),'to block',head)
def s(x,bits=256):
    x=int(x,16); return x-(1<<bits) if x>>(bits-1) else x
pos=collections.OrderedDict()
for l in logs:
    d=l['data'][2:]; pid=l['topics'][1]; owner='0x'+l['topics'][2][-40:]
    tl=s(d[0:64]); tu=s(d[64:128]); ld=s(d[128:192]); salt=d[192:256]
    k=(pid,owner,tl,tu,salt); p=pos.setdefault(k,[0,0,int(l['blockNumber'],16)]); p[0]+=ld; p[1]+=1
live=[(k,v) for k,v in pos.items() if v[0]>0]
print('positions seen',len(pos),'with net liquidity above zero',len(live))
def i24(x): return (x & 0xffffff).to_bytes(3,'big')
def slots(pid,owner,tl,tu,salt):
    key=keccak256(bytes.fromhex(owner[2:])+i24(tl)+i24(tu)+bytes.fromhex(salt))
    state=int.from_bytes(keccak256(bytes.fromhex(pid[2:])+(6).to_bytes(32,'big')),'big')
    ps=int.from_bytes(keccak256(key+(state+6).to_bytes(32,'big')),'big')
    return state,ps
SV='0x726f84e1dfb8d375a365e0808282f40d52d3e4e8'
bn=hex(head)
calls=[]
for (pid,owner,tl,tu,salt),v in live:
    st,ps=slots(pid,owner,tl,tu,salt)
    calls.append((pm,sel('extsload(bytes32,uint256)')+w(ps)+w(3)))
    calls.append((SV,sel('getFeeGrowthInside(bytes32,int24,int24)')+pid[2:]+w(tl%(1<<256))+w(tu%(1<<256))))
r=agg3(chain,calls,blk=bn,chunk=200)
rows=[]
for i,((pid,owner,tl,tu,salt),v) in enumerate(live):
    ok1,b1=r[2*i]; ok2,b2=r[2*i+1]
    liq=int.from_bytes(b1[64:96],'big')&((1<<128)-1) if ok1 and len(b1)>=160 else None
    f0=int.from_bytes(b1[96:128],'big') if ok1 and len(b1)>=160 else None
    f1=int.from_bytes(b1[128:160],'big') if ok1 and len(b1)>=160 else None
    c0=int.from_bytes(b2[0:32],'big') if ok2 and len(b2)>=64 else None
    c1=int.from_bytes(b2[32:64],'big') if ok2 and len(b2)>=64 else None
    st,ps=slots(pid,owner,tl,tu,salt)
    rows.append(dict(pool=pid,owner=owner,tl=tl,tu=tu,salt=salt,netLogs=v[0],liq=liq,f0=f0,f1=f1,c0=c0,c1=c1,slot=hex(ps),events=v[1],first=v[2]))
pickle.dump(rows,open('raw/mega_positions.pkl','wb'))
chk=sum(1 for x in rows if x['liq']==x['netLogs']); print('storage liquidity equals log sum for',chk,'of',len(rows))
z0=[x for x in rows if x['liq'] and x['f0']==0 and x['c0']]; z1=[x for x in rows if x['liq'] and x['f1']==0 and x['c1']]
both=[x for x in rows if x['liq'] and ((x['f0']==0 and x['c0']) or (x['f1']==0 and x['c1']))]
nonz=[x for x in rows if x['liq'] and x['f0']!=0 and x['f1']!=0]
zero_stored=[x for x in rows if x['liq'] and x['f0']==0 and x['f1']==0]
print('live positions',sum(1 for x in rows if x['liq']),'| stored fee growth zero for both currencies',len(zero_stored),'| exit needs a zero to nonzero write: currency0',len(z0),'currency1',len(z1),'either',len(both),'| both stored values nonzero',len(nonz))
print('owners of positions that need such a write',collections.Counter(x['owner'] for x in both).most_common(5))
print('pools',len(set(x['pool'] for x in rows)),'pools with such positions',len(set(x['pool'] for x in both)))
