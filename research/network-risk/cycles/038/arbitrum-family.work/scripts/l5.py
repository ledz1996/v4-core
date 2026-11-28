"""Cycle 38 L5: PoolManager code hash, owner(), protocolFeeController(), owner code length, on the three chains. Read-only."""
import json, subprocess, sys, hashlib
def rpc(u,m,p):
    o=subprocess.run(['curl','-s','--max-time','40','-X','POST','-H','content-type: application/json','--data',json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}),u],capture_output=True,text=True).stdout
    return json.loads(o)
N=json.load(open('state/networks.json')); N=N if isinstance(N,list) else N.get('networks',N)
out={}
for n in N:
    if n['chainId'] not in (42161,4663,99901): continue
    u,pm=n['rpc'],n['poolManager']
    bn=rpc(u,'eth_blockNumber',[])['result']
    code=bytes.fromhex(rpc(u,'eth_getCode',[pm,bn])['result'][2:])
    own=rpc(u,'eth_call',[{'to':pm,'data':'0x8da5cb5b'},bn])['result']
    pfc=rpc(u,'eth_call',[{'to':pm,'data':'0xf02de3b2'},bn])['result']
    oa='0x'+own[-40:]; pa='0x'+pfc[-40:]
    oc=rpc(u,'eth_getCode',[oa,bn])['result']; pc=rpc(u,'eth_getCode',[pa,bn])['result']
    r={'block':int(bn,16),'codeLen':len(code),'codeSha256':hashlib.sha256(code).hexdigest()[:16],'owner':oa,'protocolFeeController':pa,
       'ownerCodeLen':(len(oc)-2)//2,'pfcCodeLen':(len(pc)-2)//2,
       'matchesNetworksJson':{'codeSha256':hashlib.sha256(code).hexdigest()[:16]==n['codeSha256'],'owner':oa.lower()==n['owner'].lower(),'pfc':pa.lower()==n['protocolFeeController'].lower()}}
    tr=rpc(u,'debug_traceBlockByNumber',[bn,{'tracer':'callTracer'}])
    r['debug_traceBlockByNumber']='served' if 'result' in tr else tr.get('error')
    out[n['chainId']]=r; print(n['chainId'],json.dumps(r))
json.dump(out,open(sys.argv[1],'w'),indent=1)
