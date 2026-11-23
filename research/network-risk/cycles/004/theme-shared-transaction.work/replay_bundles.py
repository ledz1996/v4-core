# Read-only replay of recent ERC-4337 handleOps transactions that contained a PoolManager swap, with and without a sync
# made earlier in the same transaction. eth_simulateV1 at the parent block; the bundler address gets the code of the public
# Simple7702Account through a state override and calls executeBatch of [handleOps] (control) or [PoolManager.sync(token), handleOps] (test).
# The logs of both runs are compared: UserOperationEvent.success per operation and the number of PoolManager Swap events.
import json, sys, concurrent.futures as cf
from lib import *
from config import CFG
from replay_native import enc_batch, ACC, PROBE, T0
UOE='0x'+keccak256(b'UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)').hex()
EPS={'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789':'v0.6','0x0000000071727de22e5e9d8baf0edac6f37da032':'v0.7','0x4337084d9e255ff0702461cf8895ce9e3b5ff108':'v0.8','0x433709009b8330fda32311df1c2afa402ed8d009':'v0.9'}
def sim(u,frm,data,block,code,gas):
    p={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'stateOverrides':{frm:{'code':code}},'calls':[{'from':frm,'to':frm,'data':data,'gas':hex(gas)}]}],'validation':False},hex(block)]}
    j=post(u,p,timeout=90,tries=3)
    if 'error' in j: return {'err':json.dumps(j['error'])[:200]}
    c=j['result'][0]['calls'][0]; logs=c.get('logs') or []
    ops=[(l['topics'][1][:12],l['topics'][2][-40:],int(l['data'][2+64:2+128],16)) for l in logs if l['topics'][0]==UOE]
    return {'status':c.get('status'),'ret':(c.get('returnData') or '')[:140],'err2':json.dumps(c.get('error'))[:160] if c.get('error') else None,'ops':ops,'swaps':sum(1 for l in logs if l['topics'][0]==T0),'swapSenders':sorted({'0x'+l['topics'][2][-40:] for l in logs if l['topics'][0]==T0})}
def run(cid,u,cap=1500,nsim=30):
    n=net(cid); c=CFG[cid]; pm=n['poolManager']; lu=c['logs']
    head=int(rpc(u,'eth_blockNumber',[]),16); chunk=c['chunk']; hi=head-2; hashes=[]; seen=set(); req=0
    while len(hashes)<cap and req<30:
        lo=hi-chunk+1
        try: l=rpc(lu,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
        except Exception as e:
            try: l=rpc(u,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
            except Exception as e2:
                chunk//=4; continue
        req+=1; hi=lo-1
        for x in l[::-1]:
            if x['transactionHash'] not in seen: seen.add(x['transactionHash']); hashes.append(x['transactionHash'])
    def gettx(h):
        try: return rpc(u,'eth_getTransactionByHash',[h],tries=2)
        except Exception: return None
    with cf.ThreadPoolExecutor(6) as ex: tl=[t for t in ex.map(gettx,hashes[:cap]) if t and (t.get('to') or '').lower() in EPS]
    code=rpc(u,'eth_getCode',[ACC,'latest']); tok=PROBE[cid]['mc3']['token']; syncd='0x'+sel('sync(address)')+adr(tok); out=[]
    def one(t):
        b=int(t['blockNumber'],16)-1; gas=min(int(t['gas'],16)*2+500000,28000000)
        ctl=sim(u,t['from'],enc_batch([(t['to'],0,t['input'])]),b,code,gas)
        tst=sim(u,t['from'],enc_batch([(pm,0,syncd),(t['to'],0,t['input'])]),b,code,gas)
        return dict(tx=t['hash'],ep=EPS[t['to'].lower()],block=b+1,ctl=ctl,tst=tst)
    with cf.ThreadPoolExecutor(3) as ex: out=list(ex.map(one,tl[:nsim]))
    return dict(chainId=cid,url=u,token=tok,handleOpsTxs=len(tl),results=out)
if __name__=='__main__':
    res=[]
    for cid,u in ((1868,'https://rpc.soneium.org'),(8453,'https://mainnet.base.org/'),(480,'https://480.rpc.thirdweb.com'),(1,'https://ethereum-rpc.publicnode.com'),(42161,'https://arb1.arbitrum.io/rpc')):
        if sys.argv[1:] and str(cid) not in sys.argv[1:]: continue
        try: r=run(cid,u)
        except Exception as e: r=dict(chainId=cid,err=str(e)[:300],results=[])
        res.append(r)
        print(cid,'handleOps txs with a swap',r.get('handleOpsTxs'),r.get('err',''))
        for x in r['results']:
            c,t=x['ctl'],x['tst']
            if 'err' in c or 'err' in t: print('   ',x['tx'][:14],x['ep'],'ERR',c.get('err'),t.get('err')); continue
            cs=[o[2] for o in c['ops']]; ts=[o[2] for o in t['ops']]
            print('   ',x['tx'][:14],x['ep'],'control: status',c['status'],'ops ok',cs,'swaps',c['swaps'],'| test: status',t['status'],'ops ok',ts,'swaps',t['swaps'],'| senders',[s[:10] for s in c['swapSenders']],'' if (cs==ts and c['swaps']==t['swaps']) else '<== DIFFERENT '+str(t.get('ret'))+str(t.get('err2')))
    old={}
    try: old={r['chainId']:r for r in json.load(open('replay_bundles.json'))}
    except Exception: pass
    for r in res: old[r['chainId']]=r
    json.dump(list(old.values()),open('replay_bundles.json','w'),indent=1)
