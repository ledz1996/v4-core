"""For each transaction, run debug_traceTransaction (default struct logger, no memory/storage) on the public MegaETH
endpoint, follow call frames to find PoolManager code frames, and record every execution of the five sites
(pc 22378 MULMOD, 22639 MULMOD, 15519 SAR, 16642 SHL, 12232 CALLDATALOAD) with operands and result, checked
against Python. The trace is the replica interpreter's; it selects transactions, and block validation tests the producer.
Read-only. Usage: sites.py <txlist.json> <out.jsonl> <threads>"""
import json,sys,urllib.request,threading,queue
R='https://mainnet.megaeth.com/rpc'; PM='0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
SITES={22378:'MULMOD',22639:'MULMOD',15519:'SAR',16642:'SHL',12232:'CALLDATALOAD'}
M=1<<256
def rpc(m,p):
  r=urllib.request.Request(R,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
  return json.load(urllib.request.urlopen(r,timeout=600))
def sgn(x): return x-M if x>>255 else x
def expect(op,args):
  if op=='MULMOD': a,b,n=args; return (a*b)%n if n else 0
  if op=='SAR': s,v=args; return (sgn(v)>>min(s,256))%M
  if op=='SHL': s,v=args; return (v<<s)%M if s<256 else 0
  return None
def work(tx):
  t=rpc('eth_getTransactionByHash',[tx])['result']
  x=rpc('debug_traceTransaction',[tx,{"disableMemory":True,"disableStorage":True}])
  if 'error' in x: return {"tx":tx,"error":x['error']}
  sl=x['result']['structLogs']; frames=[(t['to'] or '').lower()]; hits=[]
  pend=None
  for i,s in enumerate(sl):
    d=s['depth']
    while len(frames)>d: frames.pop()
    if pend is not None:
      if d==pend[0]: # result of a site instruction
        rec=pend[1]; rec['out']=int(s['stack'][-1],16); rec['ok']= rec['exp'] is None or rec['exp']==rec['out']; hits.append(rec)
        pend=None
      elif d<pend[0]: pend=None
    op=s['op']; st=s['stack']
    if op in ('CALL','STATICCALL','CALLCODE','DELEGATECALL'):
      tgt='0x'+('%064x'%int(st[-2],16))[-40:]
      code=tgt
      if op in ('DELEGATECALL','CALLCODE'): code=tgt  # code that runs is the target's
      if i+1<len(sl) and sl[i+1]['depth']==d+1: frames.append(code)
    elif op in ('CREATE','CREATE2'):
      if i+1<len(sl) and sl[i+1]['depth']==d+1: frames.append('create')
    if frames[-1]==PM and s['pc'] in SITES and SITES[s['pc']]==op:
      n={'MULMOD':3,'SAR':2,'SHL':2,'CALLDATALOAD':1}[op]
      args=[int(v,16) for v in st[::-1][:n]]
      rec={"pc":s['pc'],"op":op,"args":[hex(a) for a in args],"exp":expect(op,args)}
      if op=='MULMOD': rec['hi']=(args[0]*args[1])>>256
      pend=(d,rec)
  for h in hits:
    if h['exp'] is not None: h['exp']=hex(h['exp'])
    h['out']=hex(h['out'])
  return {"tx":tx,"block":int(t['blockNumber'],16),"failed":x['result']['failed'],"steps":len(sl),"hits":hits}
txs=json.load(open(sys.argv[1])); q=queue.Queue(); [q.put(t) for t in txs]; lock=threading.Lock(); out=open(sys.argv[2],'w')
def run():
  while True:
    try: tx=q.get_nowait()
    except queue.Empty: return
    for k in range(3):
      try: r=work(tx); break
      except Exception as e: r={"tx":tx,"error":str(e)}
    with lock: out.write(json.dumps(r)+"\n"); out.flush()
    import time; time.sleep(float(sys.argv[4]) if len(sys.argv)>4 else 0)
th=[threading.Thread(target=run) for _ in range(int(sys.argv[3]))]; [t.start() for t in th]; [t.join() for t in th]
