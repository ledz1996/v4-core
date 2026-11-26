"""Read-only census of gas price 0 (system) transactions on HyperEVM since the MRB fork.
Seed 2027027, 2,000 blocks uniform in [50988232, head]. Replica: rpc.purroofgroup.com (nanoreth).
Official endpoint eth_getSystemTxsByBlockNumber for every 10th sampled block."""
import json, random, sys, time, urllib.request, concurrent.futures as cf
REP='https://rpc.purroofgroup.com'; OFF='https://rpc.hyperliquid.xyz/evm'
PM='0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
def rpc(url, method, params, tries=6):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    for k in range(tries):
        try:
            req=urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'rpc-client'})
            r=json.loads(urllib.request.urlopen(req,timeout=40).read())
            if 'error' in r: raise Exception(str(r['error']))
            return r['result']
        except Exception as e:
            err=str(e); time.sleep(2*(k+1))
    raise Exception(err)
out=sys.argv[1]
head=int(rpc(REP,'eth_blockNumber',[]),16)
rec={'seed':2027027,'from':50988232,'head':head,'clientBefore':{u:rpc(u,'web3_clientVersion',[]) for u in (REP,OFF)}}
random.seed(2027027); blocks=sorted(random.sample(range(50988232,head+1),2000))
def one(b):
    blk=rpc(REP,'eth_getBlockByNumber',[hex(b),True])
    sys_=[]
    for t in blk['transactions']:
        if int(t.get('gasPrice','0x1'),16)==0:
            s=int(t['s'],16)
            dec='0x2222222222222222222222222222222222222222' if s==1 else ('0x'+(s & ((1<<160)-1)).to_bytes(20,'big').hex())
            sys_.append({'h':t['hash'],'type':t['type'],'from':t['from'].lower(),'sDecoded':dec,'to':(t['to'] or '').lower(),'sel':t['input'][:10],'arg0':t['input'][10:74],'value':t['value']})
    return b,len(blk['transactions']),sys_
res={}
with cf.ThreadPoolExecutor(6) as ex:
    for b,n,s in ex.map(one,blocks): res[b]={'n':n,'sys':s}
rec['blocks']=res
offcmp={}
for b in blocks[::10]:
    try:
        o=rpc(OFF,'eth_getSystemTxsByBlockNumber',[hex(b)])
        offcmp[b]=[(x.get('from','').lower(),(x.get('to') or '').lower(),x.get('input','')[:10]) for x in o]
    except Exception as e: offcmp[b]=str(e)[:200]
    time.sleep(0.3)
rec['official']=offcmp
rec['clientAfter']={u:rpc(u,'web3_clientVersion',[]) for u in (REP,OFF)}
json.dump(rec,open(out,'w'),indent=0)
