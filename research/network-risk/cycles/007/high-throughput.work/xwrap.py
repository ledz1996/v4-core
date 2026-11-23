import gzip
from mc import *
chain=143; pm=PM[chain]
cur=json.load(gzip.open('../../004/theme-balance-reconcile.work/raw/currencies_143.json.gz'))['currencies']
addrs=[a for a in cur if int(a,16)!=0]
X=json.load(open('raw/xstocks_143.json')); xs={r['token']:r for r in X['rows']}
bn=hex(X['block'])
r=agg3(chain,[(a,sel('asset()')) for a in addrs],blk=bn,chunk=400)
wr=[(a,'0x'+b[12:32].hex()) for a,(ok,b) in zip(addrs,r) if ok and len(b)==32 and '0x'+b[12:32].hex() in xs]
print('wrappers whose asset() is an xStocks token:',len(wr))
calls=[]
for a,u in wr:
    calls+= [(a,sel('symbol()')),(a,sel('balanceOf(address)')+w(int(pm,16))),(a,sel('convertToAssets(uint256)')+w(10**18)),(a,sel('totalSupply()')),(a,sel('totalAssets()')),(u,sel('balanceOf(address)')+w(int(a,16)))]
rr=agg3(chain,calls,blk=bn,chunk=300)
rows=[]
for i,(a,u) in enumerate(wr):
    p=rr[i*6:(i+1)*6]
    g=lambda j:int.from_bytes(p[j][1][:32],'big') if p[j][0] and len(p[j][1])>=32 else None
    sym=p[0][1][64:64+int.from_bytes(p[0][1][32:64],'big')].decode(errors='replace') if p[0][0] else '?'
    rows.append(dict(wrapper=a,symbol=sym,underlying=u,usym=xs[u]['symbol'],pmBalance=g(1),assetsPerShare=g(2),totalSupply=g(3),totalAssets=g(4),underlyingHeld=g(5),mult=xs[u]['curMult'],pools=cur[a]))
json.dump(rows,open('raw/xwrap_143.json','w'),indent=0)
rows.sort(key=lambda r:-(r['pmBalance'] or 0))
for r in rows[:14]: print(r['symbol'],r['wrapper'],'pmBal %.2f'%((r['pmBalance'] or 0)/1e18),'assets/share',r['assetsPerShare'],'mult',r['mult'],'pools',r['pools'],'supply %.1f'%((r['totalSupply'] or 0)/1e18),'held %.1f'%((r['underlyingHeld'] or 0)/1e18))
print('wrappers with PM balance > 0:',sum(1 for r in rows if r['pmBalance']))
print('assetsPerShare differs from multiplier:',[(r['symbol'],r['assetsPerShare'],r['mult']) for r in rows if r['assetsPerShare']!=r['mult']][:10])
for r in rows:
    if 'SNDK' in r['symbol'] or r['mult']>1.2e18 or r['mult']<0.8e18: print('SPLIT TOKEN WRAPPER',r)
