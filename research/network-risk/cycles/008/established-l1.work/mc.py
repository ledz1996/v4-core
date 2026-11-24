# Measurement helper: Multicall3 runtime code placed at the PoolManager address by state override (eth_call only).
import sys,json
sys.path.insert(0,'.')
from rpc import rpc
MC3='0xcA11bde05977b3631167028862bE2a173976CA11'
def pad(x): return x.lower().replace('0x','').zfill(64)
def u(n): return hex(n)[2:].zfill(64)
def enc_agg3(calls):
    # calls: list of (target, allowFailure, calldata hex)
    head=''; tail=''; n=len(calls)
    offs=[]; bodies=[]
    for t,af,cd in calls:
        cd=cd.replace('0x','')
        b=pad(t)+u(1 if af else 0)+u(96)+u(len(cd)//2)+cd+'0'*((64-len(cd)%64)%64)
        bodies.append(b)
    cur=32*n
    for b in bodies:
        offs.append(u(cur)); cur+=len(b)//2
    return '0x82ad56cb'+u(32)+u(n)+''.join(offs)+''.join(bodies)
def dec_agg3(res):
    h=res[2:]
    w=lambda i: int(h[i*64:(i+1)*64],16)
    base=1  # words: [0]=0x20, [1]=n
    n=w(1); out=[]
    for i in range(n):
        off=w(2+i)  # relative to start of array data (after length)
        p=(2*32+off)//32
        succ=w(p); doff=w(p+1); 
        ln=w(p+doff//32); data=h[(p+doff//32+1)*64:(p+doff//32+1)*64+ln*2]
        out.append((bool(succ),data))
    return out
_code={}
def mc_code(url):
    if url not in _code:
        _code[url]=rpc(url,'eth_getCode',[MC3,'latest'])['result']
    return _code[url]
def as_pm(url,pm,calls,block='latest',sender='0x00000000000000000000000000000000000a11ce',extra_override=None):
    ov={pm:{'code':mc_code(url)}}
    if extra_override: ov.update(extra_override)
    r=rpc(url,'eth_call',[{'from':sender,'to':pm,'data':enc_agg3(calls)},block,ov])
    if 'result' not in r: return r
    return dec_agg3(r['result'])
