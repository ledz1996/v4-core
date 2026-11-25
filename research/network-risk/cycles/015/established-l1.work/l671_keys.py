import json, sys, urllib.request, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
R='https://api.avax.network/ext/bc/C/rpc'
PM='0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
def rpc(m,p,url=R):
    req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(req,timeout=60))
MOD='0x'+keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
INIT='0x'+keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
txs=[x['tx'] for x in json.load(open('/home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work/raw/an3-43114.json'))['results'] if x.get('aside')=='pool key not found']
out={}
for t in txs:
    rc=rpc('eth_getTransactionReceipt',[t])['result']
    ids=set()
    for lg in rc['logs']:
        if lg['address'].lower()==PM and lg['topics'][0] in (MOD,INIT): ids.add(lg['topics'][1])
        if lg['address'].lower()==PM and lg['topics'][0]==INIT:
            out.setdefault('initInTx',{})[lg['topics'][1]]=t
    out[t]={'block':int(rc['blockNumber'],16),'pools':sorted(ids),'to':rc['to'],'status':rc['status']}
    print(t, out[t], flush=True)
json.dump(out,open('raw_l671_pools.json','w'),indent=1)
