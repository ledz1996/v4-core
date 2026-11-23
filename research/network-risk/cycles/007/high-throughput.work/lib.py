import json,urllib.request,ssl,sys,time
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
MON='https://rpc.monad.xyz'
MEGA='https://mainnet.megaeth.com/rpc'
PM={143:'0x188d586ddcf52439676ca21a244753fa19f9ea8e',4326:'0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'}
URL={143:MON,4326:MEGA}
def post(url,body,timeout=40):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=timeout,context=ctx) as r:
        return json.load(r)
def rpc(method,params,url,raw=False):
    for i in range(5):
        try:
            j=post(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
            if 'error' in j and ('rate' in json.dumps(j['error']).lower() or 'limit exceeded' in json.dumps(j['error']).lower()):
                time.sleep(1.5*(i+1)); continue
            break
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    else: raise Exception('rpc failed')
    if raw: return j
    if 'error' in j: raise Exception(json.dumps(j['error'])[:400])
    return j['result']
def batch(calls,url):
    body=[{'jsonrpc':'2.0','id':i,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    for i in range(5):
        try:
            j=post(url,body)
            if isinstance(j,list): break
            time.sleep(1.5*(i+1))
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    else: raise Exception('batch failed '+str(j)[:200])
    return sorted(j,key=lambda x:x['id'])
from keccak import keccak256
def sel(sig): return keccak256(sig.encode())[:4].hex()
def w(x): return (x if isinstance(x,int) else int(x,16)).to_bytes(32,'big').hex()
