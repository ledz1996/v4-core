"""usage: batchscan.py rpc topic0 range batch from to out.jsonl [address]  -- batched eth_getLogs, resumable, appends per-batch records"""
import sys,json,urllib.request,time,os
U,T,R,NB,F,TO,O=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]),sys.argv[7]
ADDR=sys.argv[8] if len(sys.argv)>8 else None
def post(body):
    req=urllib.request.Request(U,json.dumps(body).encode(),{"content-type":"application/json","user-agent":"rpc-client/1.0"})
    return json.load(urllib.request.urlopen(req,timeout=120))
start=F
if os.path.exists(O):
    for line in open(O):
        r=json.loads(line)
        if r.get('done'): start=max(start,r['to']+1)
f=open(O,'a')
f.write(json.dumps({'client':post({"jsonrpc":"2.0","id":0,"method":"web3_clientVersion","params":[]}).get('result'),'time':time.time(),'start':start})+'\n')
b=start
while b<=TO:
    reqs=[];
    for i in range(NB):
        s=b+i*R; e=min(TO,s+R-1)
        if s>TO: break
        flt={"fromBlock":hex(s),"toBlock":hex(e),"topics":[T.split(",") if "," in T else T]}
        if ADDR: flt["address"]=ADDR.split(",") if "," in ADDR else ADDR
        if T=="-": del flt["topics"]
        reqs.append({"jsonrpc":"2.0","id":i,"method":"eth_getLogs","params":[flt]})
    last=min(TO,b+len(reqs)*R-1)
    for att in range(8):
        try:
            res=post(reqs)
            if isinstance(res,dict): raise Exception(str(res)[:200])
            bad=[x for x in res if 'error' in x]
            if bad: raise Exception(str(bad[0])[:200])
            break
        except Exception as ex:
            err=str(ex); time.sleep(1.5*(att+1)); res=None
    if res is None:
        f.write(json.dumps({'failed':[b,last],'err':err})+'\n'); f.flush(); b=last+1; continue
    logs=[l for x in res for l in x['result']]
    f.write(json.dumps({'done':True,'from':b,'to':last,'logs':logs})+'\n'); f.flush()
    b=last+1
f.write(json.dumps({'client':post({"jsonrpc":"2.0","id":0,"method":"web3_clientVersion","params":[]}).get('result'),'time':time.time(),'end':b})+'\n')
