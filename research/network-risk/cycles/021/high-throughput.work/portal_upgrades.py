# Scan Upgraded(address) events of the MegaETH OptimismPortal2 proxy on Ethereum, 2,000-block windows (L-932).
import json, sys, time, urllib.request
R='https://rpc.flashbots.net'; A='0x7f82f57F0Dd546519324392e408b01fcC7D709e8'
T='0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b'
def rpc(m,p):
    for k in range(6):
        try:
            rq=urllib.request.Request(R,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8.5.0'})
            r=json.load(urllib.request.urlopen(rq,timeout=60))
            if 'error' in r: raise Exception(r['error'])
            return r['result']
        except Exception as e:
            err=e; time.sleep(2*(k+1))
    raise err
lo=int(sys.argv[1]); hi=int(rpc('eth_blockNumber',[]),16); out=[]; b=lo; n=0
while b<=hi:
    e=min(hi,b+1999); logs=rpc('eth_getLogs',[{'address':A,'topics':[T],'fromBlock':hex(b),'toBlock':hex(e)}]); n+=1
    for l in logs: out.append({'block':int(l['blockNumber'],16),'impl':'0x'+l['topics'][1][26:],'tx':l['transactionHash']}); print(out[-1],flush=True)
    b=e+1
json.dump({'from':lo,'to':hi,'windows':n,'upgraded':out},open(sys.argv[2],'w'),indent=1)
print('done',lo,hi,n,len(out))
