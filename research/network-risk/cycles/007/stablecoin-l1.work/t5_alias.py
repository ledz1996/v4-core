# L-197: call input borrowing in evm2 (Tempo) against revm (Arc). The same override code and calldata run on both endpoints, read-only.
import json, hashlib
from lib import *
from asm import assemble, OPS
OPS.update(dict(MSIZE=0x59, NOT=0x19, XOR=0x18, KECCAK256=0x20, CALLCODE=0xf2, CODECOPY=0x39, TLOAD=0x5c, TSTORE=0x5d, MCOPY=0x5e, MSTORE8=0x53, CALLVALUE=0x34))
ECHO='0x7e57000000000000000000000000000000000ec0'; MID='0x7e57000000000000000000000000000000000ec1'; TOP='0x7e57000000000000000000000000000000000ec2'
# ECHO: grows its own memory to 64 kB, then returns its calldata
echo=assemble('1 0xffe0 MSTORE  CALLDATASIZE 0 0 CALLDATACOPY  CALLDATASIZE 0 RETURN')
# MID: copies calldata to 0x100, calls ECHO with input and output on the same range, overwrites the input range of ITS caller is impossible,
# then re-reads its own calldata (still served from the caller's memory) and returns: echo output ++ second copy of calldata
mid=assemble('''
CALLDATASIZE 0 0x100 CALLDATACOPY
CALLDATASIZE 0x100 CALLDATASIZE 0x100 0 %s GAS CALL POP
1 0x7fe0 MSTORE
CALLDATASIZE 0 CALLDATASIZE 0x100 ADD CALLDATACOPY
CALLDATASIZE 2 MUL 0x100 RETURN
''' % ECHO)
# TOP: variant in calldata word 0 selects the output offset relative to the input (0 = same range, 16 = shifted, 0x1000 = disjoint)
top=assemble('''
0x20 CALLDATASIZE SUB 0x20 0x100 CALLDATACOPY
0x20 CALLDATASIZE SUB 2 MUL   0 CALLDATALOAD 0x100 ADD   0x20 CALLDATASIZE SUB   0x100   0 %s GAS CALL
0x80 MSTORE
RETURNDATASIZE 0xa0 MSTORE
RETURNDATASIZE 0 0x4000 RETURNDATACOPY
; second call: static, input and output on the same range, to MID again, after memory was changed
0xdeadbeef 0x100 MSTORE
0x20 CALLDATASIZE SUB 0x100 0x20 CALLDATASIZE SUB 0x100 %s GAS STATICCALL
0xc0 MSTORE
0x6000 0x80 RETURN
''' % (MID, MID))
ov={ECHO:{'code':echo},MID:{'code':mid},TOP:{'code':top}}
urls={'Tempo (evm2)':net(4217)['rpc'],'Arc (revm)':'https://arc.drpc.org'}
res={}
import random; random.seed(7)
cases=[]
for n in (1,31,32,33,68,100,256,1000):
    for off in (0,16,0x20,0x1000):
        cases.append((n,off,bytes(random.getrandbits(8) for _ in range(n)).hex()))
bad=0
for n,off,pat in cases:
    outs={}
    for name,u in urls.items():
        r=rpc(u,'eth_call',[{'from':'0x7e57000000000000000000000000000000000a00','to':TOP,'data':'0x'+w(off)+pat,'gas':hex(3_000_000)},'latest',ov])
        outs[name]=r.get('result') or json.dumps(r.get('error'))
    hs={k:hashlib.sha256(v.encode()).hexdigest()[:12] for k,v in outs.items()}
    same=len(set(outs.values()))==1; bad+=(not same)
    res['%d_%d'%(n,off)]={'same':same,'hash':hs,'len':{k:len(v) for k,v in outs.items()}}
    if not same: print('DIFF',n,off,hs,{k:v[:200] for k,v in outs.items()})
print('cases',len(cases),'differences',bad)
print({k:v["len"] for k,v in list(res.items())[:6]})
json.dump(res,open('raw/t5_alias.json','w'),indent=1)
