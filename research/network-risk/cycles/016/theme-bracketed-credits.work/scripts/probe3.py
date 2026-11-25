import json,urllib.request,sys
def rpc(url,m,p):
    r=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    try: return json.load(urllib.request.urlopen(r,timeout=40))
    except Exception as e: return {'error':str(e)}
nets=json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
A={'L2XDM':'0x4200000000000000000000000000000000000007','L2SB':'0x4200000000000000000000000000000000000010','LxLyBridge':'0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe','Teleporter':'0x253b2784c75e510dD0fF1da844684a1aC0aa5fcf','ArbRetryable':'0x000000000000000000000000000000000000006E','StateReceiver':'0x0000000000000000000000000000000000001001'}
out={}
for n in nets:
    o={}
    for k,a in A.items():
        c=rpc(n['rpc'],'eth_getCode',[a,'latest']); o[k]=len(c.get('result','0x'))//2-1 if 'result' in c else c.get('error')
    cv=rpc(n['rpc'],'web3_clientVersion',[]); o['client']=cv.get('result',cv.get('error'))
    # messageNonce on L2XDM to check it's a messenger
    if isinstance(o['L2XDM'],int) and o['L2XDM']>0:
        r=rpc(n['rpc'],'eth_call',[{'to':A['L2XDM'],'data':'0xecc70428'},'latest']); o['L2XDM_messageNonce']=r.get('result',r.get('error'))
    out[n['chainId']]=o; print(n['chainId'],n['name'],o,flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
