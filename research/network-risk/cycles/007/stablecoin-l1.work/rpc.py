import json,urllib.request,sys,time
URLS={4217:"https://rpc.mainnet.tempo.xyz",5042:"https://rpc.mainnet.arc.io"}
ARC_SIM="https://arc.drpc.org"
ARC_ALT=["https://arc.drpc.org","https://arc-rpc.publicnode.com","https://5042.rpc.thirdweb.com"]
PM={4217:"0x33620f62c5b9b2086dd6b62f4a297a9f30347029",5042:"0x8366a39CC670B4001A1121B8F6A443A643e40951"}
def rpc(chain,method,params,url=None,raw=False):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    for i in range(4):
        try:
            req=urllib.request.Request(url or URLS[chain],data=body,headers={"content-type":"application/json","user-agent":"curl/8"})
            r=json.load(urllib.request.urlopen(req,timeout=25))
            if raw: return r
            if 'error' in r: return {'error':r['error']}
            return r['result']
        except Exception as e:
            err=e; time.sleep(1+i)
    return {'error':str(err)}
def batch(chain,calls,url=None,n=None):
    n=n or (10 if chain==5042 else 40)
    out=[]
    for i in range(0,len(calls),n):
        r=_batch(chain,calls[i:i+n],url)
        if isinstance(r,dict): r=[r]*len(calls[i:i+n])
        out+=r
    return out
def _batch(chain,calls,url=None):
    body=json.dumps([{"jsonrpc":"2.0","id":i,"method":m,"params":p} for i,(m,p) in enumerate(calls)]).encode()
    for i in range(4):
        try:
            req=urllib.request.Request(url or URLS[chain],data=body,headers={"content-type":"application/json","user-agent":"curl/8"})
            r=json.load(urllib.request.urlopen(req,timeout=25))
            r.sort(key=lambda x:x['id'])
            return [x.get('result',{'error':x.get('error')}) for x in r]
        except Exception as e:
            err=e; time.sleep(1+i)
    return {'error':str(err)}
def call(chain,to,data,frm=None,block='latest',value=None,ov=None):
    tx={"to":to,"data":data}
    if frm: tx['from']=frm
    if value: tx['value']=hex(value)
    p=[tx,block]
    if ov: p.append(ov)
    return rpc(chain,'eth_call',p)
def pad(a): return a.lower().replace('0x','').rjust(64,'0')
if __name__=='__main__':
    for c in URLS:
        print(c, rpc(c,'web3_clientVersion',[]), int(rpc(c,'eth_blockNumber',[]),16), rpc(c,'eth_chainId',[]))
