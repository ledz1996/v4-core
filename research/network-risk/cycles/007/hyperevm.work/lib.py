import json,urllib.request,ssl,sys,time
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
OFF='https://rpc.hyperliquid.xyz/evm'
ARCH='https://rpc.purroofgroup.com'
PM='0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
def post(url,body,timeout=40):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=timeout,context=ctx) as r:
        return json.load(r)
def rpc(method,params,url=OFF,raw=False):
    for i in range(4):
        try:
            j=post(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
            break
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    else: raise err
    if raw: return j
    if 'error' in j: raise Exception(json.dumps(j['error'])[:400])
    return j['result']
def batch(calls,url=OFF):
    body=[{'jsonrpc':'2.0','id':i,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    for i in range(4):
        try:
            j=post(url,body); break
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    else: raise err
    if isinstance(j,dict): raise Exception('batch error '+json.dumps(j)[:200])
    j=sorted(j,key=lambda x:x['id'])
    return j
def info(body):
    return post('https://api.hyperliquid.xyz/info',body)
