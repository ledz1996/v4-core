"""Scan MegaETH block headers (batched eth_getHeaderByNumber, read-only) for gasUsed and tx counts. Usage: gasscan.py <from> <to> <out.json>"""
import json,sys,urllib.request,time
R='https://mainnet.megaeth.com/rpc'
fr,to=int(sys.argv[1]),int(sys.argv[2]); out={}
b=fr
while b<=to:
  n=min(50,to-b+1); req=[{"jsonrpc":"2.0","id":i,"method":"eth_getHeaderByNumber","params":[hex(b+i)]} for i in range(n)]
  for k in range(5):
    try:
      r=urllib.request.Request(R,data=json.dumps(req).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
      x=json.load(urllib.request.urlopen(r,timeout=120)); break
    except Exception as e: print('retry',b,e,flush=True); time.sleep(10)
  for h in x:
    if 'result' in h and h['result']: out[int(h['result']['number'],16)]=int(h['result']['gasUsed'],16)
  b+=n; time.sleep(1)
json.dump(out,open(sys.argv[3],'w'))
v=sorted(out.items(),key=lambda t:-t[1])[:20]; print(len(out), v)
