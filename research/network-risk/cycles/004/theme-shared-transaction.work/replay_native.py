# Read-only replay of recent swaps that paid native value, with and without a sync left behind earlier in the same transaction.
# Method: eth_call at the parent block of the original transaction. The sender address gets the runtime code of the public,
# verified Simple7702Account (0xe6Cae83BdE06E4c305530e199D7217f42808555B, same address on all 21 networks) through a state
# override, which models an EIP-7702 delegated account. The call is executeBatch of
#   control: [ original call ]
#   test:    [ PoolManager.sync(token), original call ]
# sync ignores its caller (src/PoolManager.sol:279-288), so the test equals a sync made by anyone earlier in the transaction.
# Nothing is signed or sent.
import json, sys, time, concurrent.futures as cf
from lib import *
from config import CFG
T0='0x'+keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
ACC='0xe6Cae83BdE06E4c305530e199D7217f42808555B'
PROBE={r['chainId']:r for r in json.load(open('probe_chain.json'))}
def enc_batch(calls):
    head=u256(32)+u256(len(calls)); offs=[]; bodies=[]; off=32*len(calls)
    for t,v,d in calls:
        b=bytes.fromhex(d[2:] if d.startswith('0x') else d); body=adr(t)+u256(v)+u256(96)+u256(len(b))+b.hex().ljust(((len(b)+31)//32)*64,'0')
        offs.append(off); bodies.append(body); off+=len(body)//2
    return '0x'+sel('executeBatch((address,uint256,bytes)[])')+head+''.join(u256(o) for o in offs)+''.join(bodies)
def call(u,frm,data,block,code,gas):
    j=post(u,{'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':frm,'to':frm,'data':data,'gas':hex(gas)},hex(block),{frm:{'code':code}}]},timeout=60,tries=3)
    if 'error' in j:
        e=j['error']; d=e.get('data'); d=d if isinstance(d,str) else json.dumps(d)
        return {'ok':False,'msg':str(e.get('message'))[:120],'data':(d or '')[:600]}
    return {'ok':True}
def run(n, maxlogs=3000, per_sender=2, max_senders=14):
    cid=n['chainId']; c=CFG[cid]; pm=n['poolManager']; out={'chainId':cid,'name':n['name'],'results':[],'err':None}
    try:
        lu=c['logs']; head=int(rpc(lu,'eth_blockNumber',[]),16); chunk=c['chunk']; hi=head-2; logs=[]; req=0
        while len(logs)<maxlogs and req<40 and hi>0:
            lo=max(0,hi-chunk+1)
            try: l=rpc(lu,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
            except Exception as e:
                if chunk>50: chunk//=4; continue
                raise
            req+=1; logs+=l[::-1]; hi=lo-1
        txs={}
        for l in logs: txs.setdefault(l['transactionHash'],set()).add('0x'+l['topics'][2][-40:])
        out['txs']=len(txs); hashes=list(txs)[:900]
        su=[u for u in c['state']]+[n['rpc']]
        def gettx(h):
            for u in (lu,n['rpc']):
                try:
                    t=rpc(u,'eth_getTransactionByHash',[h],tries=2)
                    if t: return t
                except Exception: pass
            return None
        with cf.ThreadPoolExecutor(6) as ex: tl=list(ex.map(gettx,hashes))
        cand=[t for t in tl if t and t.get('to') and int(t.get('value','0x0'),16)>0 and t.get('type') not in ('0x7e','0x76','0x6a','0x68','0x69')]
        out['valueTxs']=len(cand); seen={}; picks=[]
        for t in cand:
            ss=tuple(sorted(txs[t['hash']])); k=(t['to'].lower(),ss)
            if seen.get(k,0)>=per_sender: continue
            if len(seen)>=max_senders and k not in seen: continue
            seen[k]=seen.get(k,0)+1; picks.append((t,ss))
        tok=PROBE[cid]['mc3']['token']; code=None
        for u in su:
            try: code=rpc(u,'eth_getCode',[ACC,'latest']); break
            except Exception: pass
        syncd='0x'+sel('sync(address)')+adr(tok)
        def sim(p):
            t,ss=p; b=int(t['blockNumber'],16)-1; gas=min(int(t['gas'],16)*2+300000, 25000000 if cid!=999 else 2900000); v=int(t['value'],16); res=None
            for u in su:
                try:
                    ctl=call(u,t['from'],enc_batch([(t['to'],v,t['input'])]),b,code,gas)
                    if not ctl['ok'] and ('missing trie' in ctl['msg'] or 'not available' in ctl['msg'] or 'state' in ctl['msg'].lower() and 'revert' not in ctl['msg'].lower() or 'header not found' in ctl['msg'] or 'unknown block' in ctl['msg'].lower()): res={'ctl':ctl}; continue
                    tst=call(u,t['from'],enc_batch([(pm,0,syncd),(t['to'],v,t['input'])]),b,code,gas) if ctl['ok'] else None
                    res={'ctl':ctl,'tst':tst,'url':u}; break
                except Exception as e: res={'ctl':{'ok':False,'msg':'EXC '+str(e)[:100],'data':''}}
            return dict(tx=t['hash'],to=t['to'].lower(),senders=list(ss),value=v,block=b+1,**(res or {}))
        with cf.ThreadPoolExecutor(4) as ex: out['results']=list(ex.map(sim,picks))
        out['token']=tok
    except Exception as e: out['err']=str(e)[:300]
    return out
if __name__=='__main__':
    nets=[n for n in NETS if not sys.argv[1:] or str(n['chainId']) in sys.argv[1:]]
    with cf.ThreadPoolExecutor(7) as ex: res=list(ex.map(run,nets))
    old={}
    try: old={r['chainId']:r for r in json.load(open('replay_native.json'))}
    except Exception: pass
    for r in res: old[r['chainId']]=r
    json.dump(list(old.values()),open('replay_native.json','w'),indent=1)
    for r in res:
        print(r['chainId'],r['name'],'txs',r.get('txs'),'with value',r.get('valueTxs'),'err',r['err'])
        for x in r['results']:
            c=x.get('ctl') or {}; t=x.get('tst')
            v='control failed: '+(c.get('msg','')+' '+c.get('data','')[:60]) if not c.get('ok') else ('SAME (ok with stale sync)' if t['ok'] else 'REVERTS with stale sync: '+('NonzeroNativeValue ' if 'b0ec849e' in t['data'] else '')+t['msg'][:50]+' '+t['data'][:90])
            print('    to %s senders %s  %s'%(x['to'],','.join(s[:10] for s in x['senders']),v))
