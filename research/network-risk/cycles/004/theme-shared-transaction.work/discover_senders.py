# Tally the `sender` topic of recent PoolManager Swap events per network. The sender is the contract that called swap,
# that is, the router that later has to pay the PoolManager. Read only (eth_getLogs).
import json, sys, time, concurrent.futures as cf
from lib import *
from config import CFG
T0='0x'+keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
def run(n, want=4000, maxreq=60):
    cid=n['chainId']; c=CFG[cid]; pm=n['poolManager']
    urls=[c['logs']]+[u for u in c['state'] if u!=c['logs']]+[n['rpc']]
    out={'chainId':cid,'name':n['name'],'senders':{},'logs':0,'from':None,'to':None,'err':None}
    for u in urls:
        try:
            head=int(rpc(u,'eth_blockNumber',[]),16); chunk=c['chunk']; hi=head; got=0; req=0; tally={}; txs={}
            while got<want and req<maxreq and hi>0:
                lo=max(0,hi-chunk+1)
                try: logs=rpc(u,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
                except Exception as e:
                    if chunk>50: chunk//=4; continue
                    raise
                req+=1
                for l in logs:
                    s='0x'+l['topics'][2][-40:]; tally[s]=tally.get(s,0)+1; txs.setdefault(s,l['transactionHash'])
                got+=len(logs); hi=lo-1
                if req>=6 and got==0 and chunk<200000: chunk*=4
            out.update(senders=tally,logs=got,to=head,sample=txs,url=u); out['from']=hi+1
            if got: return out
        except Exception as e:
            out['err']=(out['err'] or '')+' | '+u+': '+str(e)[:120]
    return out
if __name__=='__main__':
    nets=[n for n in NETS if not sys.argv[1:] or str(n['chainId']) in sys.argv[1:]]
    with cf.ThreadPoolExecutor(10) as ex: res=list(ex.map(run,nets))
    old={}
    try: old={r['chainId']:r for r in json.load(open('senders.json'))}
    except Exception: pass
    for r in res: old[r['chainId']]=r
    json.dump(list(old.values()),open('senders.json','w'),indent=1)
    for r in res:
        print(r['chainId'],r['name'],'logs',r['logs'],'blocks',r['from'],r['to'],'err',r['err'])
        for s,k in sorted(r['senders'].items(),key=lambda x:-x[1])[:8]: print('    %s %d'%(s,k))
