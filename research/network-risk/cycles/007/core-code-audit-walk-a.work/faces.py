# Read-only: which candidate addresses mirror the PoolManager's native balance (OpenZeppelin C-01 precondition).
import json
from walk import NETS, rpc
CAND={'CELO token':'0x471EcE3750Da237f93B8E339c536989b8978a438','0x1010':'0x0000000000000000000000000000000000001010','0x3600':'0x3600000000000000000000000000000000000000',
      'LegacyERC20ETH':'0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000','OP WETH predeploy':'0x4200000000000000000000000000000000000006'}
out={}
for n in NETS:
    pm=n['poolManager']; u=n['rpc']
    B=rpc(u,'eth_blockNumber',[]).get('result','latest')
    nb=rpc(u,'eth_getBalance',[pm,B]); nbv=int(nb.get('result','0x0'),16)
    e={'block':int(B,16) if B!='latest' else None,'native':nbv,'cands':{}}
    for name,a in CAND.items():
        code=rpc(u,'eth_getCode',[a,B]).get('result','0x'); cl=(len(code)-2)//2
        r=rpc(u,'eth_call',[{'to':a,'data':'0x70a08231'+pm[2:].lower().rjust(64,'0')},B])
        res=r.get('result'); v=int(res,16) if res and len(res)>=66 else None
        t=rpc(u,'eth_call',[{'from':pm,'to':a,'data':'0xa9059cbb'+'dead'.rjust(64,'0')+hex(1)[2:].rjust(64,'0')},B])
        tr = ('ok:'+t['result'][:70]) if 'result' in t else ('err:'+json.dumps(t['error'])[:90])
        e['cands'][name]={'codeLen':cl,'balanceOf':v,'mirrors': (v is not None and nbv>0 and (v==nbv or v==nbv//10**12)),'transfer1_from_pm':tr}
    out[n['chainId']]=e
    print(n['chainId'],n['name'],'block',e['block'],'native',nbv)
    for k,v in e['cands'].items():
        if v['codeLen'] or v['balanceOf'] is not None: print('    ',k,v)
json.dump(out,open('raw/faces.json','w'),indent=1)
