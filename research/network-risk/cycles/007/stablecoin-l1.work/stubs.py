# Measuring stubs for read-only eth_call tests with state overrides. None of them is deployed and no transaction is sent.
from asm import assemble
# RUNNER: runs a list of calls and returns what each one answered.
# Entry mode calldata: [flags][item]...           Callback mode: unlockCallback(bytes) where bytes = [flags][item]...
# item = [target][value][n][n bytes of calldata padded to 32]. Record per item = [ok][returndatasize][return data padded to 32].
# flags bit 0: end with REVERT carrying the records (so they survive when the surrounding unlock cannot close).
# In callback mode without that bit the records are returned as ABI bytes, which is what unlock expects.
RUNNER = assemble('''
0 CALLDATALOAD 0xe0 SHR 0x91dd7346 EQ @cb JUMPI
0 CALLDATALOAD 0xff60 MSTORE
0x20 0xff00 MSTORE
CALLDATASIZE 0xff20 MSTORE
0 0xff80 MSTORE
@start JUMP
cb:
0x44 CALLDATALOAD 0xff60 MSTORE
0x64 0xff00 MSTORE
0x24 CALLDATALOAD 0x44 ADD 0xff20 MSTORE
1 0xff80 MSTORE
start:
0x10000 0xff40 MSTORE
loop:
0xff20 MLOAD 0xff00 MLOAD LT ISZERO @end JUMPI
0xff00 MLOAD 0x40 ADD CALLDATALOAD
DUP1 0xff00 MLOAD 0x60 ADD 0 CALLDATACOPY
0 0 DUP3 0
0xff00 MLOAD 0x20 ADD CALLDATALOAD
0xff00 MLOAD CALLDATALOAD
GAS CALL
0xff40 MLOAD MSTORE
RETURNDATASIZE 0xff40 MLOAD 0x20 ADD MSTORE
RETURNDATASIZE 0 0xff40 MLOAD 0x40 ADD RETURNDATACOPY
RETURNDATASIZE 0x1f ADD 0x1f NOT AND 0x40 ADD 0xff40 MLOAD ADD 0xff40 MSTORE
0x1f ADD 0x1f NOT AND 0x60 ADD 0xff00 MLOAD ADD 0xff00 MSTORE
@loop JUMP
end:
0xff60 MLOAD 1 AND @rev JUMPI
0xff80 MLOAD @cbret JUMPI
0x10000 0xff40 MLOAD SUB 0x10000 RETURN
cbret:
0x20 0xffc0 MSTORE
0x10000 0xff40 MLOAD SUB 0xffe0 MSTORE
0x10000 0xff40 MLOAD SUB 0x40 ADD 0xffc0 RETURN
rev:
0x10000 0xff40 MLOAD SUB 0x10000 REVERT
''')
# PROXY: forwards every call to the PoolManager by DELEGATECALL and passes the answer through.
def proxy(pm):
    return assemble('''
CALLDATASIZE 0 0 CALLDATACOPY
0 0 CALLDATASIZE 0 %s GAS DELEGATECALL
RETURNDATASIZE 0 0 RETURNDATACOPY
@ok JUMPI
RETURNDATASIZE 0 REVERT
ok:
RETURNDATASIZE 0 RETURN
''' % pm)
# EIP-7702 delegation designator pointing at the PoolManager
def designator(pm): return '0xef0100' + pm[2:].lower()
# BAL: returns the native balance of the address in calldata word 0
BAL = assemble('0 CALLDATALOAD BALANCE 0 MSTORE 0x20 0 RETURN')
if __name__ == '__main__':
    print(len(RUNNER) // 2 - 1, RUNNER); print(proxy('0x000000000004444c5dc75cB358380D2e3dE08A90')); print(BAL)
