"""usage: alllogs.py rpc addr from to step out.json  -- all logs of addr, adaptive range"""
import sys,json
sys.path.insert(0,'scripts'); from rpc import call
U,A,F,Tb,S,O=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),sys.argv[6]
cv=call(U,'web3_clientVersion',[]).get('result'); logs=[];errs=[];b=F;step=S
while b<=Tb:
    e=min(Tb,b+step-1)
    r=call(U,'eth_getLogs',[{"fromBlock":hex(b),"toBlock":hex(e),"address":A}])
    if 'error' in r:
        errs.append([b,e,r['error']]); 
        if step==1: b+=1
        step=max(step//4,1); continue
    logs+=r['result']; b=e+1
json.dump({"client":[cv,call(U,'web3_clientVersion',[]).get('result')],"addr":A,"from":F,"to":Tb,"errors":errs[:50],"nerr":len(errs),"logs":logs},open(O,'w'))
print(len(logs),len(errs))
