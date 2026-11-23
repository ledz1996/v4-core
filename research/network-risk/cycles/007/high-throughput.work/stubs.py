from asm import asm
from lib import *
# F at the PoolManager address: forwards calldata[52:] to address calldata[0:20] with value calldata[20:52] by CALL, returns [ok][returndata]
F=asm([52,'CALLDATASIZE','SUB','DUP1',52,0,'CALLDATACOPY',
       0,0,'DUP3',0,20,'CALLDATALOAD',0,'CALLDATALOAD',96,'SHR','GAS','CALL',
       0,'MSTORE','RETURNDATASIZE',0,32,'RETURNDATACOPY','RETURNDATASIZE',32,'ADD',0,'RETURN'])
# K: calldata = kind(1) target(20) value(32) data. kind 0 CALL, 1 STATICCALL, 2 DELEGATECALL, 3 CALLCODE.
# returns ok, CALLVALUE here, SELFBALANCE, BALANCE(target), BALANCE(CALLER), returndatasize, returndata
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
# C: callee reporter: caller, callvalue, address, origin, selfbalance
C=asm(['CALLER',0,'MSTORE','CALLVALUE',32,'MSTORE','ADDRESS',64,'MSTORE','ORIGIN',96,'MSTORE','SELFBALANCE',128,'MSTORE',160,0,'RETURN'])
A='0xa11ce00000000000000000000000000000000a11'
EOA='0xe0a0000000000000000000000000000000000e0a'
CAL='0xca11ee000000000000000000000000000000ca11'
KINDS=['CALL','STATICCALL','DELEGATECALL','CALLCODE']
def inherited_req(chain,target,data,kind,v_pm_to_a=0,v_a_to_t=0,a_balance=0,gas=3_000_000,blk='latest',extra=None):
    """EOA -> PM(F) -CALL value v_pm_to_a-> A(K) -kind-> target"""
    pm=PM[chain]
    inner=bytes([kind]).hex()+target[2:].rjust(40,'0')+w(v_a_to_t)+data
    outer=A[2:]+w(v_pm_to_a)+inner
    ov={pm:{'code':F},A:{'code':K,'balance':hex(a_balance)},EOA:{'balance':hex(10**21)},CAL:{'code':C}}
    if extra: ov.update(extra)
    return ('eth_call',[{'from':EOA,'to':pm,'data':'0x'+outer,'gas':hex(gas)},blk,ov])
def direct_req(chain,target,data,kind,value=0,gas=3_000_000,blk='latest',extra=None):
    """EOA -> PM(K) -kind-> target ; the PoolManager address itself issues the call as an inner frame"""
    pm=PM[chain]
    inner=bytes([kind]).hex()+target[2:].rjust(40,'0')+w(value)+data
    ov={pm:{'code':K},EOA:{'balance':hex(10**21)},CAL:{'code':C}}
    if extra: ov.update(extra)
    return ('eth_call',[{'from':EOA,'to':pm,'data':'0x'+inner,'gas':hex(gas)},blk,ov])
def parse(r,inherited):
    if 'error' in r: return {'err':json.dumps(r['error'])[:160]}
    b=bytes.fromhex(r['result'][2:])
    if inherited:
        okF=int.from_bytes(b[:32],'big'); b=b[32:]
        if not okF or len(b)<192: return {'pm_call_ok':okF,'raw':b.hex()[:200]}
    if len(b)<192: return {'short':b.hex()}
    g=lambda i:int.from_bytes(b[32*i:32*i+32],'big')
    return {'ok':g(0),'cv':g(1),'selfbal':g(2),'tbal':g(3),'callerbal':g(4),'rds':g(5),'ret':b[192:].hex()}
