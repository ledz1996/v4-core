"""Probe extra public endpoints: client version, prestateTracer diffMode, prestateTracer (disableCode), callTracer withLog, muxTracer."""
import json, sys
from rpcu import call
cid=sys.argv[1]; tx=json.load(open('../raw/probe-%s.json'%cid))[cid]['tx']
for u in sys.argv[2:]:
    d={'client':call(u,'web3_clientVersion',[],20)}
    for name,cfg in [('diff',{'tracer':'prestateTracer','tracerConfig':{'diffMode':True,'disableCode':True}}),('pre',{'tracer':'prestateTracer','tracerConfig':{'disableCode':True}}),
                     ('call',{'tracer':'callTracer','tracerConfig':{'withLog':True}}),('mux',{'tracer':'muxTracer','tracerConfig':{'prestateTracer':{'diffMode':True,'disableCode':True},'callTracer':{'withLog':True}}})]:
        a,e=call(u,'debug_traceTransaction',[tx,cfg],60)
        d[name]=('ok %d'%len(json.dumps(a))) if a else (e or 'empty')[:120]
    d['clientAfter']=call(u,'web3_clientVersion',[],20)
    print(cid,u,json.dumps(d),flush=True)
