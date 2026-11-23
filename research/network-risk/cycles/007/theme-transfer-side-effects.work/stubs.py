# Measuring stubs for eth_call with state overrides. Nothing here is deployed or sent.
from base import assemble, _bal, _xfer
# calldata: pairs (address, left aligned selector). One word out per pair: the 32 byte answer of a static call, or 0.
GET = assemble('''
0
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
DUP1 0x20 ADD CALLDATALOAD 0 MSTORE
0 0x40 MSTORE
0x20 0x40 4 0 DUP5 CALLDATALOAD 0x30d40 STATICCALL
RETURNDATASIZE 0x20 EQ AND
0x40 MLOAD MUL
2 DUP3 DIV 0x1000 ADD MSTORE
0x40 ADD
@loop JUMP
end:
2 SWAP1 DIV 0x1000 RETURN
''')
# calldata: triples (address, left aligned selector + first 28 bytes of arguments, rest). Static call with 0x64 bytes: sel + 3 words. One word out.
GET3 = assemble('''
0
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
0x80 DUP2 0x20 ADD 0 CALLDATACOPY
0 0x100 MSTORE
0x20 0x100 0x64 0 DUP5 CALLDATALOAD 0x30d40 STATICCALL
0x1f RETURNDATASIZE GT AND
0x100 MLOAD MUL
5 DUP3 DIV 0x1000 ADD MSTORE
0xa0 ADD
@loop JUMP
end:
5 SWAP1 DIV 0x1000 RETURN
''')
# calldata: address words. One word out per address: EXTCODESIZE.
CSIZE = assemble('''
0
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
DUP1 CALLDATALOAD EXTCODESIZE
DUP2 0x1000 ADD MSTORE
0x20 ADD
@loop JUMP
end:
0x1000 RETURN
''')
# Placed at the PoolManager address. calldata: word0 = divisor, then pairs (token, recipient).
# Each pair is one trial in a self call that reverts, so no trial sees the state of another. Eight words per trial:
# b0 balanceOf(PM), r0 balanceOf(recipient), amt = b0 / divisor, transfer accepted by the rule of Currency.sol,
# b1, r1, skim(PM) on the recipient did not revert, b2 balanceOf(PM) after the skim.
_T = (_bal('ADDRESS', '0x200') + _bal('0x20 CALLDATALOAD', '0x220') +
      '0x40 CALLDATALOAD 0x200 MLOAD DIV 0x240 MSTORE' +
      _xfer('0x20 CALLDATALOAD', '0x240 MLOAD', '0x260') +
      _bal('ADDRESS', '0x280') + _bal('0x20 CALLDATALOAD', '0x2a0') + '''
0xbc25cf7700000000000000000000000000000000000000000000000000000000 0x80 MSTORE
ADDRESS 0x84 MSTORE
0 0 0x24 0x80 0 0x20 CALLDATALOAD GAS CALL
0x2c0 MSTORE
''' + _bal('ADDRESS', '0x2e0'))
SURCH = assemble('''
CALLER ADDRESS EQ @trial JUMPI
0x20 0x8000
loop:
DUP2 CALLDATASIZE EQ @end JUMPI
DUP2 CALLDATALOAD 0 MSTORE
DUP2 0x20 ADD CALLDATALOAD 0x20 MSTORE
0 CALLDATALOAD 0x40 MSTORE
0x100 DUP2 0x60 0 0 ADDRESS 0x3d0900 CALL POP
0x100 ADD SWAP1 0x40 ADD SWAP1
@loop JUMP
end:
0x8000 DUP2 SUB 0x8000 RETURN
trial:
''' + _T + '0x100 0x200 REVERT')
# Placed at a pair address. calldata: token, recipient, amount. Sends amount to the recipient.
# Four words: balance of recipient before, transfer accepted, balance of recipient after, balance of this address after.
FROMPAIR = assemble(_bal('0x20 CALLDATALOAD', '0x200') + _xfer('0x20 CALLDATALOAD', '0x40 CALLDATALOAD', '0x220') + _bal('0x20 CALLDATALOAD', '0x240') + _bal('ADDRESS', '0x260') + '0x80 0x200 RETURN')
if __name__ == '__main__':
    print(len(GET) // 2, len(SURCH) // 2)
# Placed at an ordinary account. calldata: token, holder, target, then the payload for the target.
# Returns: balanceOf(holder) before, success flag of the call, balanceOf(holder) after, balanceOf(this account) after.
from base import assemble as _asm
ACT = _asm('''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
0x20 CALLDATALOAD 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 0 CALLDATALOAD GAS STATICCALL POP
0x40 MLOAD 0x200 MSTORE
0x60 CALLDATASIZE SUB 0x60 0x400 CALLDATACOPY
0 0 0x60 CALLDATASIZE SUB 0x400 0 0x40 CALLDATALOAD GAS CALL
0x220 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 0 CALLDATALOAD GAS STATICCALL POP
0x40 MLOAD 0x240 MSTORE
ADDRESS 4 MSTORE
0 0x40 MSTORE
0x20 0x40 0x24 0 0 CALLDATALOAD GAS STATICCALL POP
0x40 MLOAD 0x260 MSTORE
0x80 0x200 RETURN
''')
