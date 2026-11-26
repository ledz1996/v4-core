"""Probe muxTracer (prestateTracer diffMode + callTracer withLog) and prestateTracer with disableCode, and time 10 calls."""
import json, sys, time
from rpcu import call
P=json.load(open('../raw/probe-%s.json'%sys.argv[1]))
cid=sys.argv[1]; tx=P[cid]['tx']
for u in sys.argv[2:]:
    d={'client':call(u,'web3_clientVersion',[],30)}
    a,e=call(u,'debug_traceTransaction',[tx,{'tracer':'muxTracer','tracerConfig':{'prestateTracer':{'diffMode':True,'disableCode':True},'callTracer':{'withLog':True}}}],90)
    d['mux']= ('ok keys=%s bytes=%d'%(list(a.keys()),len(json.dumps(a)))) if a else e
    if a and 'callTracer' in a:
        c=a['callTracer']; 
        def logs(f):
            for l in f.get('logs',[]): yield l
            for s in f.get('calls',[]): yield from logs(s)
        L=list(logs(c)); d['logs']=len(L); d['logpos']= 'position' in L[0] if L else None
    t=time.time(); ok=0; errs=[]
    for i in range(10):
        a,e=call(u,'debug_traceTransaction',[tx,{'tracer':'prestateTracer','tracerConfig':{'disableCode':True}}],90)
        if a: ok+=1; sz=len(json.dumps(a))
        else: errs.append(e[:80])
    d['prestate10']='%d ok in %.1fs, %s bytes, errs %s'%(ok,time.time()-t,sz if ok else '-',errs[:2])
    d['clientAfter']=call(u,'web3_clientVersion',[],30)
    print(cid,u,json.dumps(d),flush=True)
