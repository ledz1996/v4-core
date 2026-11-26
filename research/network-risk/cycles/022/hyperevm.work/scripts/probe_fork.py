import json,urllib.request,sys
A='0x00000000000000000000000000000000000c0ffe'
def rpc(u,m,p):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'probe'})
    try: return json.load(urllib.request.urlopen(r,timeout=30))
    except Exception as e: return {'err':str(e)}
# programs: CLZ(0x1e) of 1 ; MCOPY ; TSTORE/TLOAD; BLOBBASEFEE(0x4a); PUSH0
progs={
 'clz':'60011e60005260206000f3',
 'push0_mcopy':'7f11223344556677889900aabbccddeeff00112233445566778899aabbccddeeff5f526020600060205e60206020f3',
 'tstore_tload':'602a60075d60075c60005260206000f3',
 'blobbasefee':'4a60005260206000f3',
 'blobhash0':'5f4960005260206000f3',
}
out={}
for u in sys.argv[1:]:
    out[u]={'client':rpc(u,'web3_clientVersion',[]).get('result'),'head':rpc(u,'eth_blockNumber',[]).get('result')}
    for k,c in progs.items():
        out[u][k]=rpc(u,'eth_call',[{'to':A,'gas':'0x100000'},'latest',{A:{'code':'0x'+c}}])
    for a in ['0x000000000000000000000000000000000000000b','0x0000000000000000000000000000000000000011','0x0000000000000000000000000000000000000100']:
        out[u]['pc_'+a[-4:]]=rpc(u,'eth_call',[{'to':a,'data':'0x'+'00'*64,'gas':'0x100000'},'latest'])
        out[u]['code_'+a[-4:]]=rpc(u,'eth_getCode',[a,'latest']).get('result')
print(json.dumps(out,indent=1))
