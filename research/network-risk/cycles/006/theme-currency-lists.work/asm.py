# Minimal EVM assembler for read-only measuring stubs used with eth_call state overrides.
OPS = dict(STOP=0x00, ADD=0x01, MUL=0x02, SUB=0x03, DIV=0x04, LT=0x10, GT=0x11, EQ=0x14, ISZERO=0x15, AND=0x16, OR=0x17, SHL=0x1b, SHR=0x1c,
           ADDRESS=0x30, BALANCE=0x31, CALLER=0x33, CALLDATALOAD=0x35, CALLDATASIZE=0x36, CALLDATACOPY=0x37, EXTCODESIZE=0x3b, RETURNDATASIZE=0x3d, RETURNDATACOPY=0x3e,
           EXTCODEHASH=0x3f, TIMESTAMP=0x42, NUMBER=0x43, SELFBALANCE=0x47, POP=0x50, MLOAD=0x51, MSTORE=0x52, SLOAD=0x54, SSTORE=0x55, JUMP=0x56, JUMPI=0x57, GAS=0x5a, JUMPDEST=0x5b,
           CALL=0xf1, RETURN=0xf3, DELEGATECALL=0xf4, STATICCALL=0xfa, REVERT=0xfd)
for i in range(1, 17): OPS['DUP%d' % i] = 0x7f + i; OPS['SWAP%d' % i] = 0x8f + i
def assemble(src):
    toks = []
    for line in src.split('\n'):
        line = line.split(';')[0]
        toks += line.split()
    # pass 1: sizes
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

# Placed at the PoolManager address. calldata: word0 = sink, then one token per word.
# For each token writes 4 words: balance before, flags, balance after, balance of sink after.
# flags: 1 balanceOf answered, 2 transfer accepted by the rule of Currency.sol:68, 4 call did not revert.
XFER = assemble('''
0x20                         ; i (calldata offset)
0x400                        ; out pointer            [i out]
loop:
DUP2 CALLDATASIZE EQ @end JUMPI
DUP2 CALLDATALOAD            ; [i out tok]
; balanceOf(self)
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
ADDRESS 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL     ; [i out tok ok]
0x1f RETURNDATASIZE GT AND                     ; ok1
DUP1 0x60 MSTORE                               ; flags
POP
0x40 MLOAD DUP3 MSTORE                         ; out[0]=bal
; transfer(sink, bal)
0xa9059cbb00000000000000000000000000000000000000000000000000000000 0x80 MSTORE
0 CALLDATALOAD 0x84 MSTORE
0x40 MLOAD 0xa4 MSTORE
0 0x100 MSTORE
0x20 0x100 0x44 0x80 0 DUP6 0x1e8480 CALL       ; [i out tok ok2]
DUP1 4 MUL 0x60 MLOAD OR 0x60 MSTORE
RETURNDATASIZE ISZERO                          ; [.. ok2 rds0]
0x1f RETURNDATASIZE GT 0x100 MLOAD 1 EQ AND OR  ; [.. ok2 good]
AND 2 MUL 0x60 MLOAD OR                        ; flags
DUP3 0x20 ADD MSTORE                           ; out[1]=flags   [i out tok]
; balanceOf(self) after
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL POP
0x40 MLOAD DUP3 0x40 ADD MSTORE
; balanceOf(sink) after
0 CALLDATALOAD 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL POP
0x40 MLOAD DUP3 0x60 ADD MSTORE
POP                                            ; [i out]
0x80 ADD SWAP1 0x20 ADD SWAP1
@loop JUMP
end:
0x400 DUP2 SUB 0x400 RETURN
''')
if __name__ == '__main__':
    print(XFER, len(XFER) // 2 - 1)

SLOADER4 = assemble('''
0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc SLOAD 0 MSTORE
0xa3f0ad74e5423aebfd80e3ef4346578335a9a72aeaee59ff6cb3582b35133d50 SLOAD 0x20 MSTORE
0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3 SLOAD 0x40 MSTORE
0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7 SLOAD 0x60 MSTORE
0x80 0 RETURN
''')
# for every address word in calldata: STATICCALL with empty calldata, keep 0x80 bytes of return data
DRIVER80 = assemble('''
0
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
0x80 DUP2 4 MUL 0 0 DUP5 CALLDATALOAD GAS STATICCALL POP
0x20 ADD
@loop JUMP
end:
CALLDATASIZE 4 MUL 0 RETURN
''')
# word0 = left aligned selector; for every following address word: STATICCALL(selector), keep 0x20 bytes at 0x100 + offset
DRIVERSEL = assemble('''
0 CALLDATALOAD 0 MSTORE
0x20
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
0 DUP2 0x100 ADD MSTORE
0x20 DUP2 0x100 ADD 4 0 DUP5 CALLDATALOAD 0x7a120 STATICCALL POP
0x20 ADD
@loop JUMP
end:
0x20 CALLDATASIZE SUB 0x120 RETURN
''')

# Forwarder used as the ordinary account: word0 = target, rest = calldata for the target. Returns the success flag.
FWD = assemble('''
0x20 CALLDATASIZE SUB
DUP1 0x20 0 CALLDATACOPY
0 0 DUP3 0 0 0 CALLDATALOAD GAS CALL
0 MSTORE 0x20 0 RETURN
''')
def _bal(addr_expr, dst):
    return '''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
%s 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 0 CALLDATALOAD GAS STATICCALL POP
0x40 MLOAD %s MSTORE
''' % (addr_expr, dst)
def _xfer(to_expr, amt_expr, dst):
    return '''
0xa9059cbb00000000000000000000000000000000000000000000000000000000 0x80 MSTORE
%s 0x84 MSTORE
%s 0xa4 MSTORE
0 0x100 MSTORE
0x20 0x100 0x44 0x80 0 0 CALLDATALOAD GAS CALL
RETURNDATASIZE ISZERO 0x1f RETURNDATASIZE GT 0x100 MLOAD 1 EQ AND OR AND
%s MSTORE
''' % (to_expr, amt_expr, dst)
# Placed at the PoolManager address. calldata: token, account A, amount, sink, then the payload handed to A.
# Returns 8 words: b0, transfer to A accepted, A's call succeeded, b1, balance of A, full transfer accepted,
# transfer of b1 - amount accepted (meaningful when the full transfer was refused), final balance.
ASSIGN = assemble(
    _bal('ADDRESS', '0x200') +
    _xfer('0x20 CALLDATALOAD', '0x40 CALLDATALOAD', '0x220') +
    '''
0x80 CALLDATASIZE SUB 0x80 0x400 CALLDATACOPY
0 0x1e0 MSTORE
0x20 0x1e0 0x80 CALLDATASIZE SUB 0x400 0 0x20 CALLDATALOAD GAS CALL
0x1e0 MLOAD AND 0x240 MSTORE
''' +
    _bal('ADDRESS', '0x260') +
    _bal('0x20 CALLDATALOAD', '0x280') +
    _xfer('0x60 CALLDATALOAD', '0x260 MLOAD', '0x2a0') +
    _xfer('0x60 CALLDATALOAD', '0x40 CALLDATALOAD 0x260 MLOAD SUB', '0x2c0') +
    _bal('ADDRESS', '0x2e0') +
    '0x100 0x200 RETURN')

OPS['NOT'] = 0x19
_TRIAL = (
    _bal('ADDRESS', '0x200') +
    _xfer('0x20 CALLDATALOAD', '0x40 CALLDATALOAD', '0x220') +
    '''
0x80 CALLDATASIZE SUB 0x80 0x400 CALLDATACOPY
0 0x1e0 MSTORE
0x20 0x1e0 0x80 CALLDATASIZE SUB 0x400 0 0x20 CALLDATALOAD GAS CALL
0x1e0 MLOAD AND 0x240 MSTORE
''' +
    _bal('ADDRESS', '0x260') +
    _bal('0x20 CALLDATALOAD', '0x280') +
    _xfer('0x60 CALLDATALOAD', '0x260 MLOAD', '0x2a0') +
    _xfer('0x60 CALLDATALOAD', '0x40 CALLDATALOAD 0x260 MLOAD SUB', '0x2c0') +
    _bal('ADDRESS', '0x2e0'))
# Many trials in one eth_call. Top level: header (token, A, amount, sink) then items [len][payload padded to 32 bytes].
# Each trial runs in a self call that reverts with its 8 result words, so no trial sees the state of another.
MULTI = assemble('''
CALLER ADDRESS EQ @trial JUMPI
0x80 0 0x1000 CALLDATACOPY
0x80 0x8000
loop:
DUP2 CALLDATASIZE GT ISZERO @end JUMPI
DUP2 CALLDATALOAD
DUP1 DUP4 0x20 ADD 0x1080 CALLDATACOPY
0x100 DUP3 DUP3 0x80 ADD 0x1000 0 ADDRESS 0x3d0900 CALL POP
0x1f ADD 0x1f NOT AND 0x20 ADD
SWAP2 DUP3 ADD SWAP2 POP
0x100 ADD
@loop JUMP
end:
0x8000 DUP2 SUB 0x8000 RETURN
trial:
''' + _TRIAL + '0x100 0x200 REVERT')

# Ordinary account that runs several calls in order: items [target][len][data padded]. Returns 1 when all succeeded.
FWDN = assemble('''
1 0 MSTORE
0
loop:
DUP1 CALLDATASIZE GT ISZERO @end JUMPI
DUP1 0x20 ADD CALLDATALOAD
DUP1 DUP3 0x40 ADD 0x200 CALLDATACOPY
0 0 DUP3 0x200 0 DUP7 CALLDATALOAD GAS CALL
0 MLOAD AND 0 MSTORE
0x1f ADD 0x1f NOT AND 0x40 ADD ADD
@loop JUMP
end:
0x20 0 RETURN
''')

# Placed at the PoolManager address. calldata: word0 = recipient, then one token per word.
# For each token: b0, transfer of b0/3 to the recipient accepted, b1, balance of recipient after. 4 words.
THIRD = assemble('''
0x20 0x400
loop:
DUP2 CALLDATASIZE EQ @end JUMPI
DUP2 CALLDATALOAD
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
ADDRESS 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL POP
0x40 MLOAD DUP3 MSTORE
0xa9059cbb00000000000000000000000000000000000000000000000000000000 0x80 MSTORE
0 CALLDATALOAD 0x84 MSTORE
3 0x40 MLOAD DIV 0xa4 MSTORE
0 0x100 MSTORE
0x20 0x100 0x44 0x80 0 DUP6 0x1e8480 CALL
RETURNDATASIZE ISZERO 0x1f RETURNDATASIZE GT 0x100 MLOAD 1 EQ AND OR AND
DUP3 0x20 ADD MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL POP
0x40 MLOAD DUP3 0x40 ADD MSTORE
0 CALLDATALOAD 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 0x2dc6c0 STATICCALL POP
0x40 MLOAD DUP3 0x60 ADD MSTORE
POP
0x80 ADD SWAP1 0x20 ADD SWAP1
@loop JUMP
end:
0x400 DUP2 SUB 0x400 RETURN
''')
