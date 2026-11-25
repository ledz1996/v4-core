import json,sys
b=json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))
code=bytes.fromhex(b['runtime'].replace('0x','') if isinstance(b['runtime'],str) else b['runtime']['object'].replace('0x',''))
names={0:'STOP',1:'ADD',2:'MUL',3:'SUB',4:'DIV',5:'SDIV',6:'MOD',7:'SMOD',8:'ADDMOD',9:'MULMOD',10:'EXP',11:'SIGNEXTEND',0x10:'LT',0x11:'GT',0x12:'SLT',0x13:'SGT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x1d:'SAR',0x20:'KECCAK256',0x30:'ADDRESS',0x31:'BALANCE',0x32:'ORIGIN',0x33:'CALLER',0x34:'CALLVALUE',0x35:'CALLDATALOAD',0x36:'CALLDATASIZE',0x37:'CALLDATACOPY',0x38:'CODESIZE',0x39:'CODECOPY',0x3a:'GASPRICE',0x3b:'EXTCODESIZE',0x3d:'RETURNDATASIZE',0x3e:'RETURNDATACOPY',0x3f:'EXTCODEHASH',0x47:'SELFBALANCE',0x50:'POP',0x51:'MLOAD',0x52:'MSTORE',0x53:'MSTORE8',0x54:'SLOAD',0x55:'SSTORE',0x56:'JUMP',0x57:'JUMPI',0x58:'PC',0x59:'MSIZE',0x5a:'GAS',0x5b:'JUMPDEST',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY',0x5f:'PUSH0',0xf0:'CREATE',0xf1:'CALL',0xf3:'RETURN',0xfa:'STATICCALL',0xfd:'REVERT',0xfe:'INVALID'}
for i in range(1,33): names[0x5f+i]='PUSH%d'%i
for i in range(16): names[0x80+i]='DUP%d'%(i+1); names[0x90+i]='SWAP%d'%(i+1)
for i in range(5): names[0xa0+i]='LOG%d'%i
ins=[];pc=0
while pc<len(code):
  op=code[pc]; n=names.get(op,'0x%02x'%op)
  if 0x60<=op<=0x7f:
    k=op-0x5f; ins.append((pc,n+' 0x'+code[pc+1:pc+1+k].hex())); pc+=1+k
  else: ins.append((pc,n)); pc+=1
a,bb=int(sys.argv[1]),int(sys.argv[2])
for p,n in ins:
  if a<=p<=bb: print(p,n)
