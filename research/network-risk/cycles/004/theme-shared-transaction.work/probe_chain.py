# Per network, read only:
#  (1) code length at the addresses of contracts that put calls of several users into one transaction;
#  (2) one eth_call to Multicall3.aggregate3 that calls PoolManager.sync(token), then reads the synced currency and reserves
#      with exttload, then calls sync(address(0)) and reads the currency again. This shows that sibling calls made by one
#      contract inside one transaction meet the same transient map of the PoolManager and that sync leaves its values behind;
#  (3) a call to the BLS12-381 G1ADD precompile (0x0b) as a marker for the Prague instruction set.
import json, gzip, os, concurrent.futures as cf
from lib import *
from config import CFG
CUR='27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9'; RES='1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95'
WELL={
 'EntryPoint v0.6':'0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789',
 'EntryPoint v0.7':'0x0000000071727De22E5E9d8BAf0edAc6f37da032',
 'EntryPoint v0.8':'0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108',
 'EntryPoint v0.9':'0x433709009B8330FDa32311DF1C2AFA402eD8D009',
 'Multicall3':MC3,
 'CoW GPv2Settlement':'0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
 '1inch AggregationRouterV6':'0x111111125421cA6dc452d289314280a0f8842A65',
 'Bebop JamSettlement':'0xbeb0b0623f66bE8cE162EbDfA2ec543A522F4ea6',
 'Bebop PMM settlement':'0xbbbbbBB520d69a9775E85b458C58c648259FAD5F',
 'Across MulticallHandler':'0x924a9f036260DdD5808007E1AA95f08eD08aA569',
 'UniswapX V2DutchOrderReactor (mainnet address)':'0x00000011F84B9aa48e5f8aA8B9897600006289Be',
 'UniswapX PriorityOrderReactor (Base address)':'0x000000001Ec5656dcdB24D90DFa42742738De729',
 'UniswapX reactor (Arbitrum address)':'0x1bd1aAdc9E230626C44a139d7E70d842749351eb',
 'World Chain PBHEntryPoint':'0x0000000000A21818Ee9F93BB4f2AAad305b5397C',
 'Arc CallFrom precompile':'0x1800000000000000000000000000000000000003',
 'ERC-2771 style GelatoRelay1BalanceERC2771':'0xd8253782c45a12053594b9deB72d8e8aB2Fca54c',
 'Biconomy Nexus bootstrap / MEE EntryPoint':'0x0000000000000000000000000000000000000000',
}
def enc_agg3(calls):
    # aggregate3((address target,bool allowFailure,bytes callData)[])
    head=u256(32)+u256(len(calls)); offs=[]; bodies=[]; off=32*len(calls)
    for t,d in calls:
        b=bytes.fromhex(d); body=adr(t)+u256(1)+u256(96)+u256(len(b))+b.hex().ljust(((len(b)+31)//32)*64,'0')
        offs.append(off); bodies.append(body); off+=len(body)//2
    return '0x'+sel('aggregate3((address,bool,bytes)[])')+head+''.join(u256(o) for o in offs)+''.join(bodies)
def dec_agg3(h):
    b=bytes.fromhex(h[2:]); base=32; n=int.from_bytes(b[base:base+32],'big'); out=[]
    for i in range(n):
        o=base+32+int.from_bytes(b[base+32+32*i:base+64+32*i],'big')
        ok=int.from_bytes(b[o:o+32],'big'); po=o+int.from_bytes(b[o+32:o+64],'big'); ln=int.from_bytes(b[po:po+32],'big')
        out.append((ok,b[po+32:po+32+ln].hex()))
    return out
def token_for(cid):
    fn=os.path.join(HERE,'..','theme-balance-reconcile.work','raw','currencies_%d.json.gz'%cid)
    j=json.load(gzip.open(fn,'rt')); c=sorted(j['currencies'].items(),key=lambda x:-x[1])
    FALL={8453:['0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'],480:['0x4200000000000000000000000000000000000006'],196:['0xe538905cf8410324e03A5A23C1c177a474D59b2b','0x1E4a5963aBFD975d8c9021ce480b42188849D41d'],56:['0x55d398326f99059fF775485246999027B3197955']}
    return ([a for a,_ in c if int(a,16)!=0]+FALL.get(cid,[]))[:6]
def probe(n):
    cid=n['chainId']; u=n['rpc']; pm=n['poolManager']; out={'chainId':cid,'name':n['name']}
    try:
        out['block']=int(rpc(u,'eth_blockNumber',[]),16)
        try: out['client']=rpc(u,'web3_clientVersion',[])
        except Exception as e: out['client']='ERR '+str(e)[:60]
        codes={}
        for k,a in WELL.items():
            if int(a,16)==0: continue
            try: codes[k]=len(rpc(u,'eth_getCode',[a,'latest']))//2-1
            except Exception as e: codes[k]='ERR '+str(e)[:60]
        out['codeLen']=codes
        try: out['bls_g1add']=len(rpc(u,'eth_call',[{'to':'0x000000000000000000000000000000000000000b','data':'0x'+'00'*256},'latest']))//2-1
        except Exception as e: out['bls_g1add']='ERR '+str(e)[:80]
        for tok in token_for(cid):
            calls=[(pm,sel('exttload(bytes32)')+CUR),(pm,sel('sync(address)')+adr(tok)),(pm,sel('exttload(bytes32)')+CUR),(pm,sel('exttload(bytes32)')+RES),(tok,sel('balanceOf(address)')+adr(pm)),(pm,sel('sync(address)')+u256(0)),(pm,sel('exttload(bytes32)')+CUR),(pm,sel('exttload(bytes32)')+RES)]
            try:
                r=dec_agg3(rpc(u,'eth_call',[{'to':MC3,'data':enc_agg3(calls)},'latest']))
            except Exception as e:
                out['mc3']='ERR '+str(e)[:120]; continue
            out['mc3']={'token':tok,'curBefore':r[0],'syncOk':r[1][0],'curAfterSync':r[2][1],'resAfterSync':r[3][1],'balanceOf':r[4][1],'sync0Ok':r[5][0],'curAfterSync0':r[6][1],'resAfterSync0':r[7][1]}
            if r[1][0] and r[4][0] and int(r[3][1] or '0',16)>0: break
    except Exception as e:
        out['err']=str(e)[:200]
    return out
if __name__=='__main__':
    with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(probe,NETS))
    json.dump(res,open('probe_chain.json','w'),indent=1)
    for r in res:
        print(r['chainId'],r['name'],r.get('block'),str(r.get('client'))[:50],'bls',r.get('bls_g1add'),r.get('err',''))
        print('   code:',{k.split(' (')[0]:v for k,v in (r.get('codeLen') or {}).items() if v})
        m=r.get('mc3')
        if isinstance(m,dict):
            ok = m['curAfterSync'][-40:]==m['token'][2:].lower() and m['resAfterSync']==m['balanceOf'] and int(m['curAfterSync0'],16)==0
            print('   mc3: token',m['token'],'curBefore',int(m['curBefore'][1] or '0',16),'syncOk',m['syncOk'],'cur==token',m['curAfterSync'][-40:]==m['token'][2:].lower(),'res==balanceOf',m['resAfterSync']==m['balanceOf'],'res',int(m['resAfterSync'] or '0',16),'afterSync0 cur',int(m['curAfterSync0'] or '0',16),'res kept',m['resAfterSync0']==m['resAfterSync'],'PASS' if ok else 'CHECK')
        else: print('   mc3:',m)
