# Read-only eth_call helper. Usage: functions imported by dgf.py.
import json,sys,urllib.request
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
RPC='https://ethereum-rpc.publicnode.com'
def sel(sig): return keccak(sig.encode())[:4].hex()
def call(to,data,rpc=RPC,block='latest'):
    req={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':'0x'+data},block]}
    r=urllib.request.Request(rpc,json.dumps(req).encode(),{'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r,timeout=30)).get('result')
def raw(method,params,rpc=RPC):
    req={'jsonrpc':'2.0','id':1,'method':method,'params':params}
    r=urllib.request.Request(rpc,json.dumps(req).encode(),{'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r,timeout=30))
