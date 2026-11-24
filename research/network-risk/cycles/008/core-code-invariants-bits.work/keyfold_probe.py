# Read-only: does a node fold storage or transient keys that differ in one bit?
# (a) extsload of the 256 one-bit keys on the deployed PoolManager, compared with slot 0 (owner) and slot 2 (fee controller).
# (b) eth_call creation payload: SSTORE(0,0xAA), TSTORE(0,0xBB), then SLOAD and TLOAD of every key 1<<b; returns two bitmaps.
import json,concurrent.futures as cf
from width_probe import rpc,sel,W,NET
S3=sel('extsload(bytes32[])')
CODE='60aa5f55'+'60bb5f5d'+'5f'+'5b'+'6001811b'+'80541515'+'821b'+'5f51175f52'+'5c1515'+'811b'+'60205117602052'+'600101'+'8061010011'+'600957'+'60405ff3'
def run(n):
    keys=[1<<b for b in range(256)]
    r=rpc(n['rpc'],'eth_call',[{'to':n['poolManager'],'data':'0x'+S3+W(0x20)+W(256)+''.join(W(k) for k in keys)},'latest'])
    out={}
    if 'result' in r:
        x=r['result'][2:]; words=[int(x[128+64*i:192+64*i],16) for i in range(256)]
        out['nonzero_bits']={b:hex(w) for b,w in enumerate(words) if w}
    else: out['ext_err']=str(r)[:200]
    r2=rpc(n['rpc'],'eth_call',[{'from':'0x00000000000000000000000000000000b1750aaa','data':'0x'+CODE},'latest'])
    if 'result' in r2 and len(r2['result'])==130:
        s=int(r2['result'][2:66],16); t=int(r2['result'][66:],16)
        out['sload_fold_bits']=[b for b in range(256) if s>>b&1]; out['tload_fold_bits']=[b for b in range(256) if t>>b&1]
    else: out['probe_err']=str(r2)[:200]
    out['owner']=n['owner']; out['pfc']=n['protocolFeeController']
    return n['chainId'],out
with cf.ThreadPoolExecutor(8) as ex: res=dict(ex.map(run,NET))
json.dump(res,open('keyfold_probe.out.json','w'),indent=1)
for k,v in res.items(): print(k,{a:b for a,b in v.items() if a not in('owner','pfc')}, 'owner',v['owner'][-8:],'pfc',v['pfc'][-8:])
