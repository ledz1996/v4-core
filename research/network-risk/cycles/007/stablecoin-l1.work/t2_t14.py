# L-284: call shapes against the ConfigurableAccount precompile under a simulated block time after the T14 activation. Read-only.
import json,sys
from lib import *
cid=4217; n=net(cid); u=n['rpc']; pm=n['poolManager']
AACC='0xAACC000000000000000000000000000000000000'
KEYT='(address,address,uint24,int24,address)'
hooks=['beforeInitialize(address,%s,uint160)'%KEYT,'afterInitialize(address,%s,uint160,int24)'%KEYT,
 'beforeAddLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)'%KEYT,'afterAddLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)'%KEYT,
 'beforeRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)'%KEYT,'afterRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)'%KEYT,
 'beforeSwap(address,%s,(bool,int256,uint160),bytes)'%KEYT,'afterSwap(address,%s,(bool,int256,uint160),int256,bytes)'%KEYT,
 'beforeDonate(address,%s,uint256,uint256,bytes)'%KEYT,'afterDonate(address,%s,uint256,uint256,bytes)'%KEYT]
shapes=[('empty','')]+[('transfer0',cd('transfer(address,uint256)','0x7e57000000000000000000000000000000000505',0)),('transfer1',cd('transfer(address,uint256)','0x7e57000000000000000000000000000000000505',1)),
 ('balanceOf',cd('balanceOf(address)',pm)),('unlockCallback',cd('unlockCallback(bytes)',0x20,0))]+[(h.split('(')[0],sel(h)+w(0)*12) for h in hooks]
targets=sys.argv[1:] or [AACC]
def sweep(t, time=None, extra=None):
    calls=[{'from':pm,'to':t,'data':'0x'+d,'gas':hex(2_000_000)} for _,d in shapes]
    bsc={'calls':calls}
    if time: bsc['blockOverrides']={'time':hex(time)}
    if extra: bsc['stateOverrides']=extra
    r=rpc(u,'eth_simulateV1',[{'blockStateCalls':[bsc],'validation':False},'latest'])
    if 'result' not in r: return r
    out=[]
    for (name,_),c in zip(shapes,r['result'][0]['calls']):
        out.append((name,c.get('status'),c.get('returnData','')[:74],(c.get('error') or {}).get('message','')[:60], int(c.get('gasUsed','0x0'),16)))
    return out
res={}
for t in targets:
    for label,time in (('now',None),('T14',1796742000+600)):
        r=sweep(t,time); res[t+'_'+label]=r
        print('==',t,label)
        if isinstance(r,dict): print(json.dumps(r)[:600])
        else:
            for x in r: print('  ',x)
json.dump(res,open('raw/t2_t14.json','w'),indent=1)
