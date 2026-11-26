"""usage: slowscan.py rpc topic0 range from to out.jsonl delay -- one eth_getLogs per request, newest first, resumable"""
import sys,json,urllib.request,time,os
U,T,R,F,TO,O,D=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),sys.argv[6],float(sys.argv[7])
def post(body):
    req=urllib.request.Request(U,json.dumps(body).encode(),{"content-type":"application/json","user-agent":"rpc-client/1.0"})
    return json.load(urllib.request.urlopen(req,timeout=120))
lo=TO+1
if os.path.exists(O):
    for line in open(O):
        r=json.loads(line)
        if r.get('done'): lo=min(lo,r['from'])
f=open(O,'a')
def cv():
    for i in range(10):
        try: return post({"jsonrpc":"2.0","id":0,"method":"web3_clientVersion","params":[]}).get('result')
        except Exception: time.sleep(10)
f.write(json.dumps({'client':cv(),'time':time.time(),'start':lo-1})+'\n'); f.flush()
e=lo-1
while e>=F:
    s=max(F,e-R+1)
    for att in range(20):
        try:
            r=post({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(s),"toBlock":hex(e),"topics":[T]}]})
            if 'error' in r: raise Exception(str(r['error']))
            break
        except Exception as ex: err=str(ex); r=None; time.sleep(min(60,5*(att+1)))
    if r is None: f.write(json.dumps({'failed':[s,e],'err':err})+'\n')
    else: f.write(json.dumps({'done':True,'from':s,'to':e,'logs':r['result']})+'\n')
    f.flush(); e=s-1; time.sleep(D)
f.write(json.dumps({'client':cv(),'time':time.time(),'end':F})+'\n')
