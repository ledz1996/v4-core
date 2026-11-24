import json,sys,collections; from lib import *
URL='https://ethereum-rpc.publicnode.com'
PM='0x000000000004444c5dc75cb358380d2e3de08a90'
head=int(rpc(URL,'eth_blockNumber',[])['result'],16)
# 120 blocks: every 420th block over the last 50,400 blocks (about seven days)
blocks=[head-i*420 for i in range(120)]
cnt=collections.Counter(); to_pm=collections.Counter(); hdr=set(); n=0; deleg_to_pm=0
for i in range(0,len(blocks),6):
    batch=[{'jsonrpc':'2.0','id':b,'method':'eth_getBlockByNumber','params':[hex(b),True]} for b in blocks[i:i+6]]
    r=post(URL,batch,timeout=90)
    for x in r:
        blk=x['result']; hdr|=set(blk.keys()); n+=1
        for t in blk['transactions']:
            cnt[t['type']]+=1
            if (t.get('to') or '').lower()==PM: to_pm[t['type']]+=1
            extra=set(t.keys())-{'blockHash','blockNumber','from','gas','gasPrice','hash','input','nonce','to','transactionIndex','value','type','v','r','s','chainId','accessList','maxFeePerGas','maxPriorityFeePerGas','yParity','maxFeePerBlobGas','blobVersionedHashes','authorizationList'}
            if extra: cnt['extra:'+','.join(sorted(extra))]+=1
out={'head':head,'blocks':n,'first':blocks[-1],'types':dict(cnt),'directToPM':dict(to_pm),'headerFields':sorted(hdr)}
print(json.dumps(out,indent=1)); json.dump(out,open('raw_txtypes.json','w'))
