# Read-only. Same targets and sixteen shapes as stub_sweep.py, sent as top-level eth_call with
# from = PoolManager address (balance overridden), to compare with the forwarding-stub answers.
# usage: toplevel.py <chainId> <stub_sweep_out.json> <out.json>
import sys, json
src=open('stub_sweep.py').read().split("block=rpc('eth_blockNumber',[])['result']")[0]
cid=int(sys.argv[1]); exec(src)
prev=json.load(open(sys.argv[2])); block=prev['block']
stub={r['target']:r for r in prev['results']}
out=[]; diffs=[]
for t in targets:
    batch=[]
    for k,(name,data,val) in enumerate(shapes):
        batch.append({'jsonrpc':'2.0','id':k,'method':'eth_call','params':[{'from':PM,'to':t,'data':'0x'+data.hex(),'value':hex(val),'gas':hex(3_000_000)},block,{PM:{'code':code,'balance':hex(10**20)}}]})
    r=post(batch)
    if isinstance(r,dict): r=[dict(post(b),id=b['id']) for b in batch]
    r={x['id']:x for x in r}
    row=dict(target=t,shapes=[])
    for k,(name,data,val) in enumerate(shapes):
        x=r[k]; ok=1 if 'result' in x else 0; ret=bytes.fromhex(x['result'][2:]) if ok else bytes.fromhex(((x.get('error') or {}).get('data') or '0x')[2:])
        row['shapes'].append(dict(shape=name,ok=ok,retLen=len(ret),ret=ret[:64].hex(),err=None if ok else str(x.get('error'))[:100]))
        s=stub.get(t)
        if s and 'shapes' in s:
            ss=s['shapes'][k]
            if (ss['ok'],ss['retLen'],ss['ret'])!=(ok,len(ret),ret[:64].hex()):
                diffs.append(dict(target=t,shape=name,stub=[ss['ok'],ss['retLen'],ss['ret'][:64]],top=[ok,len(ret),ret[:64].hex(),row['shapes'][-1]['err']]))
    out.append(row)
json.dump(dict(chainId=cid,block=block,results=out,diffs=diffs),open(sys.argv[3],'w'),indent=0)
print('targets',len(out),'diffs',len(diffs))
for d in diffs: print(d)
