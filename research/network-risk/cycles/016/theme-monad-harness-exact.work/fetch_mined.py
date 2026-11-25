# Fetch, for each mined Monad PoolManager transaction listed by cycle 13, the receipt, the call tree
# (callTracer with logs), the prestate (prestateTracer) and the block header. Read-only JSON-RPC.
import json,os,sys,time,urllib.request,concurrent.futures as cf,itertools
URLS=['https://rpc1.monad.xyz','https://rpc-mainnet.monadinfra.com','https://rpc.monad.xyz']
c=itertools.count()
def rpc(m,p,tries=8):
    last=None
    for k in range(tries):
        u=URLS[next(c)%len(URLS)]
        try:
            req=urllib.request.Request(u,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
            r=json.loads(urllib.request.urlopen(req,timeout=90).read())
            if 'error' in r: raise Exception(str(r['error']))
            return r['result']
        except Exception as e:
            last=e; time.sleep(1+k)
    raise last
W='../../013/theme-mined-branches.work/raw/'
txs=[]
for f in ['pm-143.jsonl','old/rerun-143.jsonl']:
    for l in open(W+f):
        r=json.loads(l)
        if r['tx'] not in txs: txs.append(r['tx'])
blocks={}
def one(h):
    p=f'dl/mined/{h}.json'
    if os.path.exists(p) and 'code' not in json.load(open(p))['prestate'].get('0x188d586ddcf52439676ca21a244753fa19f9ea8e',{}) and len(json.load(open(p))['prestate'])<=1: return 'cached'
    rc=rpc('eth_getTransactionReceipt',[h]); tx=rpc('eth_getTransactionByHash',[h])
    ct=rpc('debug_traceTransaction',[h,{'tracer':'callTracer','tracerConfig':{'withLog':True}}])
    pre=rpc('debug_traceTransaction',[h,{'tracer':'prestateTracer'}])
    PM='0x188d586ddcf52439676ca21a244753fa19f9ea8e'
    pre={a:{k:v for k,v in e.items() if k!='code'} for a,e in pre.items() if a.lower()==PM}
    rc['logs']=[l for l in rc['logs'] if l['address'].lower()==PM]
    blk=rpc('eth_getBlockByNumber',[rc['blockNumber'],False])
    hdr={k:blk.get(k) for k in ('number','timestamp','baseFeePerGas','miner','gasLimit','mixHash','prevRandao')}
    json.dump({'tx':h,'receipt':rc,'txobj':tx,'calltree':ct,'prestate':pre,'header':hdr},open(p,'w'))
    return 'ok'
n=int(sys.argv[1]) if len(sys.argv)>1 else len(txs)
with cf.ThreadPoolExecutor(8) as ex:
    res=list(ex.map(lambda h:(lambda:one(h))() if True else None, txs[:n]))
print(len(txs), n, {r:res.count(r) for r in set(res)})
