# Read-only. Scan eth_feeHistory on X Layer for blocks whose gasUsedRatio exceeds a threshold.
# usage: fee_scan.py <startBlock> <endBlock> <threshold> <out.jsonl>
import sys, json, urllib.request, time, threading
URLS=['https://rpc.xlayer.tech','https://xlayerrpc.okx.com']
def post(u, body):
    req=urllib.request.Request(u, data=json.dumps(body).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
start,end,thr=int(sys.argv[1]),int(sys.argv[2]),float(sys.argv[3]); out=open(sys.argv[4],'a')
lock=threading.Lock(); state={'next':end,'calls':0,'hits':0,'blocks':0,'max':0.0}
def worker(u):
    while True:
        with lock:
            newest=state['next']
            if newest<start: return
            state['next']=newest-1024*8
        batch=[]
        for i in range(8):
            nb=newest-1024*i
            if nb<start: break
            cnt=min(1024, nb-start+1)
            batch.append({'jsonrpc':'2.0','id':i,'method':'eth_feeHistory','params':[hex(cnt),hex(nb),[]]})
        for attempt in range(40):
            try:
                r=post(u,batch)
                if not isinstance(r,list) or any('error' in x for x in r): time.sleep(1+attempt); continue
                with lock:
                    for x in r:
                        res=x['result']; ob=int(res['oldestBlock'],16); g=res['gasUsedRatio']
                        state['blocks']+=len(g); state['max']=max(state['max'],max(g) if g else 0)
                        for k,v in enumerate(g):
                            if v>=thr:
                                out.write(json.dumps([ob+k,v])+'\n'); state['hits']+=1
                    out.flush(); state['calls']+=1
                    if state['calls']%10==0: print('calls',state['calls'],'blocks',state['blocks'],'hits',state['hits'],'max',state['max'],flush=True)
                break
            except Exception as e:
                time.sleep(2+attempt)
        else: print('gave up',newest,flush=True)
ts=[threading.Thread(target=worker,args=(u,)) for u in URLS for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
print('finished',state,flush=True)
