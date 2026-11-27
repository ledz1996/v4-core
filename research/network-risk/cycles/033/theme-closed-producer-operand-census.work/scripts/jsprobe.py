import json,sys,urllib.request
url,tx=sys.argv[1],sys.argv[2]
tr="""{n:0, ops:{}, step:function(log,db){var op=log.op.toNumber(); if(op==0x09||op==0x1d){this.n++; var s=log.stack; this.ops[op]=(this.ops[op]||[]); if(this.ops[op].length<2) this.ops[op].push([s.peek(0).toString(16), s.peek(1).toString(16), typeof s.peek(0), log.contract.getAddress? toHex(log.contract.getAddress()):'' , log.getPC()]);}}, fault:function(){}, result:function(){return {n:this.n, ops:this.ops};}}"""
req={"jsonrpc":"2.0","id":1,"method":"debug_traceTransaction","params":[tx,{"tracer":tr,"timeout":"60s"}]}
r=urllib.request.urlopen(urllib.request.Request(url,json.dumps(req).encode(),{'content-type':'application/json','user-agent':'census'}),timeout=90).read()
print(r[:2000])
