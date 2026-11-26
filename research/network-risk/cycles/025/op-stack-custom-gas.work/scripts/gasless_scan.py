"""Scan recent X Layer blocks for zero-priced transactions and check whether their receipts hold PoolManager logs. Read-only."""
import json, sys, urllib.request, concurrent.futures as cf
RPC='https://rpc.xlayer.tech'; PM='0x360e68faccca8ca495c1b759fd9eee466db9fb32'
def rpc(body):
    r=urllib.request.Request(RPC,data=json.dumps(body).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r,timeout=90))
N=int(sys.argv[1]); out=sys.argv[2]
head=int(rpc({'jsonrpc':'2.0','id':1,'method':'eth_blockNumber','params':[]})['result'],16)
def blk(n):
    for _ in range(4):
        try: return rpc({'jsonrpc':'2.0','id':1,'method':'eth_getBlockByNumber','params':[hex(n),True]})['result']
        except Exception: pass
with cf.ThreadPoolExecutor(8) as ex: blocks=list(ex.map(blk,range(head-N+1,head+1)))
zero=[]
for b in blocks:
    if not b: continue
    for t in b['transactions']:
        gp=int(t.get('maxFeePerGas',t.get('gasPrice','0x1')),16)
        if gp==0 and t.get('type')!='0x7e': zero.append((int(b['number'],16),t['hash'],t['from'],t.get('to'),t['input'][:10],int(t['gas'],16)))
def rc(h):
    for _ in range(4):
        try: return rpc({'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[h]})['result']
        except Exception: pass
with cf.ThreadPoolExecutor(8) as ex: recs=list(ex.map(rc,[z[1] for z in zero]))
res=[]
for z,r in zip(zero,recs):
    pm=sum(1 for l in (r or {}).get('logs',[]) if l['address'].lower()==PM)
    res.append({'block':z[0],'hash':z[1],'from':z[2],'to':z[3],'sel':z[4],'gas':z[5],'status':(r or {}).get('status'),'gasUsed':(r or {}).get('gasUsed'),'pmLogs':pm})
from collections import Counter
summary={'range':[head-N+1,head],'zeroPriced':len(res),'byTo':Counter(x['to'] for x in res).most_common(10),'bySel':Counter(x['sel'] for x in res).most_common(10),'senders':len(set(x['from'] for x in res)),'withPMLogs':[x for x in res if x['pmLogs']]}
json.dump({'summary':summary,'txs':res},open(out,'w'),indent=1)
print(json.dumps(summary,indent=1)[:4000])
