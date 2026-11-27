"""Cycle 31: per un-entered value block (cycle 30 notentered-classified.json), the instructions with their EVM opcode
(read from the runtime bytecode at the logged pc) and the logged state count. usage: blockops.py states.jsonl out.json"""
import sys, json, collections
C = '/home/user/v4-core/research/network-risk/cycles'
code = bytes.fromhex(open(C + '/027/theme-monad-engine-agreement.work/out/pm-runtime.hex').read().strip().removeprefix('0x'))
NAMES = {0x00:'STOP',0x01:'ADD',0x02:'MUL',0x03:'SUB',0x04:'DIV',0x05:'SDIV',0x06:'MOD',0x07:'SMOD',0x08:'ADDMOD',0x09:'MULMOD',0x0a:'EXP',0x0b:'SIGNEXTEND',
 0x10:'LT',0x11:'GT',0x12:'SLT',0x13:'SGT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x1d:'SAR',
 0x20:'KECCAK256',0x30:'ADDRESS',0x31:'BALANCE',0x32:'ORIGIN',0x33:'CALLER',0x34:'CALLVALUE',0x35:'CALLDATALOAD',0x36:'CALLDATASIZE',0x37:'CALLDATACOPY',0x38:'CODESIZE',0x39:'CODECOPY',0x3a:'GASPRICE',0x3b:'EXTCODESIZE',0x3c:'EXTCODECOPY',0x3d:'RETURNDATASIZE',0x3e:'RETURNDATACOPY',0x3f:'EXTCODEHASH',
 0x40:'BLOCKHASH',0x41:'COINBASE',0x42:'TIMESTAMP',0x43:'NUMBER',0x44:'PREVRANDAO',0x45:'GASLIMIT',0x46:'CHAINID',0x47:'SELFBALANCE',0x48:'BASEFEE',0x49:'BLOBHASH',0x4a:'BLOBBASEFEE',
 0x50:'POP',0x51:'MLOAD',0x52:'MSTORE',0x53:'MSTORE8',0x54:'SLOAD',0x55:'SSTORE',0x56:'JUMP',0x57:'JUMPI',0x58:'PC',0x59:'MSIZE',0x5a:'GAS',0x5b:'JUMPDEST',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY',0x5f:'PUSH0',
 0xf0:'CREATE',0xf1:'CALL',0xf2:'CALLCODE',0xf3:'RETURN',0xf4:'DELEGATECALL',0xf5:'CREATE2',0xfa:'STATICCALL',0xfd:'REVERT',0xfe:'INVALID',0xff:'SELFDESTRUCT'}
for i in range(32): NAMES[0x60+i] = 'PUSH%d' % (i+1)
for i in range(16): NAMES[0x80+i] = 'DUP%d' % (i+1); NAMES[0x90+i] = 'SWAP%d' % (i+1)
for i in range(5): NAMES[0xa0+i] = 'LOG%d' % i
def opname(pc): return NAMES.get(code[pc], hex(code[pc])) if 0 <= pc < len(code) else 'END'
if __name__ == '__main__':
    ne = json.load(open(C + '/030/theme-monad-mined-native-coverage.work/out/notentered-classified.json'))
    val = [b for b in ne['blocks'] if b['class'] == 'value']
    changed = {b['block'] for b in val if b['changed167']}
    want = {int(b['block'], 16) for b in val}
    per = collections.defaultdict(list)
    for l in open(sys.argv[1]):
        d = json.loads(l)
        if d['b'] in want: per[d['b']].append(d)
    out = {}; tot = collections.Counter()
    for b in sorted(want):
        rows = per.get(b, [])
        ops = [opname(d['pc']) if d['w'] == 'i' else ('TERM:%d' % (d['op'] - 1000) if d['w'] == 't' else 'ENTRY') for d in rows]
        out[hex(b)] = {'changed167': hex(b) in changed, 'states': len(rows), 'ops': ops}
        tot.update(o for o in ops)
    json.dump({'blocks': out, 'opcount': dict(tot.most_common())}, open(sys.argv[2], 'w'), indent=1)
    print(len(want), 'blocks;', sum(len(v['ops']) for v in out.values()), 'logged states;', 'missing', [k for k, v in out.items() if not v['states']])
    print(dict(tot.most_common()))
