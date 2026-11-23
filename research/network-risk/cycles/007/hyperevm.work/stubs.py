from asm import asm
from lib import *
F=asm([52,'CALLDATASIZE','SUB','DUP1',52,0,'CALLDATACOPY',
       0,0,'DUP3',0,20,'CALLDATALOAD',0,'CALLDATALOAD',96,'SHR','GAS','CALL',
       0,'MSTORE','RETURNDATASIZE',0,32,'RETURNDATACOPY','RETURNDATASIZE',32,'ADD',0,'RETURN'])
K=asm([53,'CALLDATASIZE','SUB','DUP1',53,0x100,'CALLDATACOPY',
       0,'CALLDATALOAD',248,'SHR',
       'DUP1',1,'EQ',('ref','static'),'JUMPI',
       'DUP1',2,'EQ',('ref','deleg'),'JUMPI',
       'DUP1',3,'EQ',('ref','callcode'),'JUMPI',
       'POP',0,0,'DUP3',0x100,21,'CALLDATALOAD',1,'CALLDATALOAD',96,'SHR','GAS','CALL',('ref','done'),'JUMP',
       ('label','static'),'POP',0,0,'DUP3',0x100,1,'CALLDATALOAD',96,'SHR','GAS','STATICCALL',('ref','done'),'JUMP',
       ('label','deleg'),'POP',0,0,'DUP3',0x100,1,'CALLDATALOAD',96,'SHR','GAS','DELEGATECALL',('ref','done'),'JUMP',
       ('label','callcode'),'POP',0,0,'DUP3',0x100,21,'CALLDATALOAD',1,'CALLDATALOAD',96,'SHR','GAS','CALLCODE',
       ('label','done'),0,'MSTORE','CALLVALUE',32,'MSTORE','SELFBALANCE',64,'MSTORE',
       1,'CALLDATALOAD',96,'SHR','BALANCE',96,'MSTORE','CALLER','BALANCE',128,'MSTORE',
       'RETURNDATASIZE',160,'MSTORE','RETURNDATASIZE',0,192,'RETURNDATACOPY','RETURNDATASIZE',192,'ADD',0,'RETURN'])
# callee reporter: caller, callvalue, address, origin, selfbalance
C=asm(['CALLER',0,'MSTORE','CALLVALUE',32,'MSTORE','ADDRESS',64,'MSTORE','ORIGIN',96,'MSTORE','SELFBALANCE',128,'MSTORE',160,0,'RETURN'])
A='0xa11ce00000000000000000000000000000000a11'
EOA='0xe0a0000000000000000000000000000000000e0a'
CAL='0xca11ee000000000000000000000000000000ca11'
KINDS=['CALL','STATICCALL','DELEGATECALL','CALLCODE']
def w(x): return x.to_bytes(32,'big').hex()
def run(target,data,kind,v_pm_to_a=0,v_a_to_t=0,url=OFF,extra=None,gas=2_000_000,blk='latest',a_balance=0):
    inner=bytes([kind]).hex()+target[2:].rjust(40,'0')+w(v_a_to_t)+data
    outer=A[2:]+w(v_pm_to_a)+inner
    ov={PM:{'code':F},A:{'code':K,'balance':hex(a_balance)},EOA:{'balance':hex(10**20)},CAL:{'code':C}}
    if extra: ov.update(extra)
    r=rpc('eth_call',[{'from':EOA,'to':PM,'data':'0x'+outer,'gas':hex(gas)},blk,ov],url=url,raw=True)
    if 'error' in r: return {'err':json.dumps(r['error'])[:200]}
    b=bytes.fromhex(r['result'][2:])
    okF=int.from_bytes(b[:32],'big'); rest=b[32:]
    if not okF or len(rest)<192: return {'pm_call_ok':okF,'raw':rest.hex()[:200]}
    g=lambda i:int.from_bytes(rest[32*i:32*i+32],'big')
    return {'ok':g(0),'callvalue_in_A':g(1),'A_bal':g(2),'target_bal':g(3),'PM_bal':g(4),'rds':g(5),'ret':rest[192:].hex()}
if __name__=='__main__':
    print('F',F);print('K',K);print('C',C)
    pmbal=int(rpc('eth_getBalance',[PM,'latest']),16); print('PM balance',pmbal)
    for k in range(4):
        r=run(CAL,'',k,v_pm_to_a=10**15,v_a_to_t=7 if k in(0,3) else 0)
        print(KINDS[k],{x:(hex(y) if isinstance(y,int) else y) for x,y in r.items() if x!='ret'})
        ret=r.get('ret','')
        print('   callee saw caller',ret[24:64],'value',int(ret[64:128] or '0',16),'address',ret[152:192],'origin',ret[216:256],'selfbal',int(ret[256:320] or '0',16))
