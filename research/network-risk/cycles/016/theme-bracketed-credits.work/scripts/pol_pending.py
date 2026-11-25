import json,urllib.request,sys
def rpc(url,m,p):
    r=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    try: return json.load(urllib.request.urlopen(r,timeout=40))
    except Exception as e: return {'error':str(e)}
d=json.load(open('/home/user/v4-core/research/network-risk/cycles/008/established-l1.work/raw/polygon_statesync_since_uburu.json'))
PM='67366782805870060151383f4bbff9dab53e5cd6'
SS='0x28e4F3a7f651294B9564800b2D01f35189A5bFbE'
L1=['https://ethereum-rpc.publicnode.com','https://eth.llamarpc.com','https://cloudflare-eth.com']
fsh=rpc('https://ethereum-rpc.publicnode.com','web3_sha3',['0x'+'failedStateSyncHashes(uint256)'.encode().hex()])['result'][:10]
out={}
for sid,(recv,l1b) in d['receivers'].items():
    sid=int(sid)
    h=rpc('https://polygon-bor-rpc.publicnode.com','eth_call',[{'to':'0x0000000000000000000000000000000000001001','data':fsh+hex(sid)[2:].rjust(64,'0')},'latest'])
    logs=None
    for u in L1:
        r=rpc(u,'eth_getLogs',[{'address':SS,'fromBlock':hex(l1b),'toBlock':hex(l1b),'topics':[None,'0x'+hex(sid)[2:].rjust(64,'0')]}])
        if 'result' in r: logs=r['result']; src=u; break
    data=logs[0]['data'] if logs else None
    out[sid]={'receiver':recv,'l1Block':l1b,'pendingHash':h.get('result'),'hasPM':(PM in data.lower()) if data else None,'dataLen':len(data) if data else None,'l1rpc':src if logs else None}
    print(sid,out[sid])
json.dump(out,open(sys.argv[1],'w'),indent=1)
