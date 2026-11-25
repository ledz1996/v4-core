# Task 1 (L-912): does rpc.hyperliquid.xyz/evm honour historical block tags?
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
import urllib.request, ssl
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpcb(url, calls):
    body=[{'jsonrpc':'2.0','id':i,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    req=urllib.request.Request(url, json.dumps(body).encode(), {'content-type':'application/json','user-agent':'rpc-client'})
    try:
        r=json.loads(urllib.request.urlopen(req, timeout=60, context=CTX).read())
    except Exception as e:
        return {'error':repr(e)}
    if isinstance(r,dict): return {'error':r}
    r=sorted(r,key=lambda x:x['id'])
    return [x.get('result', {'error':x.get('error')}) for x in r]
def rpc1(url,m,p):
    out=rpcb(url,[('web3_clientVersion',[]),(m,p),('web3_clientVersion',[])])
    return out
OFF='https://rpc.hyperliquid.xyz/evm'; ARC='https://rpc.purroofgroup.com'
PM='0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
