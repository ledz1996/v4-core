# Read-only replay of recent token-input swaps through the canonical Universal Router with this state left behind earlier in
# the same transaction: sync(X) for the input token X, followed by a plain transfer of 1 unit of X to the PoolManager
# (synced reserves lower than the balance when the router acts). eth_simulateV1 at the parent block, sender code overridden
# with the public Simple7702Account, batch = [PoolManager.sync(X), X.transfer(PoolManager, 1), original call].
# Compared with the control run: every Transfer log other than the 1 unit donation must be the same if the router's own
# sync replaces the stale value.
import json, sys, concurrent.futures as cf
from lib import *
from config import CFG
from replay_native import enc_batch, ACC, T0
TR='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def sim(u,frm,data,block,code,gas):
    p={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'stateOverrides':{frm:{'code':code}},'calls':[{'from':frm,'to':frm,'data':data,'gas':hex(gas)}]}],'validation':False},hex(block)]}
    j=post(u,p,timeout=90,tries=3)
    if 'error' in j: return {'err':json.dumps(j['error'])[:160]}
    c=j['result'][0]['calls'][0]
    return {'status':c.get('status'),'transfers':[(l['address'],l['topics'][1][-40:],l['topics'][2][-40:],l['data']) for l in (c.get('logs') or []) if l['topics'] and l['topics'][0]==TR and len(l['topics'])==3],'swaps':sum(1 for l in (c.get('logs') or []) if l['topics'] and l['topics'][0]==T0)}
def run(cid,u,want=8):
    n=net(cid); pm=n['poolManager']; urs={v.lower() for k,v in n['contracts'].items() if k.replace(' ',' ').startswith('Universal Router')}
    head=int(rpc(u,'eth_blockNumber',[]),16); chunk=min(CFG[cid]['chunk'],2000); hi=head-2; hashes=[]; seen=set(); req=0
    while len(hashes)<500 and req<12:
        lo=hi-chunk+1
        try: l=rpc(u,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
        except Exception: chunk//=4; req+=1; continue
        req+=1; hi=lo-1
        for x in l[::-1]:
            if x['transactionHash'] not in seen and ('0x'+x['topics'][2][-40:]) in urs: seen.add(x['transactionHash']); hashes.append(x['transactionHash'])
    code=rpc(u,'eth_getCode',[ACC,'latest']); out=[]
    for h in hashes[:60]:
        if len(out)>=want: break
        try:
            t=rpc(u,'eth_getTransactionByHash',[h]); 
            if int(t['value'],16)!=0 or t['to'].lower() not in urs: continue
            rc=rpc(u,'eth_getTransactionReceipt',[h]); X=None
            for l in rc['logs']:
                if l['topics'] and l['topics'][0]==TR and len(l['topics'])==3 and l['topics'][2][-40:]==pm[2:].lower(): X=l['address']; break
            if not X: continue
            b=int(t['blockNumber'],16)-1; gas=min(int(t['gas'],16)*2+400000,28000000)
            ctl=sim(u,t['from'],enc_batch([(t['to'],0,t['input'])]),b,code,gas)
            tst=sim(u,t['from'],enc_batch([(pm,0,'0x'+sel('sync(address)')+adr(X)),(X,0,'0x'+sel('transfer(address,uint256)')+adr(pm)+u256(1)),(t['to'],0,t['input'])]),b,code,gas)
            if 'err' in ctl or 'err' in tst or ctl['status']!='0x1': out.append(dict(tx=h,token=X,note='control failed or error',ctl=ctl.get('status') or ctl.get('err'),tst=tst.get('status') or tst.get('err'))); continue
            don=(X.lower(),t['from'][2:].lower().rjust(40,'0'),pm[2:].lower(),'0x'+u256(1))
            rest=[x for x in tst['transfers'] if (x[0].lower(),x[1],x[2],x[3])!=don] if tst['status']=='0x1' else None
            out.append(dict(tx=h,token=X,block=b+1,control=ctl['status'],test=tst['status'],sameTransfers=(rest==ctl['transfers']) if rest is not None else None,nTransfers=len(ctl['transfers'])))
        except Exception as e: out.append(dict(tx=h,note='EXC '+str(e)[:100]))
    return dict(chainId=cid,url=u,results=out)
if __name__=='__main__':
    res=[]
    for cid,u in ((8453,'https://mainnet.base.org/'),(1868,'https://rpc.soneium.org'),(42161,'https://arb1.arbitrum.io/rpc'),(1,'https://ethereum-rpc.publicnode.com')):
        try: r=run(cid,u)
        except Exception as e: r=dict(chainId=cid,err=str(e)[:200],results=[])
        res.append(r); print(cid,r.get('err',''))
        for x in r['results']: print('   ',{k:(v if k!='tx' else v[:14]) for k,v in x.items()})
    json.dump(res,open('replay_donation.json','w'),indent=1)
