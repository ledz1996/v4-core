# Lead L-464: merge the NodeReal log parts for sNVB, refetch failed ranges, and check them against archive state read from a different endpoint.
import sys,json,glob,time,collections,bisect
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
logs={k:[] for k in filters}; fails=[]; cover=[]
for f in sorted(glob.glob('raw/snvb_logs_nodereal_p*.json')):
    d=json.load(open(f)); cover.append((d['start'],d['upto']))
    for k in logs: logs[k]+=d['logs'][k]
    fails+=d['fails']
print('coverage',cover,'fails to refetch',len(fails))
still=[]
for k,b,e,_ in fails:
    ok=False
    for attempt in range(6):
        r=rpc(U,'eth_getLogs',[{"fromBlock":hex(b),"toBlock":hex(e),"address":TOK,"topics":filters[k]}],timeout=60,retries=0)
        if isinstance(r,dict) and isinstance(r.get('result'),list):
            logs[k]+=[{'b':int(l['blockNumber'],16),'tx':l['transactionHash'],'topics':l['topics'],'data':l['data'],'li':int(l['logIndex'],16)} for l in r['result']]; ok=True; break
        time.sleep(3)
    if not ok: still.append((k,b,e))
print('still failed',still)
for k in logs:
    seen=set(); u=[]
    for l in sorted(logs[k],key=lambda l:(l['b'],l['li'])):
        key=(l['tx'],l['li'])
        if key in seen: continue
        seen.add(key); u.append(l)
    logs[k]=u
print({k:len(v) for k,v in logs.items()})
# rebase series
reb=[(l['b'],l['li'],int(l['topics'][1],16),int(l['data'][2:66],16),int(l['data'][66:130],16),l['tx']) for l in logs['rebase']]
epochs=[r[2] for r in reb]
missing=sorted(set(range(min(epochs),max(epochs)+1))-set(epochs)) if epochs else []
print('rebase logs',len(reb),'epochs',min(epochs),max(epochs),'missing epochs',len(missing),missing[:20],'dups',len(epochs)-len(set(epochs)))
# payouts: transactions with a rebase log and a transfer out of the PoolManager
rtx={r[5] for r in reb}
outs=[(l['b'],l['li'],l['tx'],'0x'+l['topics'][2][-40:],int(l['data'],16)) for l in logs['out']]
ins=[(l['b'],l['li'],l['tx'],'0x'+l['topics'][1][-40:],int(l['data'],16)) for l in logs['in']]
pay=[o for o in outs if o[2] in rtx]
print('transfers out',len(outs),'in',len(ins),'out in a rebase transaction',len(pay))
bytx=collections.defaultdict(lambda:{'out':0,'in':0,'to':set(),'b':0})
for o in pay: bytx[o[2]]['out']+=o[4]; bytx[o[2]]['to'].add(o[3]); bytx[o[2]]['b']=o[0]
for i in ins:
    if i[2] in bytx: bytx[i[2]]['in']+=i[4]
rows=[{'tx':t,'block':v['b'],'out':str(v['out']),'in':str(v['in']),'net_out':str(v['out']-v['in']),'to':sorted(v['to'])} for t,v in sorted(bytx.items(),key=lambda kv:kv[1]['b'])]
for r in rows[:12]: print(r)
tot=sum(int(r['net_out']) for r in rows)
print('rebase transactions with PoolManager outflow',len(rows),'net outflow',tot/1e9,'sNVB')
# state check against archive balances read from another endpoint (raw/snvb_grid.json)
grid=json.load(open('raw/snvb_grid.json'))
idx_series=sorted((r[0],r[1],r[4]) for r in reb)
def index_at(b,li):
    i=bisect.bisect_right(idx_series,(b,li,1<<300))-1
    return idx_series[i][2] if i>=0 else None
ev=sorted([(o[0],o[1],-o[4]) for o in outs]+[(i[0],i[1],i[4]) for i in ins])
checks=[]
for (b0,bal0,i0,_),(b1,bal1,i1,_) in zip(grid,grid[1:]):
    if not isinstance(bal0,int) or not isinstance(bal1,int): continue
    s=0.0; n=0
    for b,li,amt in ev:
        if b0<b<=b1:
            ix=index_at(b,li)
            if ix: s+=amt/ix; n+=1
    want=bal1/i1-bal0/i0
    checks.append({'from':b0,'to':b1,'nTransfers':n,'stateDelta':want,'logDelta':s,'diff':want-s})
bad=[c for c in checks if abs(c['diff'])>1e-6*max(1.0,abs(c['stateDelta']))+1e-6]
print('grid intervals',len(checks),'mismatching',len(bad))
for c in bad[:10]: print(c)
json.dump({'coverage':cover,'stillFailed':still,'counts':{k:len(v) for k,v in logs.items()},'epochMin':min(epochs),'epochMax':max(epochs),'missingEpochs':missing,'rebaseTxWithOutflow':rows,'netOutflowInRebaseTx':str(tot),'gridChecks':checks,'gridMismatch':bad},open('raw/snvb_result.json','w'),indent=1)
