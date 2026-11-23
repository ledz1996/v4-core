# Minimal EVM assembler for read-only measuring stubs used with eth_call state overrides.
# Same token syntax as cycles/005/theme-claim-operators.work/asm.py (numbers push, @label pushes a 2 byte target, label: is a JUMPDEST).
OPS = dict(STOP=0x00, ADD=0x01, MUL=0x02, SUB=0x03, DIV=0x04, LT=0x10, GT=0x11, EQ=0x14, ISZERO=0x15, AND=0x16, OR=0x17, NOT=0x19, SHL=0x1b, SHR=0x1c,
           ADDRESS=0x30, BALANCE=0x31, ORIGIN=0x32, CALLER=0x33, CALLVALUE=0x34, CALLDATALOAD=0x35, CALLDATASIZE=0x36, CALLDATACOPY=0x37, EXTCODESIZE=0x3b,
           RETURNDATASIZE=0x3d, RETURNDATACOPY=0x3e, EXTCODEHASH=0x3f, SELFBALANCE=0x47, POP=0x50, MLOAD=0x51, MSTORE=0x52, JUMP=0x56, JUMPI=0x57,
           GAS=0x5a, JUMPDEST=0x5b, TLOAD=0x5c, TSTORE=0x5d, CALL=0xf1, RETURN=0xf3, DELEGATECALL=0xf4, STATICCALL=0xfa, REVERT=0xfd)
for i in range(1, 17): OPS['DUP%d' % i] = 0x7f + i; OPS['SWAP%d' % i] = 0x8f + i
def assemble(src):
    toks = []
    for line in src.split('\n'):
        line = line.split(';')[0]
        toks += line.split()
    items = []; pc = 0; labels = {}
    for t in toks:
        if t.endswith(':'):
            labels[t[:-1]] = pc; items.append(('op', 0x5b)); pc += 1
        elif t.startswith('@'):
            items.append(('lab', t[1:])); pc += 3
        elif t.startswith('0x') or t.isdigit():
            v = int(t, 0); n = max(1, (v.bit_length() + 7) // 8)
            items.append(('push', v, n)); pc += 1 + n
        else:
            items.append(('op', OPS[t])); pc += 1
    out = bytearray()
    for it in items:
        if it[0] == 'op': out.append(it[1])
        elif it[0] == 'lab': out.append(0x61); out += labels[it[1]].to_bytes(2, 'big')
        else: out.append(0x5f + it[2]); out += it[1].to_bytes(it[2], 'big')
    return '0x' + out.hex()
