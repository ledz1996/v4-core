"""print the instructions of IR blocks with source lines: python3 dis.py 0x173e 0x1755 ..."""
import sys, blocks as B
NAMES = {0x01:'ADD',0x02:'MUL',0x03:'SUB',0x04:'DIV',0x05:'SDIV',0x06:'MOD',0x07:'SMOD',0x08:'ADDMOD',0x09:'MULMOD',0x0a:'EXP',0x0b:'SIGNEXTEND',0x10:'LT',0x11:'GT',0x12:'SLT',0x13:'SGT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x1d:'SAR',0x20:'KECCAK256',0x30:'ADDRESS',0x31:'BALANCE',0x33:'CALLER',0x34:'CALLVALUE',0x35:'CALLDATALOAD',0x36:'CALLDATASIZE',0x37:'CALLDATACOPY',0x3d:'RETURNDATASIZE',0x3e:'RETURNDATACOPY',0x47:'SELFBALANCE',0x50:'POP',0x51:'MLOAD',0x52:'MSTORE',0x54:'SLOAD',0x55:'SSTORE',0x56:'JUMP',0x57:'JUMPI',0x5a:'GAS',0x5b:'JUMPDEST',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY',0x5f:'PUSH0',0xf1:'CALL',0xf3:'RETURN',0xfa:'STATICCALL',0xfd:'REVERT',0xfe:'INVALID',0x00:'STOP',0xa1:'LOG1',0xa2:'LOG2',0xa3:'LOG3',0xa4:'LOG4'}
def name(o):
    if 0x60 <= o <= 0x7f: return f'PUSH{o-0x5f}'
    if 0x80 <= o <= 0x8f: return f'DUP{o-0x7f}'
    if 0x90 <= o <= 0x9f: return f'SWAP{o-0x8f}'
    return NAMES.get(o, hex(o))
def ins(pc):
    o = B.code[pc]; n = name(o)
    if 0x60 <= o <= 0x7f: n += ' 0x' + B.code[pc+1:pc+1+o-0x5f].hex()
    return n
if __name__ != "__main__": sys.argv = sys.argv[:1]
offs = B.block_offsets(sys.argv[1]) if len(sys.argv) > 1 else []; sp = B.block_spans(offs) if offs else {}
for a in sys.argv[2:]:
    a = int(a, 16); print(f'--- block {a:#x}')
    for p in sp[a]: print(f'  {p:#06x} {ins(p):40s} {B.where(p)} {B.JT.get(p)}')
