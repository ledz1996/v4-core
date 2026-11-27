"""Task 1 probe: which endpoints serve debug_traceTransaction prestateTracer (diffMode) and trace_replayTransaction stateDiff
on one recent PoolManager transaction. Read-only. Writes raw/probe.json."""
import json, sys, time
from rpcu import call
from eps import CAND, NETS
out={}
for cid in [int(x) for x in sys.argv[1:]] or CAND:
    pm=NETS[cid]['poolManager']; r={}
    urls=CAND[cid]; tx=None
    for u in urls:
        bn,e=call(u,'eth_blockNumber',[],30)
        if e: continue
        bn=int(bn,16)
        for span in (100,1000,5000):
            lg,e=call(u,'eth_getLogs',[{'address':pm,'fromBlock':hex(bn-span),'toBlock':hex(bn)}],60)
            if lg: tx=lg[-1]['transactionHash']; break
        if tx: break
    r['tx']=tx
    for u in urls:
        v0,e0=call(u,'web3_clientVersion',[],30)
        d={'clientBefore':v0 or e0}
        t=time.time(); a,e=call(u,'debug_traceTransaction',[tx,{'tracer':'prestateTracer','tracerConfig':{'diffMode':True}}],90)
        d['prestateDiff']='ok %d bytes, pm in post: %s'%(len(json.dumps(a)), pm.lower() in {k.lower() for k in (a or {}).get('post',{})}) if a is not None else e
        a,e=call(u,'debug_traceTransaction',[tx,{'tracer':'prestateTracer'}],90)
        d['prestate']='ok %d bytes'%len(json.dumps(a)) if a is not None else e
        a,e=call(u,'trace_replayTransaction',[tx,['stateDiff']],90)
        d['replayStateDiff']='ok %d bytes'%len(json.dumps(a)) if a is not None else e
        a,e=call(u,'debug_traceTransaction',[tx,{'tracer':'callTracer'}],90)
        d['callTracer']='ok' if a is not None else e
        v1,e1=call(u,'web3_clientVersion',[],30); d['clientAfter']=v1 or e1
        d['secs']=round(time.time()-t,1)
        r[u]=d; print(cid,u,json.dumps(d)[:600],flush=True)
    out[cid]=r
json.dump(out,open('../raw/probe-%s.json'%('-'.join(sys.argv[1:]) or 'all'),'w'),indent=1)
