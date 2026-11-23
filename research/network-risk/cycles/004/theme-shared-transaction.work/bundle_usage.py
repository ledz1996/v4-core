# Per network: how recent transactions that contain a PoolManager Swap event were carried.
#  - top level target of the transaction (EntryPoint versions, PBHEntryPoint, Multicall3, known settlement contracts)
#  - transaction type (0x4 = EIP-7702 set code transaction, 0x76 = Tempo transaction, 0x7e = deposit, ...)
#  - how many senders carry an EIP-7702 delegation designator (code 0xef0100 || address)
#  - how many handleOps transactions hold more than one UserOperation event (several operations in one transaction)
#  - whether the four EntryPoint addresses hold the same code as on Ethereum
# Read only.
import json, sys, hashlib, concurrent.futures as cf
from lib import *
from config import CFG
T0='0x'+keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
UOE='0x'+keccak256(b'UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)').hex()
EP={'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789':'EntryPoint v0.6','0x0000000071727de22e5e9d8baf0edac6f37da032':'EntryPoint v0.7','0x4337084d9e255ff0702461cf8895ce9e3b5ff108':'EntryPoint v0.8','0x433709009b8330fda32311df1c2afa402ed8d009':'EntryPoint v0.9'}
KNOWN=dict(EP); KNOWN.update({'0x0000000000a21818ee9f93bb4f2aaad305b5397c':'World Chain PBHEntryPoint','0xca11bde05977b3631167028862be2a173976ca11':'Multicall3','0x9008d19f58aabd9ed0d60971565aa8510560ab41':'CoW GPv2Settlement','0x111111125421ca6dc452d289314280a0f8842a65':'1inch AggregationRouterV6','0xbeb0b0623f66be8ce162ebdfa2ec543a522f4ea6':'Bebop JamSettlement','0xbbbbbbb520d69a9775e85b458c58c648259fad5f':'Bebop settlement','0x00000011f84b9aa48e5f8aa8b9897600006289be':'UniswapX V2DutchOrderReactor','0x000000001ec5656dcdb24d90dfa42742738de729':'UniswapX PriorityOrderReactor','0x1bd1aadc9e230626c44a139d7e70d842749351eb':'UniswapX reactor (Arbitrum)','0x924a9f036260ddd5808007e1aa95f08ed08aa569':'Across MulticallHandler','0x0000000000001ff3684f28c67538d4d072c22734':'0x AllowanceHolder','0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae':'LI.FI Diamond','0x6a000f20005980200259b80c5102003040001068':'Velora AugustusV6'})
REFH={}
def codehash(u,a):
    try: return hashlib.sha256(bytes.fromhex(rpc(u,'eth_getCode',[a,'latest'])[2:])).hexdigest()[:16]
    except Exception as e: return 'ERR'
def run(n,cap=600):
    cid=n['chainId']; c=CFG[cid]; pm=n['poolManager']; out={'chainId':cid,'name':n['name'],'err':None}
    try:
        out['epSameAsEthereum']={v:codehash(n['rpc'],a)==REFH[a] for a,v in EP.items()}
        lu=c['logs']; head=int(rpc(lu,'eth_blockNumber',[]),16); chunk=c['chunk']; hi=head-2; hashes=[]; req=0; seen=set()
        while len(hashes)<cap and req<40 and hi>0:
            lo=max(0,hi-chunk+1)
            try: l=rpc(lu,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(lo),'toBlock':hex(hi)}],timeout=60,tries=2)
            except Exception as e:
                if chunk>50: chunk//=4; continue
                raise
            req+=1; hi=lo-1
            for x in l[::-1]:
                if x['transactionHash'] not in seen: seen.add(x['transactionHash']); hashes.append(x['transactionHash'])
        hashes=hashes[:cap]; out['txs']=len(hashes); out['blocks']=[hi+1,head]
        def gettx(h):
            for u in (lu,n['rpc']):
                try:
                    t=rpc(u,'eth_getTransactionByHash',[h],tries=2)
                    if t: return t
                except Exception: pass
        with cf.ThreadPoolExecutor(6) as ex: tl=[t for t in ex.map(gettx,hashes) if t]
        types={}; tos={}; eptx=[]
        for t in tl:
            types[t.get('type')]=types.get(t.get('type'),0)+1
            k=KNOWN.get((t.get('to') or '').lower())
            if k: tos[k]=tos.get(k,0)+1
            if (t.get('to') or '').lower() in EP or (t.get('to') or '').lower()=='0x0000000000a21818ee9f93bb4f2aaad305b5397c': eptx.append(t['hash'])
        out['types']=types; out['knownTargets']=tos
        froms=list({t['from'] for t in tl})[:200]
        def deleg(a):
            try: return rpc(n['rpc'],'eth_getCode',[a,'latest'])[:8]=='0xef0100'
            except Exception: return None
        with cf.ThreadPoolExecutor(6) as ex: d=list(ex.map(deleg,froms))
        out['sendersChecked']=len(froms); out['sendersDelegated']=sum(1 for x in d if x)
        multi=[]
        def nops(h):
            try:
                r=rpc(lu,'eth_getTransactionReceipt',[h],tries=2); return (h,sum(1 for l in r['logs'] if l['topics'] and l['topics'][0]==UOE))
            except Exception: return (h,None)
        with cf.ThreadPoolExecutor(6) as ex: k=list(ex.map(nops,eptx[:80]))
        out['handleOpsTxs']=len(eptx); out['handleOpsWithSeveralOps']=[(h,c2) for h,c2 in k if c2 and c2>1][:5]; out['opsPerTx']=sorted([c2 for h,c2 in k if c2],reverse=True)[:10]
    except Exception as e: out['err']=str(e)[:300]
    return out
if __name__=='__main__':
    for a in EP: REFH[a]=codehash(net(1)['rpc'],a)
    nets=[n for n in NETS if not sys.argv[1:] or str(n['chainId']) in sys.argv[1:]]
    with cf.ThreadPoolExecutor(7) as ex: res=list(ex.map(run,nets))
    old={}
    try: old={r['chainId']:r for r in json.load(open('bundle_usage.json'))}
    except Exception: pass
    for r in res: old[r['chainId']]=r
    json.dump(list(old.values()),open('bundle_usage.json','w'),indent=1)
    for r in res:
        print(r['chainId'],r['name'],'txs',r.get('txs'),'types',r.get('types'),'err',r['err'])
        print('    EP code same as Ethereum:',r.get('epSameAsEthereum'))
        print('    targets:',r.get('knownTargets'),'| delegated senders %s of %s'%(r.get('sendersDelegated'),r.get('sendersChecked')),'| handleOps txs',r.get('handleOpsTxs'),'ops per tx',r.get('opsPerTx'),'multi',[(h[:12],c) for h,c in (r.get('handleOpsWithSeveralOps') or [])])
