# Read-only eth_call probes of the deployed PoolManagers: calldata width validation and the hook flag / fee / spacing rules.
import json,os,sys,time,urllib.request,concurrent.futures as cf
from keccak import keccak256
os.environ.setdefault('SSL_CERT_FILE','/root/.ccr/ca-bundle.crt')
NET=json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
def rpc(url,method,params,timeout=40,retries=3):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(retries+1):
        try:
            req=urllib.request.Request(url,data=body,headers={'content-type':'application/json','user-agent':'curl/8'})
            with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read())
        except Exception as e:
            last={'neterror':str(e)[:200]}; time.sleep(1.5)
    return last
sel=lambda s: keccak256(s.encode())[:4].hex()
W=lambda x: (x%(1<<256)).to_bytes(32,'big').hex()
INIT=sel('initialize((address,address,uint24,int24,address),uint160)')
ERR={sel(s):s for s in ['TickSpacingTooLarge(int24)','TickSpacingTooSmall(int24)','CurrenciesOutOfOrderOrEqual(address,address)','HookAddressNotValid(address)','LPFeeTooLarge(uint24)','InvalidHookResponse()','PoolAlreadyInitialized()','InvalidSqrtPrice(uint160)','WrappedError(address,bytes4,bytes,bytes)','ManagerLocked()']}
C0=0x7a11c0de00000000000000000000000000b17501
C1=0x7a11c0de00000000000000000000000000b17502
HP=0x5eed00c0ffee00000000000000000000b1750000   # hook prefix, low 16 bits free
Q96=1<<96
MINP=4295128739; MAXP=1461446703485210103287273052203988822378723970342
def init(c0=C0,c1=C1,fee=3000,sp=60,hook=0,price=Q96): return '0x'+INIT+W(c0)+W(c1)+W(fee)+W(sp)+W(hook)+W(price)
D=1<<160
cases=[
 ('clean key, fee 3000, spacing 60, no hook', init()),
 ('currency0 word with bit 160 set', init(c0=C0|D)),
 ('currency1 word with bit 160 set', init(c1=C1|D)),
 ('fee word with bit 24 set', init(fee=3000|1<<24)),
 ('spacing word with bit 24 set', init(sp=60|1<<24)),
 ('spacing word 0xffffc4 without sign extension', init(sp=0xffffc4)),
 ('spacing -60 sign extended', init(sp=-60)),
 ('hooks word with bit 160 set', init(hook=D)),
 ('price word with bit 160 set', init(price=Q96|D)),
 ('fee 0x800000 with zero hook', init(fee=0x800000)),
 ('fee 1000000', init(fee=1000000)),
 ('fee 1000001', init(fee=1000001)),
 ('fee 0x800001', init(fee=0x800001)),
 ('fee 0xC00000', init(fee=0xC00000)),
 ('fee 0x400000', init(fee=0x400000)),
 ('spacing 0', init(sp=0)),
 ('spacing 32767', init(sp=32767)),
 ('spacing 32768', init(sp=32768)),
 ('equal currencies', init(c1=C0)),
 ('currencies out of order', init(c0=C1,c1=C0)),
 ('price MIN_SQRT_PRICE', init(price=MINP)),
 ('price MIN_SQRT_PRICE - 1', init(price=MINP-1)),
 ('price MAX_SQRT_PRICE - 1', init(price=MAXP-1)),
 ('price MAX_SQRT_PRICE', init(price=MAXP)),
 ('hook flags 0x0000, static fee', init(hook=HP)),
 ('hook flags 0x0000, dynamic fee', init(hook=HP,fee=0x800000)),
 ('hook flag bit 14 only (0x4000), static fee', init(hook=HP|0x4000)),
 ('hook flags 0x0008 (beforeSwapReturnDelta alone)', init(hook=HP|0x0008)),
 ('hook flags 0x0004 (afterSwapReturnDelta alone)', init(hook=HP|0x0004)),
 ('hook flags 0x0002 (afterAddLiquidityReturnDelta alone)', init(hook=HP|0x0002)),
 ('hook flags 0x0001 (afterRemoveLiquidityReturnDelta alone)', init(hook=HP|0x0001)),
 ('hook flags 0x0088 (beforeSwap + returnDelta), codeless', init(hook=HP|0x0088)),
 ('hook flags 0x0044', init(hook=HP|0x0044)),
 ('hook flags 0x0402', init(hook=HP|0x0402)),
 ('hook flags 0x0101', init(hook=HP|0x0101)),
 ('hook flags 0x0fff (all but initialize)', init(hook=HP|0x0fff)),
 ('hook flags 0x2000 (beforeInitialize), codeless', init(hook=HP|0x2000)),
 ('hook flags 0x1000 (afterInitialize), codeless', init(hook=HP|0x1000)),
 ('protocolFeesAccrued(clean)', '0x'+sel('protocolFeesAccrued(address)')+W(C0)),
 ('protocolFeesAccrued(word with bit 160 set)', '0x'+sel('protocolFeesAccrued(address)')+W(C0|D)),
 ('balanceOf(clean owner, id)', '0x'+sel('balanceOf(address,uint256)')+W(C0)+W(C1)),
 ('balanceOf(owner word with bit 160 set, id)', '0x'+sel('balanceOf(address,uint256)')+W(C0|D)+W(C1)),
 ('balanceOf(owner, id with bit 200 set)', '0x'+sel('balanceOf(address,uint256)')+W(C0)+W(C1|1<<200)),
 ('isOperator(clean, word with bit 255 set)', '0x'+sel('isOperator(address,address)')+W(C0)+W(C1|1<<255)),
 ('sync(zero address word with bit 160 set)', '0x'+sel('sync(address)')+W(D)),
 ('sync(address(0))', '0x'+sel('sync(address)')+W(0)),
 ('take while locked', '0x'+sel('take(address,address,uint256)')+W(0)+W(C0)+W(0)),
]
FROM='0x00000000000000000000000000000000b1750aaa'
def decode(r):
    if 'neterror' in r: return 'NET:'+r['neterror'][:60]
    if 'result' in r:
        x=r['result']; n=(len(x)-2)//2
        if n==32:
            v=int(x,16); v=v-(1<<256) if v>>255 else v
            return f'ok:{v}'
        return f'ok:{n}bytes'
    e=r.get('error',{}); d=e.get('data')
    if isinstance(d,dict): d=d.get('data') or d.get('result')
    if isinstance(d,str) and d.startswith('0x') and len(d)>=10:
        s=d[2:10]; name=ERR.get(s,s)
        arg=''
        if len(d)>=74 and not name.startswith('WrappedError'): arg=':'+hex(int(d[10:74],16))
        return 'revert:'+name+arg
    if isinstance(d,str) and d in ('0x',''): return 'revert:empty'
    return 'revert:nodata(' + str(e.get('message'))[:50] + ')'
def run(n):
    out=[]
    blk=rpc(n['rpc'],'eth_blockNumber',[])
    for name,data in cases:
        r=rpc(n['rpc'],'eth_call',[{'from':FROM,'to':n['poolManager'],'data':data},'latest'])
        out.append(decode(r)); time.sleep(0.05)
    return n['chainId'],n['name'],blk.get('result'),out
if __name__=='__main__':
    res={}
    with cf.ThreadPoolExecutor(8) as ex:
        for cid,name,blk,out in ex.map(run,NET):
            res[cid]={'name':name,'block':int(blk,16) if blk else None,'out':out}
    json.dump({'cases':[c[0] for c in cases],'res':res},open('width_probe.out.json','w'),indent=1)
    ref=res[1]['out']
    for i,(name,_) in enumerate(cases):
        vals={}
        for cid,v in res.items(): vals.setdefault(v['out'][i],[]).append(cid)
        print(f'{i:2d} {name:58s}', ' | '.join(f'{k} x{len(v)}'+('' if len(vals)==1 else str(v)) for k,v in vals.items()))
    print({cid:v['block'] for cid,v in res.items()})
