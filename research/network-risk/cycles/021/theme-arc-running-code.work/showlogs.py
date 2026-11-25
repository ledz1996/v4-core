import sys, json
sys.path.insert(0,'.')
import lazyreplay as L
D=json.load(open('raw/txs.json'))
h=sys.argv[1]; tx,rec=D['tx'][h]['tx'],D['tx'][h]['rec']; blk=D['blocks'][str(int(tx['blockNumber'],16))]
base,w,ok,ret,err,rounds=L.replay('https://rpc.mainnet.arc.io',tx,rec,blk)
rl=[(l['address'].lower()[:8],l['topics'][0][:10] if l['topics'] else '-', ('%s>%s'%(l['topics'][1][-6:],l['topics'][2][-6:])) if len(l['topics'])>2 else '', l['data'][:20]) for l in rec['logs']]
ol=[('0x%040x'%a)[:8]+'|'+('0x%064x'%tp[0])[:10]+'|'+(('%06x>%06x'%(tp[1]&0xffffff,tp[2]&0xffffff)) if len(tp)>2 else '')+'|0x'+d.hex()[:18] for a,tp,d in w.logs]
for i in range(max(len(rl),len(ol))):
    a='|'.join(rl[i]) if i<len(rl) else ''; b=ol[i] if i<len(ol) else ''
    print('%-60s %-60s %s'%(a,b,'' if a==b else '<<'))
print(err, ok)
