"""Read-only: count PoolManager logs by topic from a start block to head. Usage: python3 -I logs.py <rpc> <from> <step> <out.json>"""
import sys, json, urllib.request, collections, time
rpc, start, step, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
PM='0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
def rq(b):
    r=urllib.request.Request(rpc,data=json.dumps(b).encode(),headers={'content-type':'application/json','user-agent':'research-client'})
    return json.load(urllib.request.urlopen(r,timeout=120))
cv=rq({"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]})['result']
head=int(rq({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
logs=[]; b=start; errs=0
while b<=head:
    e=min(b+step-1,head)
    x=rq({"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"address":PM,"fromBlock":hex(b),"toBlock":hex(e)}]})
    if 'error' in x:
        errs+=1; time.sleep(1)
        if errs>20: break
        continue
    logs+=x['result']; b=e+1
c=collections.Counter(l['topics'][0] for l in logs)
cv2=rq({"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]})['result']
json.dump({'client':[cv,cv2],'from':start,'to':head,'counts':c,'logs':logs},open(out,'w'))
print(cv,cv2,start,head,len(logs),dict(c),'lastBlock',max([int(l['blockNumber'],16) for l in logs] or [0]))
