import json,subprocess,sys
sys.path.insert(0,'tools/opdiff')
from evm import keccak
def rpc(u,m,p):
    out=subprocess.run(['curl','-s','--max-time','40','-X','POST','-H','content-type: application/json','--data',json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}),u],capture_output=True,text=True).stdout
    return json.loads(out)
nets=[(42161,'https://arb1.arbitrum.io/rpc','0x360e68faccca8ca495c1b759fd9eee466db9fb32'),(4663,'https://rpc.mainnet.chain.robinhood.com','0x8366a39cc670b4001a1121b8f6a443a643e40951'),(99901,'https://rpc.elysium.kinetiq.xyz','0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1')]
sel=lambda s:'0x'+keccak(s.encode()).hex()[:8]
res={}
for cid,u,pm in nets:
    bn=rpc(u,'eth_blockNumber',[])['result']
    r={'block':int(bn,16)}
    for f in ['owner()','protocolFeeController()']:
        v=rpc(u,'eth_call',[{'to':pm,'data':sel(f)},bn])['result']
        a='0x'+v[-40:]; c=rpc(u,'eth_getCode',[a,bn])['result']
        r[f]=a; r[f+'.codeLen']=(len(c)-2)//2
        if (len(c)-2)//2>0:
            import hashlib; r[f+'.codeSha256']=hashlib.sha256(bytes.fromhex(c[2:])).hexdigest()[:16]
    code=rpc(u,'eth_getCode',[pm,bn])['result']; import hashlib
    r['pmCodeLen']=(len(code)-2)//2; r['pmSha256']=hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()[:16]
    res[cid]=r; print(cid,r)
json.dump(res,open(sys.argv[1],'w'),indent=1)
