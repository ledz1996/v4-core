# Read-only: for precompile-dispatched tokens, does an address that differs in one bit answer balanceOf(PoolManager) like the token itself?
import json,time,concurrent.futures as cf
from width_probe import rpc,sel,W,NET
N={n['chainId']:n for n in NET}
TOK={4217:['0x20c0000000000000000000000000000000000000','0x20c000000000000000000000030a4c7f7b8f3586','0x20c0000000000000000000006a37da5c996874be'],
     5042:['0x3600000000000000000000000000000000000000'],
     8453:['0xB2000000000000000000002fEb517dFeC7415344','0xB2000000000000000000000d8Ce462E99ee7A47B']}
BO=sel('balanceOf(address)')
def q(url,addr,pm):
    r=rpc(url,'eth_call',[{'to':'0x%040x'%addr,'data':'0x'+BO+W(int(pm,16))},'latest'],retries=4)
    if not isinstance(r,dict): return 'neterr'
    if 'result' in r: return r['result']
    if 'neterror' in r: return 'neterr'
    return 'revert'
out={}
for cid,toks in TOK.items():
    n=N[cid]
    for t in toks:
        T=int(t,16); base=q(n['rpc'],T,n['poolManager'])
        def one(b): 
            time.sleep(0.02); return b,q(n['rpc'],T^(1<<b),n['poolManager'])
        with cf.ThreadPoolExecutor(4) as ex: res=dict(ex.map(one,range(160)))
        kinds={}
        for b,v in res.items():
            k='same-as-token' if (v==base and v not in('revert','neterr','0x')) else ('revert' if v=='revert' else ('empty' if v=='0x' else ('neterr' if v=='neterr' else 'other:'+v[-16:])))
            kinds.setdefault(k,[]).append(b)
        out[f'{cid}:{t}']={'base':base,'kinds':{k:(v if len(v)<12 else f'{len(v)} bits') for k,v in kinds.items()}}
        print(cid,t,'base',base[-20:] if base.startswith('0x') else base,{k:(v if len(v)<12 else f'{len(v)} bits') for k,v in kinds.items()})
json.dump(out,open('addrfold_probe.out.json','w'),indent=1)
