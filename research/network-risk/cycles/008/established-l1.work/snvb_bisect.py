# Lead L-464: find every block where the PoolManager's sNVB balance changed other than by a rebase,
# without eth_getLogs. ratio = balanceOf(PM) * 1e18 // index is constant across rebases.
import sys,json,time
sys.path.insert(0,'.')
from rpc import rpc
U='https://bsc.api.pocket.network'
PM='28e2ea090877bf75740558f6bfb36a5ffee9e9df'
TOK='0x6d6c16a3cbd318f3000e33cfd27662cf00f7e7c1'
cache={}
calls=0
def state(b):
    global calls
    if b in cache: return cache[b]
    for attempt in range(4):
        r=rpc(U,'eth_call',[{"to":TOK,"data":'0x70a08231'+'0'*24+PM},hex(b)])
        s=rpc(U,'eth_call',[{"to":TOK,"data":'0x2986c0e5'},hex(b)])
        calls+=2
        try:
            bal=int(r['result'],16); idx=int(s['result'],16)
            cache[b]=(bal,idx); return cache[b]
        except Exception:
            time.sleep(2)
    raise RuntimeError('rpc failed at %d: %s %s'%(b,r,s))
def same(a,b):
    (ba,ia),(bb,ib)=state(a),state(b)
    # gons unchanged <=> ba/ia == bb/ib up to rounding of one base unit on each side
    return abs(ba*ib-bb*ia) <= ia+ib
changes=[]
def walk(a,b):
    if calls>9000: raise RuntimeError('budget')
    if same(a,b): return
    if b-a==1:
        changes.append((b,state(a),state(b))); print('change',b,state(a),state(b),flush=True); return
    m=(a+b)//2
    walk(a,m); walk(m,b)
start=49283729
head=int(rpc(U,'eth_blockNumber',[])['result'],16)-20
grid=[start+i*(head-start)//400 for i in range(401)]
try:
    for a,b in zip(grid,grid[1:]):
        walk(a,b)
except Exception as e:
    print('stopped',e)
json.dump({'head':head,'calls':calls,'changes':changes},open('raw/snvb_changes.json','w'))
print('done',len(changes),'calls',calls)
