import sys, json
sys.path.insert(0,'.')
import lazyreplay as L
from rpc import batch
U='https://rpc.mainnet.arc.io'
D=json.load(open('raw/txs.json'))
h=sys.argv[1]; tx,rec=D['tx'][h]['tx'],D['tx'][h]['rec']; bn=int(tx['blockNumber'],16); idx=int(tx['transactionIndex'],16); blk=D['blocks'][str(bn)]
hs=blk['transactions'][:idx]; pairs=[]
for i in range(0,len(hs),5):
    ch=hs[i:i+5]; r=batch(U,[('eth_getTransactionByHash',[x]) for x in ch]+[('eth_getTransactionReceipt',[x]) for x in ch]); pairs+=[(r[j],r[len(ch)+j]) for j in range(len(ch))]
pairs.append((tx,rec))
print('block',bn,'index',idx,[ (p[0]['hash'][:10], p[0]['to'], int(p[1]['status'],16), len(p[1]['logs']), sum(1 for l in p[1]['logs'] if l['address'].lower()=='0x8366a39cc670b4001a1121b8f6a443a643e40951')) for p in pairs])
# rerun prefix, capturing the logs of every transaction
orig=L.run_once; per=[]
def spy(base, tx, rec, blk, cid=5042, pre=None):
    w,ok,ret=orig(base,tx,rec,blk,cid,pre); per.append((tx['hash'], ok, w.logs[:])); return w,ok,ret
L.run_once=spy
base,w,ok,ret,err,rounds,notes=L.replay_prefix(U,pairs,blk)
last={}
for hh,ok,lg in per: last[hh]=(ok,lg)
for p in pairs:
    ok,lg=last[p[0]['hash']]
    rl=[(l['address'].lower(),[x.lower() for x in l['topics']],l['data'].lower()) for l in p[1]['logs']]
    ol=[('0x%040x'%a,['0x%064x'%t for t in tp],'0x'+d.hex()) for a,tp,d in lg]
    print(p[0]['hash'][:12], 'status', int(p[1]['status'],16), int(bool(ok)), 'logs equal', rl==ol, len(rl), len(ol))
print(err, notes)
