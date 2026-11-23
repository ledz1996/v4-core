# Tempo: state of every pooled TIP-20 token as the PoolManager sees it (read-only).
import json
from lib import *
cid=4217; n=net(cid); u=n['rpc']; pm=n['poolManager']
REG='0x403c000000000000000000000000000000000000'; SINK='0x7e57000000000000000000000000000000000505'
toks=[t for t in json.load(open('tempo_bal.json')) if t['token'].startswith('0x20c0')]
blk=rpc(u,'eth_blockNumber',[])['result']
def c(to,data,frm=None):
    tx={'to':to,'data':'0x'+data}
    if frm: tx['from']=frm
    r=rpc(u,'eth_call',[tx,blk]); return r.get('result') if 'result' in r else 'ERR '+json.dumps(r.get('error'))[:90]
rows=[]
for t in toks:
    a=t['token']
    paused=c(a,sel('paused()')); pol=c(a,sel('transferPolicyId()'))
    pid=int(pol,16) if pol and pol.startswith('0x') and len(pol)>2 else None
    auth=c(REG,cd('isAuthorized(uint64,address)',pid,pm)) if pid is not None else None
    xfer=c(a,cd('transfer(address,uint256)',SINK,1),pm) if (t['bal'] or 0)>0 else 'no balance'
    bal=c(a,cd('balanceOf(address)',pm))
    quote=c(a,sel('quoteToken()')); cap=c(a,sel('supplyCap()')); cur=c(a,sel('currency()'))
    rows.append(dict(token=a,sym=t['sym'],bal=int(bal,16) if bal.startswith('0x') else bal,paused=paused[-1:] if paused.startswith('0x') else paused,policy=pid,authorized=auth[-1:] if auth and auth.startswith('0x') else auth,transfer1=xfer[-1:] if xfer.startswith('0x') else xfer,quote=quote[-40:] if quote.startswith('0x') else quote))
    r=rows[-1]; print(r['token'],r['sym'][:10].ljust(10),str(r['bal']).rjust(16),'paused',r['paused'],'policy',r['policy'],'auth',r['authorized'],'transfer1',r['transfer1'][:60],'quote',r['quote'][-8:])
json.dump({'block':blk,'rows':rows},open('raw/t4_tip20.json','w'),indent=1)
