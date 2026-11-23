# Minimal EVM disassembler for reading small unverified contracts.
import sys
N = {0x00:'STOP',0x01:'ADD',0x02:'MUL',0x03:'SUB',0x04:'DIV',0x05:'SDIV',0x06:'MOD',0x07:'SMOD',0x08:'ADDMOD',0x09:'MULMOD',0x0a:'EXP',0x0b:'SIGNEXTEND',0x10:'LT',0x11:'GT',0x12:'SLT',0x13:'SGT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x1d:'SAR',0x20:'KECCAK256',0x30:'ADDRESS',0x31:'BALANCE',0x32:'ORIGIN',0x33:'CALLER',0x34:'CALLVALUE',0x35:'CALLDATALOAD',0x36:'CALLDATASIZE',0x37:'CALLDATACOPY',0x38:'CODESIZE',0x39:'CODECOPY',0x3a:'GASPRICE',0x3b:'EXTCODESIZE',0x3c:'EXTCODECOPY',0x3d:'RETURNDATASIZE',0x3e:'RETURNDATACOPY',0x3f:'EXTCODEHASH',0x40:'BLOCKHASH',0x41:'COINBASE',0x42:'TIMESTAMP',0x43:'NUMBER',0x44:'PREVRANDAO',0x45:'GASLIMIT',0x46:'CHAINID',0x47:'SELFBALANCE',0x48:'BASEFEE',0x50:'POP',0x51:'MLOAD',0x52:'MSTORE',0x53:'MSTORE8',0x54:'SLOAD',0x55:'SSTORE',0x56:'JUMP',0x57:'JUMPI',0x58:'PC',0x59:'MSIZE',0x5a:'GAS',0x5b:'JUMPDEST',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY',0x5f:'PUSH0',0xa0:'LOG0',0xa1:'LOG1',0xa2:'LOG2',0xa3:'LOG3',0xa4:'LOG4',0xf0:'CREATE',0xf1:'CALL',0xf2:'CALLCODE',0xf3:'RETURN',0xf4:'DELEGATECALL',0xf5:'CREATE2',0xfa:'STATICCALL',0xfd:'REVERT',0xfe:'INVALID',0xff:'SELFDESTRUCT'}
for i in range(1, 33): N[0x5f + i] = 'PUSH%d' % i
for i in range(1, 17): N[0x7f + i] = 'DUP%d' % i; N[0x8f + i] = 'SWAP%d' % i
def dis(code):
    b = bytes.fromhex(code[2:] if code.startswith('0x') else code); i = 0; out = []
    while i < len(b):
        op = b[i]; n = N.get(op, 'UNK_%02x' % op)
        if 0x60 <= op <= 0x7f:
            k = op - 0x5f; out.append((i, n, b[i + 1:i + 1 + k].hex())); i += 1 + k
        else: out.append((i, n, None)); i += 1
    return out
def show(code, compact=True):
    line = []
    for pc, n, a in dis(code):
        if n == 'JUMPDEST':
            if line: print(' '.join(line)); line = []
            line.append('%04x:' % pc)
        else: line.append(n + ('_' + a if a else ''))
        if n in ('JUMP', 'RETURN', 'REVERT', 'STOP', 'INVALID', 'SELFDESTRUCT'):
            print(' '.join(line)); line = []
    if line: print(' '.join(line))
if __name__ == '__main__':
    from lib import *
    from state import url
    cid = int(sys.argv[1]); x = sys.argv[2]
    c = rpc(url(cid), 'eth_getCode', [x, 'latest'])
    show(c)
