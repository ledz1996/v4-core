from asm import asm
from lib import *
import sys
TT='0x7e57000000000000000000000000000000007e57'; DD='0xd41be40000000000000000000000000000d41be4'; NOCODE='0x00000000000000000000000000000000deadc0de'; EOA='0xe0a0000000000000000000000000000000000e0a'
tt=asm([0,'CALLDATALOAD',248,'SHR']+sum([['DUP1',i,'EQ',('ref',f'l{i}'),'JUMPI'] for i in range(1,9)],[])+['STOP',
 ('label','l1'),0xAA,0,'TSTORE',0,0,'REVERT',
 ('label','l2'),0xBB,0,'TSTORE','INVALID',
 ('label','l3'),0xCC,0,'TSTORE','STOP',
 ('label','l4'),0,'TLOAD',0,'MSTORE',32,0,'RETURN',
 ('label','l5'),3,0,'MSTORE8',0,0,1,0,0,'ADDRESS','GAS','CALL','POP',0,0,'REVERT',
 ('label','l6'),'GAS',0,'MSTORE',32,0,'RETURN',
 ('label','l7'),0xDD,0,'TSTORE',('label','loop'),('ref','loop'),'JUMP',
 ('label','l8'),'CALLVALUE',0,'MSTORE','SELFBALANCE',32,'MSTORE',64,0,'RETURN'])
steps=[];names=[]
n=[0]
def out(tok,name):
    steps.extend(tok+[0x200+32*n[0],'MSTORE']); names.append(name); n[0]+=1
def call(kind,addr,byte,name,value=0,gas='GAS'):
    pre=[0,0x40,'MSTORE',0,0x60,'MSTORE',byte,0,'MSTORE8']
    g=[gas] if isinstance(gas,str) else [gas]
    if kind=='CALL': c=[64,0x40,1,0,value,addr]+g+['CALL']
    elif kind=='STATICCALL': c=[64,0x40,1,0,addr]+g+['STATICCALL']
    elif kind=='DELEGATECALL': c=[64,0x40,1,0,addr]+g+['DELEGATECALL']
    out(pre+c,name+':success'); out(['RETURNDATASIZE'],name+':rds'); out([0x40,'MLOAD'],name+':ret0'); 
call('CALL',TT,1,'s1 tstore then REVERT')
call('CALL',TT,4,'s2 tload after reverted tstore')
call('CALL',TT,2,'s3 tstore then INVALID',gas=100000)
call('CALL',TT,4,'s4 tload after invalid')
call('CALL',TT,7,'s5 tstore then out of gas',gas=50000)
call('CALL',TT,4,'s6 tload after oog')
call('CALL',TT,5,'s7 nested ok tstore, parent reverts',gas=200000)
call('CALL',TT,4,'s8 tload after parent revert')
call('STATICCALL',TT,3,'s9 tstore under STATICCALL',gas=100000)
call('CALL',TT,4,'s10 tload after static attempt')
call('CALL',TT,3,'s11 tstore success')
call('CALL',TT,4,'s12 tload in later call same tx')
call('STATICCALL',TT,4,'s13 tload under STATICCALL')
call('DELEGATECALL',TT,3,'s14 delegatecall tstore')
out([0,'TLOAD'],'s14b own tload after delegatecall tstore')
out(['GAS'],'s15a gas before')
call('CALL',TT,6,'s15 gas seen by callee, all gas forwarded')
out(['GAS'],'s15c gas after')
call('CALL',TT,8,'s16 value call: callvalue',value=5)
out([0x60,'MLOAD'],'s16b callee selfbalance')
call('CALL',NOCODE,0,'s17 value call to address without code',value=3)
out([NOCODE,'BALANCE'],'s17b balance of codeless address')
call('CALL',TT,8,'s18 value above balance',value=10**30)
call('CALL',TT,6,'s19 value call with gas 0: stipend seen',value=1,gas=0)
out(['SELFBALANCE'],'s20 selfbalance at end')
out(['CALLVALUE'],'s21 callvalue')
# mcopy/push0 check: mstore 0x1122 at 0, mcopy to 0x20
steps+=[0x1122,0,'MSTORE',32,0,0x20,'MCOPY']; out([0x20,'MLOAD'],'s22 mcopy')
steps+=[32*n[0],0x200,'RETURN']
dd=asm(steps)
def run(url,blk='latest'):
    ov={TT:{'code':tt},DD:{'code':dd},EOA:{'balance':hex(10**20)}}
    r=rpc('eth_call',[{'from':EOA,'to':DD,'value':hex(1000),'gas':hex(2_000_000)},blk,ov],url=url,raw=True)
    if 'error' in r: return r
    b=bytes.fromhex(r['result'][2:])
    return {names[i]:int.from_bytes(b[32*i:32*i+32],'big') for i in range(len(names))}
if __name__=='__main__':
    urls={'official':OFF,'archive':ARCH}
    if len(sys.argv)>1: urls={sys.argv[1]:sys.argv[2]}
    res={k:run(u) for k,u in urls.items()}
    json.dump(res,open('raw/opprobe_%s.json'%('_'.join(urls)),'w'),indent=1)
    ks=list(res)
    if any('error' in res[k] for k in ks): print(res); sys.exit()
    for nme in names: print(f"{nme:55}", *[hex(res[k][nme]) if res[k][nme]>9 else res[k][nme] for k in ks])
