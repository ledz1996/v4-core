from lib import *
import pickle,collections
logs=pickle.load(open('raw/mega_modliq_logs.pkl','rb'))
POSM='0x9ae0921e981aaa7308f176f8d4f9129b9247c89d'
def s256(x): 
    x=int(x,16); return x-(1<<256) if x>>255 else x
rem=[];add=[]
for l in logs:
    d=l['data'][2:]; ld=s256(d[128:192]); sender='0x'+l['topics'][2][-40:]
    (rem if ld<0 else add).append((l['transactionHash'],sender,ld,int(l['blockNumber'],16)))
print('removals',len(rem),'adds/zero',len(add),'senders of removals',collections.Counter(s for _,s,_,_ in rem).most_common(5))
txs=sorted(set(h for h,_,_,_ in rem))
print('distinct removal transactions',len(txs))
out=[]
for i in range(0,len(txs),40):
    part=txs[i:i+40]
    rc=batch([('eth_getTransactionReceipt',[h]) for h in part],MEGA)
    tx=batch([('eth_getTransactionByHash',[h]) for h in part],MEGA)
    for h,r,t in zip(part,rc,tx):
        r=r['result'];t=t['result']
        out.append(dict(h=h,gasUsed=int(r['gasUsed'],16),to=(t['to'] or '').lower(),ty=t['type'],gas=int(t['gas'],16),status=r['status'],nlogs=len(r['logs']),inlen=(len(t['input'])-2)//2,frm=t['from'],block=int(r['blockNumber'],16)))
pickle.dump(out,open('raw/mega_removal_txs.pkl','wb'))
byto=collections.defaultdict(list)
for o in out: byto[o['to']].append(o)
for to,v in sorted(byto.items(),key=lambda kv:-len(kv[1])):
    g=sorted(x['gasUsed'] for x in v)
    print(to,'n',len(v),'gasUsed min',g[0],'median',g[len(g)//2],'p90',g[int(len(g)*0.9)],'max',g[-1],'above 1,000,000:',sum(1 for x in g if x>1_000_000),'types',collections.Counter(x['ty'] for x in v))
pos=[o for o in out if o['to']==POSM]
g=sorted(o['gasUsed'] for o in pos)
print('PositionManager removals',len(g),'quantiles',[g[int(len(g)*q)] for q in (0,0.1,0.25,0.5,0.75,0.9,0.99)] if g else None, 'max',g[-1] if g else None)
print('deposit-type removal txs:',[o for o in out if o['ty']=='0x7e'][:5])
