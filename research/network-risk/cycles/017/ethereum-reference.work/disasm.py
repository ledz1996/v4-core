import json,sys
c=bytes.fromhex(json.load(open(sys.argv[1]))['result'][2:])
N={0:'STOP',1:'ADD',2:'MUL',3:'SUB',4:'DIV',0x10:'LT',0x11:'GT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x30:'ADDRESS',0x31:'BALANCE',0x32:'ORIGIN',0x33:'CALLER',0x34:'CALLVALUE',0x35:'CALLDATALOAD',0x36:'CALLDATASIZE',0x37:'CALLDATACOPY',0x3d:'RETURNDATASIZE',0x3e:'RETURNDATACOPY',0x47:'SELFBALANCE',0x50:'POP',0x51:'MLOAD',0x52:'MSTORE',0x54:'SLOAD',0x55:'SSTORE',0x56:'JUMP',0x57:'JUMPI',0x5a:'GAS',0x5b:'JUMPDEST',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY',0x5f:'PUSH0',0xf1:'CALL',0xf3:'RETURN',0xfa:'STATICCALL',0xfd:'REVERT',0xfe:'INVALID',0xa0:'LOG0',0xa1:'LOG1',0xa2:'LOG2',0xa3:'LOG3'}
for i in range(0x80,0x90): N[i]='DUP%d'%(i-0x7f)
for i in range(0x90,0xa0): N[i]='SWAP%d'%(i-0x8f)
a=int(sys.argv[2],16); b=int(sys.argv[3],16)
i=0;out=[]
while i<len(c):
    o=c[i]
    if 0x60<=o<=0x7f:
        n=o-0x5f; s=f'{i:x}:PUSH{n} {c[i+1:i+1+n].hex()}'; j=i+1+n
    else:
        s=f'{i:x}:{N.get(o,hex(o))}'; j=i+1
    if a<=i<b: out.append(s)
    i=j
print(' | '.join(out))
