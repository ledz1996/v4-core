"""Read-only: eth_simulateV1 with two transactions in one simulated block calling a stub that returns TLOAD(0) and then TSTOREs 1.
Expected [0,0] when transient storage is cleared between transactions. Output raw/sim_tclear.json"""
import json, sys, urllib.request, os
NETS=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','..','state','networks.json')))['networks']
STUB='0x5f5c5f5260015f5d60205ff3'; A='0x00000000000000000000000000000000c0ffee27'
def rpc(url, method, params):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    try:
        r=json.loads(urllib.request.urlopen(urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'rpc-client'}),timeout=30).read())
        return r.get('result') if 'error' not in r else {'error':r['error']}
    except Exception as e: return {'httpError':str(e)[:200]}
want=[int(x) for x in sys.argv[2:]]
out={}
for n in NETS:
    if want and n['chainId'] not in want: continue
    u=n['rpc']; pm=n['poolManager']
    r={'clientBefore':rpc(u,'web3_clientVersion',[])}
    calls=[{'from':'0x00000000000000000000000000000000000f0f0f','to':A,'gas':'0x186a0'}]*2
    r['sim']=rpc(u,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{A:{'code':STUB}},'calls':calls}],'validation':False},'latest'])
    # same stub called twice inside one eth_call via a caller stub: CALL A twice, return second result
    r['clientAfter']=rpc(u,'web3_clientVersion',[])
    s=r['sim']
    try: r['words']=[int(c['returnData'],16) for c in s[0]['calls']]
    except Exception: r['words']=None
    out[n['chainId']]=r; print(n['chainId'],r['clientBefore'] if isinstance(r['clientBefore'],str) else '?', r['words'], str(s)[:160] if r['words'] is None else '', flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
