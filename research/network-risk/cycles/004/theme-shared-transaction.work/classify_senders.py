# For the most frequent swap senders per network (canonical Uniswap routers excluded): code length, proxy target,
# which PoolManager selectors the code holds (plain or as a shifted constant), and the verified name on Sourcify.
import json, sys, concurrent.futures as cf, requests
from lib import *
SIGS=['sync(address)','settle()','settleFor(address)','exttload(bytes32)','unlock(bytes)','unlockCallback(bytes)','take(address,address,uint256)','burn(address,uint256,uint256)','mint(address,uint256,uint256)']
SEL={s.split('(')[0]:int(sel(s),16) for s in SIGS}
def has(code,v):
    for k in range(0,4):
        if v%(1<<k)==0 and bytes.fromhex('%08x'%(v>>k)) in code: return True
    return False
def impl_of(u,a,code):
    if len(code)==45 and code[:10].hex()=='363d3d373d3d3d363d73': return '0x'+code[10:30].hex()
    if len(code)==23 and code[:3].hex()=='ef0100': return '0x'+code[3:].hex()
    for slot in ('0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc',):
        try:
            v=rpc(u,'eth_getStorageAt',[a,slot,'latest'])
            if int(v,16): return '0x'+v[-40:]
        except Exception: pass
    return None
def srcname(cid,a):
    try:
        r=requests.get('https://sourcify.dev/server/v2/contract/%d/%s?fields=compilation'%(cid,a),timeout=30,headers={'user-agent':'curl/8'})
        if r.status_code==200: return (r.json().get('compilation') or {}).get('name')
    except Exception as e: return 'ERR'
    return None
def one(job):
    cid,u,a,cnt,tx,canon=job
    try:
        code=bytes.fromhex(rpc(u,'eth_getCode',[a,'latest'])[2:]); im=impl_of(u,a,code) if len(code)<3000 else None; c2=code
        if im: c2=bytes.fromhex(rpc(u,'eth_getCode',[im,'latest'])[2:])
        return dict(chainId=cid,addr=a,count=cnt,tx=tx,len=len(code),impl=im,implLen=len(c2) if im else None,sels={k:has(c2,v) for k,v in SEL.items()},name=srcname(cid,im or a),canon=canon)
    except Exception as e: return dict(chainId=cid,addr=a,count=cnt,tx=tx,err=str(e)[:150],canon=canon)
if __name__=='__main__':
    S=json.load(open('senders.json')); jobs=[]; TOP=int(sys.argv[1]) if sys.argv[1:] else 10
    for r in S:
        n=net(r['chainId']); canon={v.lower():k.replace(' ',' ') for k,v in n['contracts'].items()}
        for a,cnt in sorted(r['senders'].items(),key=lambda x:-x[1])[:TOP]:
            jobs.append((r['chainId'],n['rpc'],a,cnt,r['sample'][a],canon.get(a)))
    with cf.ThreadPoolExecutor(12) as ex: res=list(ex.map(one,jobs))
    json.dump(res,open('senders_classified.json','w'),indent=1)
    tot={r['chainId']:r['logs'] for r in S}
    for x in res:
        if 'err' in x: print(x); continue
        s=x['sels']; fl=''.join(c if s[k] else '-' for k,c in (('sync','Y'),('settle','S'),('settleFor','F'),('exttload','X'),('unlock','U'),('unlockCallback','C'),('take','T'),('burn','B'),('mint','M')))
        print('%8d %s %5.1f%% len %5d %s %s %s %s'%(x['chainId'],x['addr'],100*x['count']/tot[x['chainId']],x['len'],fl,('impl '+x['impl']) if x['impl'] else '',x['name'] or '',('['+x['canon']+']') if x['canon'] else ''))
