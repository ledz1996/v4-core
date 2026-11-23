# Read-only behaviour walk on the deployed PoolManagers (eth_call with state overrides, nothing is sent).
# Purpose: per-network evidence for OpenZeppelin C-01 and Trail of Bits 3 (sync and collectProtocolFees guards).
import json,urllib.request,ssl,sys,time
from asm import asm
from keccak import sel
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
NETS=json.load(open('../../../state/networks.json'))['networks']
def post(url,body,timeout=40):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=timeout,context=ctx) as r: return json.load(r)
def rpc(url,method,params):
    err=None
    for i in range(3):
        try: return post(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
        except Exception as e: err=e; time.sleep(1.5*(i+1))
    return {'error':{'message':'transport '+str(err)[:150]}}
S={k:int(sel(v),16) for k,v in dict(sync='sync(address)',unlock='unlock(bytes)',settle='settle()',take='take(address,address,uint256)',
    collect='collectProtocolFees(address,address,uint256)',cb='unlockCallback(bytes)').items()}
SINK=0xdEaD
A='0xa77ac4e200000000000000000000000000a77ac4'
EOA='0xe0a0000000000000000000000000000000000e0a'
MIRROR='0x00000000000000000000000000000000fAcE0001'
# mirror token: answers every call with BALANCE(first argument). Models a native face (src/test/NativeERC20.sol:46-48 is the repo's own model).
MIRROR_CODE=asm([4,'CALLDATALOAD','BALANCE',0,'MSTORE',32,0,'RETURN'])
def stub(pm,steps):
    pm=int(pm,16); t=[]
    t+=['CALLDATASIZE','ISZERO',('ref','stop'),'JUMPI', 0,'CALLDATALOAD',224,'SHR','DUP1',S['cb'],'EQ',('ref','cb'),'JUMPI','POP']
    # main(face): remember face, sync(face) while locked, unlock("")
    t+=[4,'CALLDATALOAD',0,'SSTORE']
    t+=[S['sync'],224,'SHL',0,'MSTORE',4,'CALLDATALOAD',4,'MSTORE', 32,0x100,36,0,0,pm,'GAS','CALL',0x120,'MSTORE','RETURNDATASIZE',0x140,'MSTORE']
    t+=[S['unlock'],224,'SHL',0,'MSTORE',0x20,4,'MSTORE',0,36,'MSTORE', 0,0,68,0,0,pm,'GAS','CALL']
    t+=[0,'MSTORE',0x120,'MLOAD',32,'MSTORE',0x140,'MLOAD',64,'MSTORE',0x100,'MLOAD',96,'MSTORE','RETURNDATASIZE',0,128,'RETURNDATACOPY','RETURNDATASIZE',128,'ADD',0,'RETURN']
    t+=[('label','stop'),'STOP']
    t+=[('label','cb'),'POP']
    base=0x200
    for i,(kind,arg) in enumerate(steps):
        o=base+i*96; value=0
        if kind=='settle': t+=[S['settle'],224,'SHL',0,'MSTORE']; size=4; value=arg
        elif kind=='syncface': t+=[S['sync'],224,'SHL',0,'MSTORE',0,'SLOAD',4,'MSTORE']; size=36
        elif kind=='sync0': t+=[S['sync'],224,'SHL',0,'MSTORE',0,4,'MSTORE']; size=36
        elif kind=='collect': # collectProtocolFees(SINK, currency, 0); currency = 0 or face
            t+=[S['collect'],224,'SHL',0,'MSTORE',SINK,4,'MSTORE']+([0,'SLOAD'] if arg=='face' else [0])+[36,'MSTORE',0,68,'MSTORE']; size=100
        elif kind=='take': t+=[S['take'],224,'SHL',0,'MSTORE',0,4,'MSTORE','ADDRESS',36,'MSTORE',arg,68,'MSTORE']; size=100
        t+=[32,o+64,size,0,value,pm,'GAS','CALL',o,'MSTORE','RETURNDATASIZE',o+32,'MSTORE']
    n=len(steps)*96
    t+=[0x20,base-64,'MSTORE',n,base-32,'MSTORE',n+64,base-64,'RETURN']
    return asm(t)
ERR={sel(x):x for x in ['NonzeroNativeValue()','ManagerLocked()','InvalidCaller()','ProtocolFeeCurrencySynced()','ContractUnlocked()','CurrencyNotSettled()','AlreadyUnlocked()','WrappedError(address,bytes4,bytes,bytes)','Panic(uint256)','Error(string)']}
def dec(word,rds,ok):
    if ok: return 'ok rds=%d val=%d'%(rds,int(word,16) if rds>=32 else 0)
    s=word[:8]; return 'REVERT '+(ERR.get(s,'0x'+s) if rds>=4 else 'empty')
def run(net,face,steps,at=A,blk='latest'):
    pm=net['poolManager']; code=stub(pm,steps)
    ov={at:{'code':code,'balance':hex(10**18)},EOA:{'balance':hex(10**18)},MIRROR:{'code':MIRROR_CODE}}
    data='0x00000000'+face[2:].lower().rjust(64,'0')
    r=rpc(net['rpc'],'eth_call',[{'from':EOA,'to':at,'data':data,'gas':hex(3_000_000)},blk,ov])
    if 'error' in r: return {'error':json.dumps(r['error'])[:300]}
    b=bytes.fromhex(r['result'][2:])
    if len(b)<128: return {'error':'short '+b.hex()}
    out={'presync_while_locked':dec(b[96:128].hex(),int.from_bytes(b[64:96],'big'),int.from_bytes(b[32:64],'big')),'unlock_ok':int.from_bytes(b[:32],'big')}
    rest=b[128:]
    if not out['unlock_ok']: out['unlock_revert']=ERR.get(rest.hex()[:8],rest.hex()[:200]); return out
    body=rest[64:]
    out['steps']=[]
    for i,(kind,arg) in enumerate(steps):
        c=body[i*96:(i+1)*96]
        out['steps'].append('%s(%s): %s'%(kind,arg,dec(c[64:96].hex(),int.from_bytes(c[32:64],'big'),int.from_bytes(c[:32],'big'))))
    return out
STEPS_ATT=[('settle',1000),('collect',0),('settle',0),('settle',1000),('syncface',None),('settle',0),('take',1000)]
STEPS_CTL=[('collect','face'),('collect',0),('settle',0),('sync0',None),('settle',1000),('syncface',None),('settle',0),('take',1000)]
FACES={42220:'0x471EcE3750Da237f93B8E339c536989b8978a438',137:'0x0000000000000000000000000000000000001010',5042:'0x3600000000000000000000000000000000000000',
       10:'0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000',7777777:'0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000'}
if __name__=='__main__':
    res={}
    only=[int(x) for x in sys.argv[1:]]
    for net in NETS:
        cid=net['chainId']
        if only and cid not in only: continue
        e={'name':net['name']}
        bn=rpc(net['rpc'],'eth_blockNumber',[]); e['block']=int(bn.get('result','0x0'),16)
        cv=rpc(net['rpc'],'web3_clientVersion',[]); e['client']=cv.get('result',str(cv.get('error'))[:80])
        e['mirror_as_attacker']=run(net,MIRROR,STEPS_ATT)
        if cid in FACES: e['realface_as_attacker']=run(net,FACES[cid],STEPS_ATT)
        ctl=net['protocolFeeController']
        if int(ctl,16)!=0:
            e['mirror_as_controller']=run(net,MIRROR,STEPS_CTL,at=ctl)
            if cid in FACES: e['realface_as_controller']=run(net,FACES[cid],STEPS_CTL,at=ctl)
        res[cid]=e
        print(cid,json.dumps(e,indent=1),flush=True)
    import os
    os.makedirs('raw',exist_ok=True)
    fn='raw/walk.json'
    old=json.load(open(fn)) if os.path.exists(fn) else {}
    old.update({str(k):v for k,v in res.items()}); json.dump(old,open(fn,'w'),indent=1)
