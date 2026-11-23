import gzip,pickle
from mc import *
chain=143; pm=PM[chain]
cur=json.load(gzip.open('../../004/theme-balance-reconcile.work/raw/currencies_143.json.gz'))['currencies']
addrs=[a for a in cur if int(a,16)!=0]
bn=rpc('eth_blockNumber',[],URL[chain]); blk=rpc('eth_getBlockByNumber',[bn,False],URL[chain]); now=int(blk['timestamp'],16)
print('block',int(bn,16),'timestamp',now,'currencies',len(addrs))
r=agg3(chain,[(a,sel('getCurrentMultiplier()')) for a in addrs],blk=bn,gas=None,chunk=400)
xs=[a for a,(ok,b) in zip(addrs,r) if ok and len(b)==96]
print('tokens answering getCurrentMultiplier with three words:',len(xs))
fields=['symbol()','newMultiplier()','newMultiplierActivationTime()','lastMultiplier()','totalSupply()','multiplierUpdatesLength()']
rows=[]
calls=[]
for a in xs:
    for f in fields: calls.append((a,sel(f)))
    calls.append((a,sel('balanceOf(address)')+w(int(pm,16))))
    calls.append((a,sel('sharesOf(address)')+w(int(pm,16))))
    calls.append((a,sel('getCurrentMultiplier()')))
rr=agg3(chain,calls,blk=bn,chunk=300)
k=len(fields)+3
out=[]
for i,a in enumerate(xs):
    part=rr[i*k:(i+1)*k]
    def u(j,word=0):
        ok,b=part[j]; return int.from_bytes(b[32*word:32*word+32],'big') if ok and len(b)>=32*word+32 else None
    ok,b=part[0]; sym=b[64:64+int.from_bytes(b[32:64],'big')].decode(errors='replace') if ok and len(b)>=64 else '?'
    row=dict(token=a,symbol=sym,pools=cur[a],newMultiplier=u(1),activation=u(2),lastMultiplier=u(3),totalSupply=u(4),updates=u(5),balance=u(6),shares=u(7),curMult=u(8),periods=u(8,1))
    out.append(row)
json.dump(dict(block=int(bn,16),timestamp=now,rows=out),open('raw/xstocks_143.json','w'),indent=0)
pend=[r for r in out if r['activation'] and r['activation']>now]
print('pending multiplier changes (activation above block time):',len(pend))
for r in pend: print('  PENDING',r)
out.sort(key=lambda r:-(r['balance'] or 0))
for r in out[:60]: print(r['symbol'],r['token'],'pools',r['pools'],'bal',r['balance'],'shares',r['shares'],'mult',r['curMult'],'new',r['newMultiplier'],'act',r['activation'],'upd',r['updates'])
print('multiplier != 1e18 and not near:',[ (r['symbol'],r['curMult']) for r in out if r['curMult'] and (r['curMult']>1.2e18 or r['curMult']<0.8e18)])
