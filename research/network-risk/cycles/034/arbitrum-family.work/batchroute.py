import json,subprocess,sys,collections
U={'4663':'https://rpc.mainnet.chain.robinhood.com','42161':'https://arb1.arbitrum.io/rpc','99901':'https://rpc.elysium.kinetiq.xyz'}
N=int(sys.argv[2]); out={}
for c,u in U.items():
    mixed=0; seen=collections.Counter(); per=[]
    body=json.dumps([{"jsonrpc":"2.0","id":i,"method":"web3_clientVersion","params":[]} for i in range(8)])
    for k in range(N):
        r=subprocess.run(['curl','-s','--max-time','30','-X','POST','-H','content-type: application/json','--data',body,u],capture_output=True,text=True).stdout
        try: vs=[x.get('result') for x in json.loads(r)]
        except Exception: vs=['ERR:'+r[:80]]
        s=set(vs); seen.update(vs)
        if len(s)>1: mixed+=1; per.append(vs)
    out[c]={'batches':N,'mixed':mixed,'builds':dict(seen),'mixedExamples':per[:3]}
    print(c,json.dumps(out[c]))
json.dump(out,open(sys.argv[1],'w'),indent=1)
