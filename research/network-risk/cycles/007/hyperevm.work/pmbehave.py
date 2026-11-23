from asm import asm
from lib import *
from keccak import sel
X='0xbeef00000000000000000000000000000000beef'; EOA='0xe0a0000000000000000000000000000000000e0a'
PMI=int(PM,16)
code=asm(['CALLER',PMI,'EQ',('ref','cb'),'JUMPI',
  # top: build unlock(bytes) calldata at mem 0: selector | 0x20 | len | script
  0x48c89491,224,'SHL',0,'MSTORE',0x20,4,'MSTORE','CALLDATASIZE',36,'MSTORE','CALLDATASIZE',0,68,'CALLDATACOPY',
  0,0,'CALLDATASIZE',68,'ADD',0,0,PMI,'GAS','CALL',
  0,'MSTORE','RETURNDATASIZE',0,32,'RETURNDATACOPY','RETURNDATASIZE',32,'ADD',0,'RETURN',
  ('label','cb'),
  68,                       # ptr
  ('label','loop'),
  'DUP1',36,'CALLDATALOAD',68,'ADD','GT','ISZERO',('ref','done'),'JUMPI',   # if !(end > ptr) done ; stack: ptr
  # l = calldataload(ptr+32)
  'DUP1',32,'ADD','CALLDATALOAD',      # stack: ptr, l
  'DUP1','DUP3',64,'ADD',0,'CALLDATACOPY',   # calldatacopy(0, ptr+64, l)
  0,0,'DUP3',0,'DUP6','CALLDATALOAD',PMI,'GAS','CALL',   # call(gas,PM,value=calldataload(ptr),0,l,0,0) ; stack: ptr,l,ok
  ('ref','okk'),'JUMPI',
  'RETURNDATASIZE',0,0,'RETURNDATACOPY','RETURNDATASIZE',0,'REVERT',
  ('label','okk'),           # stack: ptr,l
  'ADD',64,'ADD',            # ptr = ptr + l + 64
  ('ref','loop'),'JUMP',
  ('label','done'),
  0x20,0,'MSTORE',0,0x20,'MSTORE',64,0,'RETURN'])
def w(x): return x.to_bytes(32,'big').hex()
def step(value,data): return w(value)+w(len(data)//2)+data
WHYPE='5555555555555555555555555555555555555555'
take1=sel('take(address,address,uint256)')+w(0)+X[2:].rjust(64,'0')+w(1)
settle=sel('settle()'); syncW=sel('sync(address)')+WHYPE.rjust(64,'0'); sync0=sel('sync(address)')+w(0)
errs={sel(s):s for s in ['NonzeroNativeValue()','CurrencyNotSettled()','ManagerLocked()','AlreadyUnlocked()','NativeTransferFailed()','WrappedError(address,bytes4,bytes,bytes)']}
tests={'take 1 wei then settle with value 1':step(0,take1)+step(1,settle),
       'sync(WHYPE), take 1 wei, settle with value 1':step(0,syncW)+step(0,take1)+step(1,settle),
       'sync(WHYPE), sync(0), take 1 wei, settle with value 1':step(0,syncW)+step(0,sync0)+step(0,take1)+step(1,settle),
       'take 1 wei and leave it unpaid':step(0,take1),
       'sync(WHYPE) then settle without value':step(0,syncW)+step(0,settle),
       'empty callback':''}
out={}
for url_name,u in (('official',OFF),('archive',ARCH)):
    for n,s in tests.items():
        r=rpc('eth_call',[{'from':EOA,'to':X,'data':'0x'+s,'gas':hex(2_500_000)},'latest',{X:{'code':code}}],url=u,raw=True)
        if 'error' in r: res='rpc error '+json.dumps(r['error'])[:200]
        else:
            b=bytes.fromhex(r['result'][2:]); ok=int.from_bytes(b[:32],'big'); rd=b[32:]
            res=f"unlock ok={ok}"+('' if ok else ' revert '+errs.get(rd[:4].hex(),rd[:4].hex())+(' inner '+ ' '.join(errs[k] for k in errs if k in rd[4:].hex()) if len(rd)>4 else ''))
        out[f'{url_name}: {n}']=res; print(url_name,'|',n,'=>',res)
    r=rpc('eth_call',[{'from':EOA,'to':PM,'data':'0x'+settle},'latest'],url=u,raw=True); d=(r.get('error') or {}).get('data','')
    print(url_name,'| settle outside unlock =>',errs.get(d[2:10],json.dumps(r)[:120])); out[f'{url_name}: settle outside unlock']=errs.get(d[2:10],'?')
json.dump(out,open('raw/pm_behaviour.json','w'),indent=1)
