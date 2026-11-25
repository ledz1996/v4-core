"""Estimate per-transaction state growth of MegaETH blocks from debug_traceBlockByNumber with prestateTracer in diffMode
(read-only): new storage slots (absent or zero before, nonzero after) plus new accounts (absent or empty before).
Usage: growth.py <out.json> <block> [<block> ...]"""
import json,sys,urllib.request,time
R='https://mainnet.megaeth.com/rpc'
def rpc(m,p):
  r=urllib.request.Request(R,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
  return json.load(urllib.request.urlopen(r,timeout=600))
def z(v): return v is None or int(v,16)==0
out={}
for b in map(int,sys.argv[2:]):
  blk=rpc('eth_getBlockByNumber',[hex(b),False])['result']
  x=rpc('debug_traceBlockByNumber',[hex(b),{"tracer":"prestateTracer","tracerConfig":{"diffMode":True}}])
  if 'error' in x: out[b]={"error":x['error']}; print(b,x['error']); continue
  rows=[]
  for i,t in enumerate(x['result']):
    res=t.get('result',t); pre=res.get('pre',{}); post=res.get('post',{})
    slots=0; accts=0
    for a,pa in post.items():
      pr=pre.get(a)
      if pr is None or (z(pr.get('balance')) and not pr.get('code') and int(str(pr.get('nonce',0)),16 if str(pr.get('nonce','0')).startswith('0x') else 10)==0 and not pr.get('storage')):
        if pr is None: accts+=1
      ps=(pr or {}).get('storage',{})
      for k,v in pa.get('storage',{}).items():
        if not z(v) and z(ps.get(k)): slots+=1
    rows.append({"i":i,"tx":t.get('txHash'),"slots":slots,"accounts":accts})
  tot=sum(r['slots']+r['accounts'] for r in rows)
  out[b]={"gasUsed":int(blk['gasUsed'],16),"txs":len(rows),"growth":tot,"rows":rows,"hashes":blk['transactions']}
  top=sorted(rows,key=lambda r:-(r['slots']+r['accounts']))[:3]
  print(b,int(blk['gasUsed'],16),len(rows),tot,top,flush=True); time.sleep(1)
json.dump(out,open(sys.argv[1],'w'))
