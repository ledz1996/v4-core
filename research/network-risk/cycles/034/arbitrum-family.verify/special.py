import json,subprocess,sys
U={42161:('https://arb1.arbitrum.io/rpc','0x360e68faccca8ca495c1b759fd9eee466db9fb32'),4663:('https://rpc.mainnet.chain.robinhood.com','0x8366a39cc670b4001a1121b8f6a443a643e40951'),99901:('https://rpc.elysium.kinetiq.xyz','0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1')}
T=['0x0000f90827f1c53a10cb7a02335b175320002935','0x00000000000000000000000000000000000a4b05']
def rpc(u,m,p):
    o=subprocess.run(['curl','-s','--max-time','40','-X','POST','-H','content-type: application/json','--data',json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}),u],capture_output=True,text=True).stdout
    try: return json.loads(o)
    except: return {'raw':o[:200]}
out={}
for c,(u,pm) in U.items():
    bn=rpc(u,'eth_blockNumber',[])['result']; r={'block':int(bn,16),'pmBalance':rpc(u,'eth_getBalance',[pm,bn]).get('result')}
    r['nativeTokenMgmtFrom']=rpc(u,'eth_call',[{'to':'0x000000000000000000000000000000000000006b','data':'0x'+'%08x'%0},bn]) if False else None
    for t in T:
        r[t+':code']=len(rpc(u,'eth_getCode',[t,bn]).get('result','0x'))//2-1
        for name,data,val in [('empty','0x','0x0'),('emptyValue1','0x','0x1'),('transfer','0xa9059cbb'+'00'*12+'11'*20+'%064x'%1,'0x0'),('balanceOf','0x70a08231'+'00'*12+pm[2:].lower(),'0x0'),('word32','0x'+'%064x'%(int(bn,16)-1),'0x0')]:
            x=rpc(u,'eth_call',[{'from':pm,'to':t,'data':data,'value':val,'gas':'0x1c9c380'},bn])
            r[t+':'+name]=x.get('result',x.get('error'))
    out[c]=r; print(c,json.dumps(r,indent=0))
json.dump(out,open(sys.argv[1],'w'),indent=1)
