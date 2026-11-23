import sys,json,time
from lib import *
lo=int(sys.argv[1]); hi=int(sys.argv[2]); out=open(sys.argv[3],'a')
TH=0.0018
n=lo; done=0
while n<=hi:
    calls=[]
    k=n
    for i in range(100):
        last=min(k+255,hi); cnt=last-k+1
        if cnt<=0: break
        calls.append(('eth_feeHistory',[hex(cnt),hex(last),[]])); k=last+1
    for attempt in range(6):
        try:
            r=batch(calls,MEGA)
            if all('result' in x for x in r): break
        except Exception as e: pass
        time.sleep(2*(attempt+1))
    else:
        out.write(json.dumps({'fail':[n,k]})+'\n'); n=k; continue
    for x in r:
        res=x['result']; ob=int(res['oldestBlock'],16)
        for j,g in enumerate(res['gasUsedRatio']):
            if g>=TH: out.write(json.dumps({'b':ob+j,'r':g})+'\n')
    out.write(json.dumps({'done':k-1})+'\n'); out.flush()
    n=k
out.write(json.dumps({'finished':hi})+'\n'); out.close()
