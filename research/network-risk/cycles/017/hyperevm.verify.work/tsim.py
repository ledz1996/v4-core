import json,urllib.request,sys
C='0x00000000000000000000000000000000000c0de1'
CODE='0x3615601057'+'60005c'+'600052'+'6020'+'6000'+'f3'+'5b'+'6042'+'6000'+'5d'+'00'
F='0x00000000000000000000000000000000000f0f01'
def rpc(u,m,p):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'probe'})
    try: return json.load(urllib.request.urlopen(r,timeout=60))
    except Exception as e: return {'exc':str(e)}
out={}
for u in sys.argv[1:]:
    o={}
    o['single_read']=rpc(u,'eth_call',[{'to':C,'data':'0x01'},'latest',{C:{'code':CODE}}])
    calls=[{'from':F,'to':C,'data':'0x','gas':'0x30000'},{'from':F,'to':C,'data':'0x01','gas':'0x30000'}]
    o['simulate_same_block']=rpc(u,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{C:{'code':CODE},F:{'balance':'0x1000000000000000000'}},'calls':calls}],'validation':False},'latest'])
    o['simulate_two_blocks']=rpc(u,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{C:{'code':CODE},F:{'balance':'0x1000000000000000000'}},'calls':calls[:1]},{'calls':calls[1:]}],'validation':False},'latest'])
    out[u]=o
json.dump(out,open('out/tsim.json','w'),indent=1)
for u,o in out.items():
    print(u)
    for k,v in o.items():
        if 'result' in v and isinstance(v['result'],list): print(' ',k,[[ (c.get('status'),c.get('returnData')) for c in b.get('calls',[])] for b in v['result']])
        else: print(' ',k,json.dumps(v)[:300])
