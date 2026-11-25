# Task 1 second probe: balance and code at blocks where they differ
import json
from rpch import rpc1, OFF, ARC, PM
out={}
for b in (1000000, 20000000, 35000000, 45000000, 50000000):
    tag=hex(b)
    for name,url in (('official',OFF),('archive',ARC)):
        bal=rpc1(url,'eth_getBalance',[PM,tag]); code=rpc1(url,'eth_getCode',[PM,tag])
        nonce=rpc1(url,'eth_getTransactionCount',[PM,tag])
        blk=rpc1(url,'eth_getBlockByNumber',[tag,False])
        cl=(len(code[1])-2)//2 if isinstance(code,list) and isinstance(code[1],str) else code
        bh=blk[1]['hash'] if isinstance(blk,list) and isinstance(blk[1],dict) else str(blk)[:200]
        out[f'{name}@{b}']={'client':bal[0] if isinstance(bal,list) else None,'balance':bal[1] if isinstance(bal,list) else bal,'codeLen':cl,'nonce':nonce[1] if isinstance(nonce,list) else nonce,'blockHash':bh,'clientAfter':bal[2] if isinstance(bal,list) else None}
        print(name,b,out[f'{name}@{b}'])
json.dump(out,open('../out/t1b_hyper.json','w'),indent=1)
