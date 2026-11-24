# Lead L-464: sNVB history of the BNB Smart Chain PoolManager from a second log source (NodeReal, 50,000 block ranges).
import sys,json,time
sys.path.insert(0,'.')
from rpc import rpc
from keccak import keccak256
def topic(sig):
    h=keccak256(sig.encode()); h=h if isinstance(h,(bytes,bytearray)) else bytes.fromhex(h.replace('0x',''))
    return '0x'+h.hex()
U='https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3'
PM='0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
TOK='0x6d6c16a3cbd318f3000e33cfd27662cf00f7e7c1'
T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
pad='0x'+'0'*24+PM[2:]
filters={'out':[T,pad],'in':[T,None,pad],'rebase':[topic('LogRebase(uint256,uint256,uint256)')]}
HEAD=int(rpc(U,"eth_blockNumber",[])["result"],16)-10
start=int(sys.argv[1]); head=min(int(sys.argv[2]),HEAD); TAG=sys.argv[3]

res={k:[] for k in filters}; fails=[]
b=start; n=0
while b<=head:
    e=min(b+49999,head)
    for k,tp in filters.items():
        ok=False
        for attempt in range(5):
            r=rpc(U,'eth_getLogs',[{"fromBlock":hex(b),"toBlock":hex(e),"address":TOK,"topics":tp}],timeout=60,retries=0)
            if isinstance(r,dict) and isinstance(r.get('result'),list):
                res[k]+=[{'b':int(l['blockNumber'],16),'tx':l['transactionHash'],'topics':l['topics'],'data':l['data'],'li':int(l['logIndex'],16)} for l in r['result']]; ok=True; break
            time.sleep(2+attempt*2)
        if not ok: fails.append((k,b,e,str(r)[:150]))
    n+=1
    if n%100==0:
        print(b,{k:len(v) for k,v in res.items()},'fails',len(fails),flush=True)
        json.dump({'head':head,'start':start,'upto':e,'logs':res,'fails':fails},open('raw/snvb_logs_nodereal_%s.json'%TAG,'w'))
    b=e+1
json.dump({'head':head,'start':start,'upto':head,'logs':res,'fails':fails},open('raw/snvb_logs_nodereal_%s.json'%TAG,'w'))
print('done',{k:len(v) for k,v in res.items()},'fails',len(fails))
