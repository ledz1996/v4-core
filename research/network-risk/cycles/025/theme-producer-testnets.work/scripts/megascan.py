import sys,json
sys.path.insert(0,'scripts'); from rpc import call
U=sys.argv[1]; T=sys.argv[2]; out=sys.argv[3]
cv=call(U,'web3_clientVersion',[])['result']
bn=int(call(U,'eth_blockNumber',[])['result'],16)
logs=[]; step=2_000_000; b=0; errs=[]
while b<=bn:
    e=min(bn,b+step-1)
    r=call(U,'eth_getLogs',[{"fromBlock":hex(b),"toBlock":hex(e),"topics":[T]}])
    if 'error' in r:
        errs.append([b,e,r['error']]); step=max(step//4,1000); continue
    logs+=r['result']; b=e+1
cv2=call(U,'web3_clientVersion',[])['result']
json.dump({"client":[cv,cv2],"to":bn,"errors":errs,"logs":logs},open(out,'w'))
print(cv,cv2,bn,len(logs),len(errs))
