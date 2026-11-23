from seq import *
def mkU(pm,g=1_500_000):
    pmi=int(pm,16)
    return asm(['CALLER','0x'+pm[2:].lower(),'EQ',('ref','cb'),'JUMPI',
     # outer: forward to PM.unlock(records)
     '0x'+sel('unlock(bytes)'),224,'SHL',0x100,'MSTORE', 0x20,0x104,'MSTORE','CALLDATASIZE',0x124,'MSTORE',
     'CALLDATASIZE',0,0x144,'CALLDATACOPY',
     0,0,'CALLDATASIZE',0x44,'ADD',0x100,0,'0x'+pm[2:].lower(),'GAS','CALL',
     'RETURNDATASIZE',0,0,'RETURNDATACOPY',('ref','okret'),'JUMPI','RETURNDATASIZE',0,'REVERT',
     ('label','okret'),'RETURNDATASIZE',0,'RETURN',
     ('label','cb'),68,0,'MSTORE',0x100,0x20,'MSTORE',36,'CALLDATALOAD',68,'ADD',0x60,'MSTORE',
     ('label','loop'),0x60,'MLOAD',0,'MLOAD','LT','ISZERO',('ref','end'),'JUMPI',
     0,'MLOAD',53,'ADD','CALLDATALOAD',240,'SHR',0x40,'MSTORE',
     0x40,'MLOAD',0,'MLOAD',55,'ADD',0x4000,'CALLDATACOPY',
     0,'MLOAD','CALLDATALOAD',248,'SHR',
     'DUP1',1,'EQ',('ref','static'),'JUMPI','DUP1',2,'EQ',('ref','deleg'),'JUMPI','DUP1',3,'EQ',('ref','callcode'),'JUMPI',
     'POP',0,0,0x40,'MLOAD',0x4000,0,'MLOAD',21,'ADD','CALLDATALOAD',0,'MLOAD',1,'ADD','CALLDATALOAD',96,'SHR',g,'CALL',('ref','done'),'JUMP',
     ('label','static'),'POP',0,0,0x40,'MLOAD',0x4000,0,'MLOAD',1,'ADD','CALLDATALOAD',96,'SHR',g,'STATICCALL',('ref','done'),'JUMP',
     ('label','deleg'),'POP',0,0,0x40,'MLOAD',0x4000,0,'MLOAD',1,'ADD','CALLDATALOAD',96,'SHR',g,'DELEGATECALL',('ref','done'),'JUMP',
     ('label','callcode'),'POP',0,0,0x40,'MLOAD',0x4000,0,'MLOAD',21,'ADD','CALLDATALOAD',0,'MLOAD',1,'ADD','CALLDATALOAD',96,'SHR',g,'CALLCODE',
     ('label','done'),0x20,'MLOAD','MSTORE',
     'RETURNDATASIZE',0x20,'MLOAD',32,'ADD','MSTORE',
     0,0x20,'MLOAD',64,'ADD','MSTORE',0,0x20,'MLOAD',96,'ADD','MSTORE',
     'RETURNDATASIZE','DUP1',64,'GT',('ref','cp'),'JUMPI','POP',64,
     ('label','cp'),0,0x20,'MLOAD',64,'ADD','RETURNDATACOPY',
     0x20,'MLOAD',128,'ADD',0x20,'MSTORE',
     0,'MLOAD',55,'ADD',0x40,'MLOAD','ADD',0,'MSTORE',('ref','loop'),'JUMP',
     ('label','end'),0x20,0xc0,'MSTORE',0x100,0x20,'MLOAD','SUB',0xe0,'MSTORE',
     0x40,0x100,0x20,'MLOAD','SUB','ADD',0xc0,'RETURN'])
X='0x0c0ffee000000000000000000000000000c0ffee'   # the ordinary account (contract or delegated EOA)
UA='0x00000000000000000000000000000000000057ab'  # where the stub code lives when X is a delegated account
def unlock_call(chain,recs,x_balance=10**20,delegated=False,gas=25_000_000,blk='latest',extra=None,post=None,g=1_500_000):
    """EOA -> X: X calls PoolManager.unlock with the real PoolManager code; in the callback X runs recs.
    post: records run by a top-level sequencer O after the unlock returned (same eth_call)."""
    pm=PM[chain]; U=mkU(pm,g)
    ov={EOA:{'balance':hex(10**21)},CAL:{'code':C}}
    if delegated:
        ov[UA]={'code':U}; ov[X]={'code':'0xef0100'+UA[2:],'balance':hex(x_balance)}
    else:
        ov[X]={'code':U,'balance':hex(x_balance)}
    if extra: ov.update(extra)
    O='0x000000000000000000000000000000000000070b'
    ov[O]={'code':mk(g*12 if not post else 'GAS') if False else M}
    body=''.join(recs)
    top=[rec(0,X,body)]+(post or [])
    r=rpc('eth_call',[{'from':EOA,'to':O,'data':'0x'+''.join(top),'gas':hex(gas)},blk,ov],URL[chain],raw=True)
    if 'error' in r: return {'err':json.dumps(r['error'])[:300]}
    b=bytes.fromhex(r['result'][2:])
    outer=[{'ok':int.from_bytes(b[i:i+32],'big'),'rds':int.from_bytes(b[i+32:i+64],'big'),'ret':b[i+64:i+128].hex()} for i in range(0,len(b),128)]
    return {'outer':outer}
def unlock_inner(chain,recs,**kw):
    """returns the per-record results of the callback (second eth_call that targets X directly)"""
    pm=PM[chain]; U=mkU(pm,kw.pop('g',1_500_000))
    delegated=kw.pop('delegated',False); x_balance=kw.pop('x_balance',10**20); extra=kw.pop('extra',None)
    ov={EOA:{'balance':hex(10**21)},CAL:{'code':C}}
    if delegated:
        ov[UA]={'code':U}; ov[X]={'code':'0xef0100'+UA[2:],'balance':hex(x_balance)}
    else:
        ov[X]={'code':U,'balance':hex(x_balance)}
    if extra: ov.update(extra)
    r=rpc('eth_call',[{'from':kw.pop('frm',EOA),'to':X,'data':'0x'+''.join(recs),'gas':hex(kw.pop('gas',25_000_000))},kw.pop('blk','latest'),ov],URL[chain],raw=True)
    if 'error' in r: return [{'err':json.dumps(r['error'])[:300]}]
    b=bytes.fromhex(r['result'][2:])
    # abi: offset, len, data
    ln=int.from_bytes(b[32:64],'big'); d=b[64:64+ln]
    return [{'ok':int.from_bytes(d[i:i+32],'big'),'rds':int.from_bytes(d[i+32:i+64],'big'),'ret':d[i+64:i+128].hex()} for i in range(0,len(d),128)]
