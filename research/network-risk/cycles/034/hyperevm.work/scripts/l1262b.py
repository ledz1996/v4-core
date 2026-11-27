"""Second pass of L-1262: compare official and archive receipts per transaction hash, after removing
receipts that only the archive serves, and classify those extra receipts by sender and gas price."""
import json,urllib.request,sys,concurrent.futures as cf
def rpc(u,m,p):
  for i in range(4):
    try:
      r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"network-review-client"})
      return json.loads(urllib.request.urlopen(r,timeout=90).read())
    except Exception as e:
      import time; time.sleep(2+i); err=str(e)
  return {"error":err}
d=json.load(open(sys.argv[1]))
def go(b):
  n=b['block']
  a=rpc("https://rpc.hyperliquid.xyz/evm","eth_getBlockReceipts",[hex(n)]).get('result') or []
  c=rpc("https://rpc.hyperlend.finance/archive","eth_getBlockReceipts",[hex(n)]).get('result') or []
  ca={x['transactionHash']:x for x in c}; sa={x['transactionHash'] for x in a}
  eq=0; ne=[]
  for x in a:
    y=ca.get(x['transactionHash'])
    if y and x['status']==y['status'] and x['gasUsed']==y['gasUsed'] and [(l['address'],l['topics'],l['data']) for l in x['logs']]==[(l['address'],l['topics'],l['data']) for l in y['logs']]: eq+=1
    else: ne.append(x['transactionHash'])
  extra=[]
  for h,y in ca.items():
    if h not in sa:
      extra.append({"tx":h,"from":y['from'],"to":y.get('to'),"gasPrice":y.get('effectiveGasPrice'),"gasUsed":y['gasUsed'],"nlogs":len(y['logs']),"pmlog":any(l['address'].lower()=="0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f" for l in y['logs'])})
  return {"block":n,"official":len(a),"archive":len(c),"equal":eq,"notEqual":ne,"extra":extra}
with cf.ThreadPoolExecutor(6) as ex: out=list(ex.map(go,d['blocks']))
from collections import Counter
s={"blocks":len(out),"officialReceipts":sum(o['official'] for o in out),"equal":sum(o['equal'] for o in out),"notEqual":sum(len(o['notEqual']) for o in out),
   "extra":sum(len(o['extra']) for o in out),"extraSenders":Counter(e['from'] for o in out for e in o['extra']).most_common(20),
   "extraGasPrice":Counter(e['gasPrice'] for o in out for e in o['extra']).most_common(5),"extraWithPmLog":sum(e['pmlog'] for o in out for e in o['extra']),
   "extraTo":Counter(e['to'] for o in out for e in o['extra']).most_common(5)}
print(json.dumps(s,indent=1))
json.dump({"summary":s,"blocks":out},open(sys.argv[2],"w"),indent=1)
