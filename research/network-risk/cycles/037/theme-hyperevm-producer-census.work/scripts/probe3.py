import json,sys,urllib.request
url,bn=sys.argv[1],int(sys.argv[2])
TR=open(__file__.replace('probe3.py','shape_tracer.js')).read()
def rpc(m,p):
  return json.loads(urllib.request.urlopen(urllib.request.Request(url,json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),{'content-type':'application/json','user-agent':'census-readonly'}),timeout=180).read())
r=rpc("debug_traceBlockByNumber",[hex(bn),{"tracer":TR,"timeout":"120s"}])
for t in r['result'][:3]:
  for k,v in t['result']['m'].items():
    if k.startswith('85:'):
      op,cl,ad,pc=k.split(':'); 
      prev=rpc("eth_getStorageAt",[ad,'0x'+v[1],hex(bn-1)])['result']
      print(k,v,'prevblock',prev)
