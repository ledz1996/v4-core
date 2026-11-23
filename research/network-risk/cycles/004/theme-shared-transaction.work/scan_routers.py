# For every downloaded router source: list each call of sync, settle, settleFor, exttload and getSynced* outside interface files,
# and hash the body of DeltaResolver._settle so that deployments can be grouped.
import os, re, json, hashlib, sys
from lib import *
res=json.load(open('routers_fetched.json'))
pat=re.compile(r'(\.sync\(|\.settle\(|\.settle\{|settleFor|exttload\(|getSyncedCurrency|getSyncedReserves)')
groups={}
for cid,name,k,a,r in res:
    if not isinstance(r,list): print(cid,name,k,a,'NO SOURCE'); continue
    d=r[0]; hits=[]; dr=None
    for fn in sorted(os.listdir(d)):
        if 'interfaces__' in fn or fn.endswith('.json') or '__test__' in fn or 'forge-std' in fn: continue
        t=open(os.path.join(d,fn)).read()
        if fn.endswith('DeltaResolver.sol'):
            m=re.search(r'function _settle\(.*?\n    \}',t,re.S); dr=hashlib.sha256(re.sub(r'\s+',' ',m.group(0)).encode()).hexdigest()[:10] if m else 'nomatch'
        for i,l in enumerate(t.split('\n'),1):
            if pat.search(l) and not l.strip().startswith(('//','///','*')): hits.append('%s:%d %s'%(fn.split('__')[-1],i,l.strip()[:110]))
    key=(dr,tuple(hits)); groups.setdefault(key,[]).append('%d %s %s %s'%(cid,name,k,a))
for i,((dr,hits),mem) in enumerate(groups.items()):
    print('GROUP',i,'DeltaResolver._settle hash',dr,'members',len(mem))
    for m in mem: print('   ',m)
    for h in hits: print('      ',h)
