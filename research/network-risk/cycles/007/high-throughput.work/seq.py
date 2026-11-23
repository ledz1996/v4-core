from stubs import *
def mk(g):
 return asm([0x80,0x20,'MSTORE',
 ('label','loop'),'CALLDATASIZE',0,'MLOAD','LT','ISZERO',('ref','end'),'JUMPI',
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
 ('label','end'),0x80,0x20,'MLOAD','SUB',0x80,'RETURN'])
M=mk('GAS')
M1=mk(1_000_000)
def rec(kind,target,data='',value=0):
    d=bytes.fromhex(data)
    return bytes([kind]).hex()+target[2:].rjust(40,'0').lower()+w(value)+len(d).to_bytes(2,'big').hex()+data
def seq_req(chain,recs,where='A',v_pm_to_a=0,a_balance=0,gas=5_000_000,blk='latest',extra=None,frm=None,M=None):
    M=M or globals()['M']
    """where='A': EOA -> PM(F) -> A(M) runs recs. where='PM': EOA -> PM(M) runs recs."""
    pm=PM[chain]; body=''.join(recs)
    if where=='A':
        ov={pm:{'code':F},A:{'code':M,'balance':hex(a_balance)},EOA:{'balance':hex(10**21)},CAL:{'code':C}}
        data='0x'+A[2:]+w(v_pm_to_a)+body
    else:
        ov={pm:{'code':M},EOA:{'balance':hex(10**21)},CAL:{'code':C}}
        data='0x'+body
    if extra: ov.update(extra)
    return ('eth_call',[{'from':frm or EOA,'to':pm,'data':data,'gas':hex(gas)},blk,ov])
def seq_parse(r,where='A'):
    if 'error' in r: return [{'err':json.dumps(r['error'])[:200]}]
    b=bytes.fromhex(r['result'][2:])
    if where=='A':
        ok=int.from_bytes(b[:32],'big'); b=b[32:]
        if not ok: return [{'pmfail':b.hex()[:200]}]
    out=[]
    for i in range(0,len(b),128):
        out.append({'ok':int.from_bytes(b[i:i+32],'big'),'rds':int.from_bytes(b[i+32:i+64],'big'),'ret':b[i+64:i+128].hex()})
    return out
def run(chain,recs,**kw):
    where=kw.get('where','A')
    return seq_parse(rpc(*seq_req(chain,recs,**kw),URL[chain],raw=True),where)
if __name__=='__main__':
    for chain in (143,4326):
        r=run(chain,[rec(0,CAL,'',5),rec(1,CAL),rec(2,CAL),rec(3,CAL,'',3)],v_pm_to_a=100)
        for x in r: print(chain,x)
