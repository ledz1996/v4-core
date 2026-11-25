import json,urllib.request,sys,time
U=sys.argv[1]; PM='0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
def rpc(m,p):
    for i in range(6):
        r=urllib.request.Request(U,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'probe'})
        try:
            j=json.load(urllib.request.urlopen(r,timeout=90))
            if 'error' in j: raise Exception(j['error'])
            return j['result']
        except Exception as e: err=e; time.sleep(2+3*i)
    raise err
lo=int(sys.argv[2]); hi=int(rpc('eth_blockNumber',[]),16); step=int(sys.argv[3])
logs=[]
b=lo
while b<=hi:
    e=min(hi,b+step-1)
    try: logs+=rpc('eth_getLogs',[{'address':PM,'fromBlock':hex(b),'toBlock':hex(e)}]); b=e+1
    except Exception as x:
        if step>100: step//=4; continue
        raise
by={}
for l in logs: by[l['topics'][0]]=by.get(l['topics'][0],0)+1
print(json.dumps({'from':lo,'to':hi,'logs':len(logs),'byTopic':by,'blocks':sorted({int(l['blockNumber'],16) for l in logs})},indent=1))
