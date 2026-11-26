# Does eth_simulateV1 with a block time after T14 (1796742000) switch Tempo's rules? Compare calls to the
# T14 configurable account precompile address with and without the override. Read-only.
import json,sys,urllib.request,ssl
U='https://rpc.mainnet.tempo.xyz'
def rpc(m,p):
    r=urllib.request.Request(U,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r,timeout=60))
PM='0x33620f62c5b9b2086dd6b62f4a297a9f30347029'
for t in [None, 1796742000+3600]:
    bsc={'calls':[{'from':PM,'to':'0xAACC000000000000000000000000000000000000','data':'0x','gas':hex(2_000_000)},
                  {'from':PM,'to':'0xAACC000000000000000000000000000000000000','data':'0x70a08231'+'00'*12+PM[2:],'gas':hex(2_000_000)}]}
    if t: bsc['blockOverrides']={'time':hex(t)}
    r=rpc('eth_simulateV1',[{'blockStateCalls':[bsc],'validation':False},'latest'])
    print('time',t, json.dumps([{k:c.get(k) for k in ('status','returnData','gasUsed','error')} for c in r['result'][0]['calls']]))
