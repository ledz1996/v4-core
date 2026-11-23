# Read-only: count Donate events of the deployed PoolManager in a recent block window on each network (eth_getLogs).
import json, sys, os, urllib.request, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../..'))
nets=json.load(open(os.path.join(ROOT,'research/network-risk/state/networks.json')))['networks']
T0='0x'+keccak(b'Donate(bytes32,address,uint256,uint256)').hex()
def rpc(url,method,params,t=20):
    req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=t) as r: return json.load(r)
out=[]
for n in nets:
    rec={'chainId':n['chainId'],'name':n['name'],'topic0':T0}
    try:
        head=int(rpc(n['rpc'],'eth_blockNumber',[])['result'],16); rec['head']=head
        for span in (100000,20000,5000,1000,400):
            try:
                r=rpc(n['rpc'],'eth_getLogs',[{'address':n['poolManager'],'topics':[T0],'fromBlock':hex(head-span),'toBlock':hex(head)}],40)
            except Exception as e:
                rec.setdefault('errors',[]).append('%d: %s'%(span,str(e)[:80])); continue
            if 'result' in r:
                logs=r['result']; rec['span']=span; rec['count']=len(logs)
                senders={}
                for l in logs:
                    s='0x'+l['topics'][2][-40:]; senders[s]=senders.get(s,0)+1
                rec['senders']=sorted(senders.items(),key=lambda x:-x[1])[:5]
                rec['sample']=[{'tx':l['transactionHash'],'block':int(l['blockNumber'],16),'pool':l['topics'][1],'data':l['data']} for l in logs[:3]]
                break
            rec.setdefault('errors',[]).append('%d: %s'%(span,json.dumps(r.get('error'))[:100]))
    except Exception as e:
        rec['fatal']=str(e)[:120]
    out.append(rec); print(json.dumps({k:rec.get(k) for k in ('chainId','name','head','span','count','senders','fatal')}))
    sys.stdout.flush()
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw/donate_logs.json'),'w'),indent=1)
