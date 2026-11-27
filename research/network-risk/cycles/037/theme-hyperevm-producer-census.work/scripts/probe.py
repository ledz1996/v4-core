import json,sys,urllib.request,time
url,bn=sys.argv[1],int(sys.argv[2])
TR=open(__file__.replace('probe.py','shape_tracer.js')).read()
req={"jsonrpc":"2.0","id":1,"method":"debug_traceBlockByNumber","params":[hex(bn),{"tracer":TR,"timeout":"120s"}]}
t=time.time()
r=urllib.request.urlopen(urllib.request.Request(url,json.dumps(req).encode(),{'content-type':'application/json','user-agent':'census-readonly'}),timeout=180).read()
print(time.time()-t, len(r)); print(r[:1500])
