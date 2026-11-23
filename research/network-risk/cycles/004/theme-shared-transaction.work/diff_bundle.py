# Compare the logs of the control run and the test run of one replayed handleOps transaction (see replay_bundles.py),
# with native transfers traced as logs. Read only.
import json, sys
from lib import *
from replay_native import enc_batch, ACC, PROBE, T0
TR='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def sim(u,frm,data,block,code,gas):
    p={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'stateOverrides':{frm:{'code':code}},'calls':[{'from':frm,'to':frm,'data':data,'gas':hex(gas)}]}],'validation':False,'traceTransfers':True},hex(block)]}
    j=post(u,p,timeout=90,tries=3)
    if 'error' in j: raise Exception(json.dumps(j['error'])[:300])
    return j['result'][0]['calls'][0]
def summarize(c):
    out=[]
    for l in c.get('logs') or []:
        t=l['topics']
        if t[0]==TR and len(t)==3: out.append(('transfer',l['address'][:12],'0x'+t[1][-40:][:10],'->','0x'+t[2][-40:][:10],int(l['data'],16) if l['data']!='0x' else 0))
        elif t[0]==T0: out.append(('PM.Swap sender','0x'+t[2][-40:][:10]))
        else: out.append(('log',l['address'][:12],t[0][:10]))
    return out
if __name__=='__main__':
    cid=int(sys.argv[1]); u=sys.argv[2]; h=sys.argv[3]; n=net(cid); pm=n['poolManager']
    t=rpc(u,'eth_getTransactionByHash',[h]); b=int(t['blockNumber'],16)-1; gas=min(int(t['gas'],16)*2+500000,28000000)
    code=rpc(u,'eth_getCode',[ACC,'latest']); tok=PROBE[cid]['mc3']['token']; syncd='0x'+sel('sync(address)')+adr(tok)
    c=sim(u,t['from'],enc_batch([(t['to'],0,t['input'])]),b,code,gas); x=sim(u,t['from'],enc_batch([(pm,0,syncd),(t['to'],0,t['input'])]),b,code,gas)
    json.dump({'tx':h,'control':c,'test':x},open('diff_%d_%s.json'%(cid,h[:12]),'w'))
    print('tx',h,'bundler',t['from'],'block',b+1,'gasUsed control',int(c['gasUsed'],16),'test',int(x['gasUsed'],16))
    a=summarize(c); bb=summarize(x)
    print('--- control (%d logs)'%len(a)); [print('  ',i) for i in a]
    print('--- test (%d logs)'%len(bb)); [print('  ',i) for i in bb]
