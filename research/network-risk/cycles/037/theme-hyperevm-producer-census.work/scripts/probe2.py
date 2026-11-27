import json,sys,urllib.request,time,collections
url,bn=sys.argv[1],int(sys.argv[2])
TR=open(__file__.replace('probe2.py','shape_tracer.js')).read()
req={"jsonrpc":"2.0","id":1,"method":"debug_traceBlockByNumber","params":[hex(bn),{"tracer":TR,"timeout":"120s"}]}
r=json.loads(urllib.request.urlopen(urllib.request.Request(url,json.dumps(req).encode(),{'content-type':'application/json','user-agent':'census-readonly'}),timeout=180).read())
c=collections.Counter()
for t in r['result']:
  if 'result' not in t: print('ERR',str(t)[:300]); continue
  for k,v in t['result']['m'].items():
    op,cl=k.split(':')[:2]; c[(int(op),int(cl))]+=v[0]
print(len(r['result']), sorted(c.items()))
