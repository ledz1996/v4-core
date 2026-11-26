"""Read-only: what each endpoint accepts for eth_call / eth_estimateGas with from = PoolManager and gas price 0.
No transaction is sent. Output: raw/from_pm.json"""
import json, sys, time, urllib.request, os
NETS=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','..','state','networks.json')))['networks']
def rpc(url, method, params):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    for k in range(3):
        try:
            req=urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'rpc-client'})
            r=json.loads(urllib.request.urlopen(req,timeout=30).read())
            return r.get('result') if 'error' not in r else {'error':r['error']}
        except Exception as e:
            err=str(e)[:200]; time.sleep(2)
    return {'httpError':err}
DEAD='0x000000000000000000000000000000000000dEaD'
out={}
ALT={1:'https://eth.drpc.org',137:'https://polygon.drpc.org'}
for n in NETS:
    if n['chainId'] not in ALT: continue
    pm=n['poolManager']; u=ALT[n['chainId']]; r={'rpc':u,'pm':pm}
    r['clientBefore']=rpc(u,'web3_clientVersion',[])
    r['nonce']=rpc(u,'eth_getTransactionCount',[pm,'latest'])
    r['balance']=rpc(u,'eth_getBalance',[pm,'latest'])
    r['codeLen']=(lambda c: (len(c)-2)//2 if isinstance(c,str) else c)(rpc(u,'eth_getCode',[pm,'latest']))
    cases={
     'call_v0_gp0':('eth_call',[{'from':pm,'to':DEAD,'gasPrice':'0x0','gas':'0x30d40'},'latest']),
     'est_v0_gp0':('eth_estimateGas',[{'from':pm,'to':DEAD,'gasPrice':'0x0'}]),
     'call_v1_gp0':('eth_call',[{'from':pm,'to':DEAD,'value':'0x1','gasPrice':'0x0','gas':'0x30d40'},'latest']),
     'est_v1_gp0':('eth_estimateGas',[{'from':pm,'to':DEAD,'value':'0x1','gasPrice':'0x0'}]),
     'call_extsload_gp0':('eth_call',[{'from':pm,'to':pm,'data':'0x1e2eaeaf'+'00'*32,'gasPrice':'0x0','gas':'0x30d40'},'latest']),
     'call_v1_nogp':('eth_call',[{'from':pm,'to':DEAD,'value':'0x1','gas':'0x30d40'},'latest']),
    }
    for k,(m,p) in cases.items(): r[k]=rpc(u,m,p)
    r['clientAfter']=rpc(u,'web3_clientVersion',[])
    out[n['chainId']]=r
    print(n['chainId'], {k:(str(v)[:90]) for k,v in r.items() if k not in('rpc','pm')}, flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
