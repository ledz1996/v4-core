# Read-only. Repeat the sweep for targets that exhausted the batch gas: one shape per eth_call, 3,000,000 gas.
import sys, json
sys.argv=[sys.argv[0]]+sys.argv[1:]
import importlib.util, types
src=open('stub_sweep.py').read().split("block=rpc('eth_blockNumber',[])['result']")[0]
cid=int(sys.argv[1]); out=sys.argv[2]
exec(src)
prev=json.load(open(sys.argv[3]))
block=prev['block']; res=[]
for r in prev['results']:
    if 'error' not in r: continue
    t=r['target']; row=dict(target=t,shapes=[])
    for name,data,val in shapes:
        calls=[(PM,0,GEB),(t,val,data),(PM,0,GEB)]
        body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':EOA,'to':PM,'data':'0x'+enc_calls(calls).hex(),'value':hex(val),'gas':hex(3_000_000)},block,{PM:{'code':code,'balance':hex(10**20)},EOA:{'balance':hex(10**20)}}]}
        x=post(body)
        if 'result' not in x: row['shapes'].append(dict(shape=name,ok=0,err=str(x.get('error'))[:80])); continue
        d=dec(x['result']); ok,ret=d[1]
        row['shapes'].append(dict(shape=name,ok=ok,retLen=len(ret),ret=ret[:40].hex(),balDelta=int.from_bytes(d[2][1],'big')-int.from_bytes(d[0][1],'big')))
    res.append(row)
    print(t,[(s['shape'],'ret%d'%s.get('retLen',-1),s.get('ret','')[:16]) for s in row['shapes'] if s['ok']] or 'fails on all 16',flush=True)
json.dump(dict(chainId=cid,block=block,results=res),open(out,'w'))
