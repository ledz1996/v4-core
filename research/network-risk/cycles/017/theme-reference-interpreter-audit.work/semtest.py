"""Cycle 17, theme-reference-interpreter-audit, task 1.
Runs gas-independent semantic cases through three copies of the reference interpreter
(tools/opdiff/pyevm.py, cycles/013/.../pyevm2.py, cycles/016/.../pyevm_tx.py) and this unit's corrected pyevm_tx17.py and through
eth_call with state overrides on an Ethereum endpoint (second source of truth), and prints
every disagreement. Read-only RPC only.
usage: python3 semtest.py [rpc] > out/semtest.json"""
import sys, os, json, urllib.request, importlib.util, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
NR = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import keccak  # noqa: E402

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

P1 = load('pyevm', os.path.join(NR, 'tools/opdiff/pyevm.py'))
P2 = load('pyevm2', os.path.join(NR, 'cycles/013/theme-mined-branches.work/pyevm2.py'))
P3 = load('pyevm_tx', os.path.join(NR, 'cycles/016/theme-revert-rollback-mined.work/pyevm_tx.py'))
P4 = load('pyevm_tx17', os.path.join(HERE, 'pyevm_tx17.py'))
RPC = sys.argv[1] if len(sys.argv) > 1 else 'https://ethereum-rpc.publicnode.com'

OP = {'STOP': 0, 'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9, 'EXP': 10,
      'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15, 'AND': 0x16, 'OR': 0x17,
      'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d, 'KECCAK256': 0x20, 'ADDRESS': 0x30,
      'BALANCE': 0x31, 'CALLER': 0x33, 'CALLVALUE': 0x34, 'CALLDATALOAD': 0x35, 'CALLDATASIZE': 0x36, 'CALLDATACOPY': 0x37,
      'CODESIZE': 0x38, 'CODECOPY': 0x39, 'EXTCODESIZE': 0x3b, 'EXTCODECOPY': 0x3c, 'RETURNDATASIZE': 0x3d, 'RETURNDATACOPY': 0x3e,
      'EXTCODEHASH': 0x3f, 'SELFBALANCE': 0x47, 'POP': 0x50, 'MLOAD': 0x51, 'MSTORE': 0x52, 'MSTORE8': 0x53, 'SLOAD': 0x54,
      'SSTORE': 0x55, 'JUMP': 0x56, 'JUMPI': 0x57, 'PC': 0x58, 'MSIZE': 0x59, 'GAS': 0x5a, 'JUMPDEST': 0x5b, 'TLOAD': 0x5c,
      'TSTORE': 0x5d, 'MCOPY': 0x5e, 'PUSH0': 0x5f, 'LOG0': 0xa0, 'LOG1': 0xa1, 'CALL': 0xf1, 'CALLCODE': 0xf2, 'RETURN': 0xf3,
      'DELEGATECALL': 0xf4, 'STATICCALL': 0xfa, 'REVERT': 0xfd, 'INVALID': 0xfe}
for i in range(1, 17): OP[f'DUP{i}'] = 0x7f + i; OP[f'SWAP{i}'] = 0x8f + i


def asm(*items):
    """items: opcode names, ints (pushed minimally), ('L', name) label, ('J', name) push of a label, raw bytes."""
    def emit(pos):
        out = bytearray(); lab = {}
        for it in items:
            if isinstance(it, tuple) and it[0] == 'L': lab[it[1]] = len(out); out.append(0x5b)
            elif isinstance(it, tuple) and it[0] == 'J': out += bytes([0x61]) + pos.get(it[1], 0).to_bytes(2, 'big')
            elif isinstance(it, str): out.append(OP[it])
            elif isinstance(it, (bytes, bytearray)): out += it
            elif isinstance(it, int):
                if it == 0: out.append(0x5f)
                else:
                    b = it.to_bytes((it.bit_length() + 7) // 8, 'big'); out.append(0x5f + len(b)); out += b
            else: raise ValueError(it)
        return bytes(out), lab
    _, lab = emit({}); code, lab2 = emit(lab); assert lab == lab2; return code


def call(kind, to, value=0, io=0, isz=0, oo=0, osz=0):
    """push the arguments of a call; leaves the success flag on the stack"""
    a = [osz, oo, isz, io]
    if kind in ('CALL', 'CALLCODE'): a.append(value)
    return a + [to, 1_000_000, kind]


class R:
    """Collects observations: each rec() stores the stack top into the next result slot at 0x1000 + 32 i."""
    def __init__(self): self.n = 0
    def rec(self): o = 0x1000 + 32 * self.n; self.n += 1; return [o, 'MSTORE']
    def ret(self): return [32 * self.n, 0x1000, 'RETURN']


A = 0xa000000000000000000000000000000000000a01  # entry
B = 0xb000000000000000000000000000000000000b02
C = 0xc000000000000000000000000000000000000c03
D = 0xd000000000000000000000000000000000000d04
X = 0xe000000000000000000000000000000000000e05  # never has code
FROM = 0xf000000000000000000000000000000000000f06

RET4 = asm(0xdeadbeef, 0, 'MSTORE', 4, 28, 'RETURN')
REV3 = asm(0xabcdef, 0, 'MSTORE', 3, 29, 'REVERT')
INVALID = asm('INVALID')
SST = asm(0x55, 1, 'SSTORE', 'STOP')
TST = asm(0x66, 1, 'TSTORE', 'STOP')
LOGGER = asm(0, 0, 'LOG0', 'STOP')
CALLDOWN = asm(*call('CALL', C), 0, 'MSTORE', 32, 0, 'RETURN')  # calls C, returns its success flag
CALLVAL1 = asm(*call('CALL', X, value=1), 0, 'MSTORE', 32, 0, 'RETURN')
DELEGDOWN = asm(*call('DELEGATECALL', C), 0, 'MSTORE', 32, 0, 'RETURN')
INFO = asm('CALLVALUE', 0, 'MSTORE', 'CALLER', 32, 'MSTORE', 'ADDRESS', 64, 'MSTORE', 'SELFBALANCE', 96, 'MSTORE',
           9, 3, 'TSTORE', 10, 3, 'SSTORE', 128, 0, 'RETURN')
TREAD = asm(3, 'TLOAD', 0, 'MSTORE', 3, 'SLOAD', 32, 'MSTORE', 64, 0, 'RETURN')


def writes_then(end):
    """SSTORE(2,7), TSTORE(2,8), CALL X with value 5, LOG0, then end"""
    return asm(7, 2, 'SSTORE', 8, 2, 'TSTORE', *call('CALL', X, value=5), 'POP', 0, 0, 'LOG0', *end)

READER = asm(2, 'SLOAD', 0, 'MSTORE', 2, 'TLOAD', 32, 'MSTORE', 64, 0, 'RETURN')
# a contract that writes and halts when called with empty calldata, and reports its own slot 2 when called with data
def selfreader(end):
    return asm('CALLDATASIZE', ('J', 'read'), 'JUMPI', 7, 2, 'SSTORE', 8, 2, 'TSTORE', *call('CALL', X, value=5), 'POP', 0, 0, 'LOG0', *end,
               ('L', 'read'), 2, 'SLOAD', 0, 'MSTORE', 2, 'TLOAD', 32, 'MSTORE', 'SELFBALANCE', 64, 'MSTORE', 96, 0, 'RETURN')

CASES = []
def case(name, codes, value=0, balances=None, data=b'', note=''):
    CASES.append(dict(name=name, codes=codes, value=value, balances=balances or {}, data=data, note=note))


# 1. CALL with value: to a non-existent account, above the balance, to a precompile; return data after each
r = R(); body = []
body += call('CALL', B, osz=0) + r.rec() + ['RETURNDATASIZE'] + r.rec()          # RET4: 1, 4
body += call('CALL', X, value=7) + r.rec() + ['RETURNDATASIZE'] + r.rec()        # empty account with value: 1, 0
body += [X, 'BALANCE'] + r.rec() + ['SELFBALANCE'] + r.rec()                     # 7, 93
body += call('CALL', B) + ['POP']                                               # return data = 4 bytes again
body += call('CALL', X, value=1000) + r.rec() + ['RETURNDATASIZE'] + r.rec()     # insufficient: 0, 0
body += call('CALL', 4, value=3, io=0, isz=5) + r.rec() + ['RETURNDATASIZE'] + r.rec() + [4, 'BALANCE'] + r.rec()  # identity: 1, 5, 3
body += call('CALL', C) + r.rec() + ['RETURNDATASIZE'] + r.rec()                 # REV3: 0, 3
body += call('CALL', D) + r.rec() + ['RETURNDATASIZE'] + r.rec()                 # INVALID: 0, 0
body += [X, 'EXTCODESIZE'] + r.rec() + [B, 'EXTCODESIZE'] + r.rec() + [1, 'EXTCODESIZE'] + r.rec()
body += ['SELFBALANCE'] + r.rec()
case('call_value_returndata', {A: asm(*body, *r.ret()), B: RET4, C: REV3, D: INVALID}, balances={A: 100, X: 0, 4: 0})

# 2. STATICCALL write protection through nested frames
r = R(); body = []
for t in (B, C, D):  # B: SSTORE, C: TSTORE, D: LOG0
    body += call('STATICCALL', t) + r.rec()
body += call('STATICCALL', 0xb0b) + r.rec()  # CALLDOWN -> SST
body += call('STATICCALL', 0xb0c) + r.rec() + ['RETURNDATASIZE'] + r.rec() + [32, 0, 0, 'RETURNDATACOPY', 0, 'MLOAD'] + r.rec()  # CALLDOWN -> RET4 child ok
body += call('STATICCALL', 0xb0d) + r.rec()  # CALLVAL1 inside static
body += call('STATICCALL', 0xb0e) + r.rec() + [32, 0, 0, 'RETURNDATACOPY', 0, 'MLOAD'] + r.rec()  # DELEGDOWN -> TST: outer ok, inner flag 0
body += call('CALL', 0xb0e) + r.rec() + [32, 0, 0, 'RETURNDATACOPY', 0, 'MLOAD'] + r.rec()  # same, not static: inner flag 1
case('static_nested', {A: asm(*body, *r.ret()), B: SST, C: TST, D: LOGGER,
                       0xb0b: asm(*call('CALL', B), 0, 'MSTORE', 32, 0, 'RETURN'),
                       0xb0c: asm(*call('CALL', 0xb0f), 0, 'MSTORE', 32, 0, 'RETURN'), 0xb0f: RET4,
                       0xb0d: CALLVAL1, 0xb0e: asm(*call('DELEGATECALL', C), 0, 'MSTORE', 32, 0, 'RETURN')}, balances={0xb0d: 10, X: 0})

# 3. RETURNDATACOPY bounds
def rdc(off, size):
    return asm(*call('CALL', B), 'POP', size, off, 0, 'RETURNDATACOPY', 1, 0, 'MSTORE', 32, 0, 'RETURN')
r = R(); body = []
for i, (o, s) in enumerate([(0, 4), (0, 5), (4, 0), (5, 0), (2, 2), (2, 3), ((1 << 255), 0)]):
    body += call('CALL', 0xc00 + i) + r.rec()
codes = {A: None, B: RET4}
for i, (o, s) in enumerate([(0, 4), (0, 5), (4, 0), (5, 0), (2, 2), (2, 3), ((1 << 255), 0)]): codes[0xc00 + i] = rdc(o, s)
codes[A] = asm(*body, *r.ret())
case('returndatacopy_bounds', codes)

# 4. DELEGATECALL: value, caller, address, selfbalance, transient and storage keyed by the caller's address
r = R(); body = []
body += call('DELEGATECALL', B, osz=128) + r.rec()
for k in range(4): body += [32 * k, 'MLOAD'] + r.rec()
body += [3, 'TLOAD'] + r.rec() + [3, 'SLOAD'] + r.rec()
body += call('CALL', C, osz=64) + r.rec() + [0, 'MLOAD'] + r.rec() + [32, 'MLOAD'] + r.rec()  # C's own context sees nothing
body += call('DELEGATECALL', D) + r.rec() + [4, 'TLOAD'] + r.rec() + [4, 'SLOAD'] + r.rec()
case('delegatecall_context', {A: asm(*body, *r.ret()), B: INFO, C: TREAD, D: asm(11, 4, 'TSTORE', 12, 4, 'SSTORE', 0, 0, 'REVERT')},
     value=5, balances={FROM: 10 ** 18, A: 1000})

# 5. rollback of storage, transient storage, balances on REVERT, INVALID, stack underflow, bad jump, return data out of bounds
ends = {'revert': [0, 0, 'REVERT'], 'invalid': ['INVALID'], 'underflow': ['ADD'], 'badjump': [3, 'JUMP'],
        'rdoob': [1, 0, 0, 'RETURNDATACOPY', 'STOP'], 'stop': ['STOP']}
for nm, end in ends.items():
    r = R(); body = []
    body += call('CALL', B, value=10) + r.rec()
    body += [B, 'BALANCE'] + r.rec() + [X, 'BALANCE'] + r.rec() + ['SELFBALANCE'] + r.rec()
    body += [1, 0, 'MSTORE8'] + call('CALL', B, isz=1, osz=96) + r.rec() + [0, 'MLOAD'] + r.rec() + [32, 'MLOAD'] + r.rec() + [64, 'MLOAD'] + r.rec()
    body += call('DELEGATECALL', C) + r.rec() + [2, 'SLOAD'] + r.rec() + [2, 'TLOAD'] + r.rec() + ['SELFBALANCE'] + r.rec() + [X, 'BALANCE'] + r.rec()
    case(f'rollback_{nm}', {A: asm(*body, *r.ret()), B: selfreader(end), C: writes_then(end)}, balances={A: 100, X: 0})

# 6. stack limit reached through PUSH, DUP and PUSH0, which skip the overflow check in the interpreter
r = R(); body = []
variants = {0xd01: [b'\x5f' * 1024, 'STOP'], 0xd02: [b'\x5f' * 1025, 'STOP'], 0xd03: [b'\x5f' * 1024, 'DUP1', 'STOP'],
            0xd04: [b'\x60\x01' * 1025, 'POP', 'STOP'], 0xd05: [b'\x5f' * 1024, 'DUP1', 'ADD', 'STOP'],
            0xd06: [b'\x5f' * 1023, 'PC', 'PC', 'STOP'], 0xd07: [b'\x5f' * 1025, 7, 1, 'SSTORE', 'STOP']}
for a in variants: body += call('CALL', a) + r.rec()
body += [1, 'SLOAD'] + r.rec()
codes = {A: asm(*body, *r.ret())}
for a, v in variants.items(): codes[a] = asm(*v)
case('stack_overflow', codes)

# 7. memory expansion on zero-length operations, then normal expansion, MCOPY expansion by source
big = 1 << 200
M = asm(0, big, 'KECCAK256', 'POP', 0, 0, big, 'CALLDATACOPY', 0, 0, big, 'CODECOPY', 0, big, big, 'MCOPY', 0, big, 'LOG0',
        0, 0, big, 'RETURNDATACOPY', *call('CALL', X, io=big, isz=0, oo=big, osz=0), 'POP', 'MSIZE',
        0x40, 'MLOAD', 'POP', 'MSIZE', 1, 0x7f, 'MSTORE8', 'MSIZE', 0, 0, 0x100, 'MCOPY', 'MSIZE', 1, 0x200, 0, 'MCOPY', 'MSIZE',
        *call('CALL', X, io=0x300, isz=1, oo=0, osz=0), 'POP', 'MSIZE', *call('CALL', X, io=0, isz=0, oo=0x400, osz=1), 'POP', 'MSIZE',
        0, 'MSTORE', 32, 'MSTORE', 64, 'MSTORE', 96, 'MSTORE', 128, 'MSTORE', 160, 'MSTORE', 192, 'MSTORE', 224, 0, 'RETURN')
r = R(); body = call('CALL', B, osz=224) + r.rec() + sum(([32 * k, 'MLOAD'] + r.rec() for k in range(7)), [])
case('memory_zero_length', {A: asm(*body, *r.ret()), B: M}, balances={X: 0})

# 8. MCOPY overlap in both directions
pat = bytes(range(1, 65))
MC = asm(pat[:32], 0, 'MSTORE', pat[32:], 32, 'MSTORE', 40, 0, 3, 'MCOPY', 40, 9, 1, 'MCOPY', 0, 0, 96, 'MCOPY', 96, 0, 'RETURN')
MC = asm(int.from_bytes(pat[:32], 'big'), 0, 'MSTORE', int.from_bytes(pat[32:], 'big'), 32, 'MSTORE',
         40, 0, 3, 'MCOPY', 40, 9, 1, 'MCOPY', 96, 0, 'RETURN')
r = R(); body = call('CALL', B, osz=96) + r.rec() + sum(([32 * k, 'MLOAD'] + r.rec() for k in range(3)), [])
case('mcopy_overlap', {A: asm(*body, *r.ret()), B: MC})

# 9. jumps
r = R(); body = []
JT = {0xe01: asm(0, 0xff, 'JUMPI', 1, 0, 'MSTORE', 32, 0, 'RETURN'),          # JUMPI to a non-destination with zero condition: falls through
      0xe02: asm(1, 0xff, 'JUMPI', 1, 0, 'MSTORE', 32, 0, 'RETURN'),          # taken to a non-destination: halt
      0xe03: asm(5, 'JUMP', 0x615b, 'STOP', 'JUMPDEST', 'STOP'),               # 0x5b inside PUSH2 data at pc 5: halt
      0xe04: asm(1 << 255, 'JUMP'),                                            # huge destination
      0xe05: bytes([0x60, 0x03, 0x56, 0x5b, 0x60, 0x01, 0x5f, 0x52, 0x60, 0x20, 0x5f, 0xf3]),  # JUMP to pc 3 (a real JUMPDEST)
      0xe06: bytes([0x60, 0x04, 0x56, 0x7f])}                                   # code ends in a truncated PUSH32: jump into it
for a in JT: body += call('CALL', a, osz=32) + r.rec() + ['RETURNDATASIZE'] + r.rec()
case('jumps', {A: asm(*body, *r.ret()), **JT})

# 10. signed arithmetic and shifts at their edges
NEG = lambda v: (1 << 256) - v
r = R(); body = []
vals = [0, 1, 2, NEG(1), NEG(2), 1 << 255, (1 << 255) - 1, 7, NEG(7), 0x80, 0xff, 0x7f, 1 << 127, NEG(1 << 127)]
import itertools
for (x, y) in [(NEG(1 << 255) & ((1 << 256) - 1), NEG(1)), (1 << 255, NEG(1)), (NEG(7), 2), (7, NEG(2)), (NEG(7), NEG(2)), (5, 0), (NEG(1), 1 << 255)]:
    for op in ('SDIV', 'SMOD', 'SLT', 'SGT', 'SAR', 'SIGNEXTEND', 'BYTE', 'SHL', 'SHR'):
        body += [y, x, op] + r.rec()
for (i, x) in [(0, 0x80), (0, 0x7f), (30, 1 << 247), (31, NEG(1)), (32, 0x80), (1 << 255, 0x80), (1, 0x8000), (15, 1 << 127)]:
    body += [x, i, 'SIGNEXTEND'] + r.rec()
for (s_, x) in [(255, 1 << 255), (256, 1 << 255), (1 << 255, NEG(1)), (254, 1 << 255), (1, NEG(2)), (256, 1)]:
    body += [x, s_, 'SAR'] + r.rec()
for (a, b, n) in [(NEG(1), NEG(1), NEG(1)), (NEG(1), 2, 3), (1 << 255, 1 << 255, (1 << 256) - 189), (5, 7, 0), (NEG(1), NEG(1), 1 << 128)]:
    body += [n, b, a, 'MULMOD'] + r.rec() + [n, b, a, 'ADDMOD'] + r.rec()
for (b, e) in [(2, 255), (2, 256), (NEG(1), NEG(1)), (3, 1 << 255), (0, 0)]:
    body += [e, b, 'EXP'] + r.rec()
case('signed_edges', {A: asm(*body, *r.ret())})

# 11. CALLDATALOAD and copies at large offsets
r = R(); body = [big, 'CALLDATALOAD'] + r.rec() + [3, 'CALLDATALOAD'] + r.rec() + [32, big, 0x40, 'CALLDATACOPY', 0x40, 'MLOAD'] + r.rec()
body += [32, 2, 0x60, 'CALLDATACOPY', 0x60, 'MLOAD'] + r.rec() + [32, big, 0x80, 'CODECOPY', 0x80, 'MLOAD'] + r.rec()
case('calldata_offsets', {A: asm(*body, *r.ret())}, data=bytes(range(1, 40)))

# 12. EXTCODESIZE, EXTCODEHASH, EXTCODECOPY of empty, funded, precompile and EIP-7702 delegated accounts; calls into a delegated account
DELEG = 0xdddddddddddddddddddddddddddddddddddd0d01
DELEG_P = 0xdddddddddddddddddddddddddddddddddddd0d02  # delegated to the identity precompile
FUNDED = 0xdddddddddddddddddddddddddddddddddddd0d03
r = R(); body = []
for a in (X, FUNDED, 1, DELEG, B):
    body += [a, 'EXTCODESIZE'] + r.rec()
case('extcodesize', {A: asm(*body, *r.ret()), B: RET4, DELEG: b'\xef\x01\x00' + B.to_bytes(20, 'big')}, balances={X: 0, FUNDED: 5, 1: 0})
r = R(); body = []
for a in (X, FUNDED, 1, DELEG, B):
    body += [a, 'EXTCODEHASH'] + r.rec()
body += [32, 0, 0, DELEG, 'EXTCODECOPY', 0, 'MLOAD'] + r.rec()
case('extcodehash', {A: asm(*body, *r.ret()), B: RET4, DELEG: b'\xef\x01\x00' + B.to_bytes(20, 'big')}, balances={X: 0, FUNDED: 5, 1: 0})
r = R(); body = call('CALL', DELEG, osz=32) + r.rec() + ['RETURNDATASIZE'] + r.rec() + [0, 'MLOAD'] + r.rec()
body += [0x1234, 0, 'MSTORE'] + call('CALL', DELEG_P, io=0, isz=32, oo=0x40, osz=32) + r.rec() + ['RETURNDATASIZE'] + r.rec()
case('call_delegated', {A: asm(*body, *r.ret()), B: RET4, DELEG: b'\xef\x01\x00' + B.to_bytes(20, 'big'),
                        DELEG_P: b'\xef\x01\x00' + (4).to_bytes(20, 'big')})

# 13. precompiles 1 to 17 and 0x100 with empty input and with a 128 byte input; each in its own case so that one that raises does not hide the others
for p in list(range(1, 0x12)) + [0x100]:
    for nm, setup, isz in (('empty', [], 0), ('128', [0x1111, 0, 'MSTORE', 0x1b, 32, 'MSTORE', 0x2222, 64, 'MSTORE', 0x3333, 96, 'MSTORE'], 128),
                           ('modexp', [1, 0, 'MSTORE', 1, 32, 'MSTORE', 1, 64, 'MSTORE', 3 << 248, 96, 'MSTORE', 5 << 248, 97, 'MSTORE', 7 << 248, 98, 'MSTORE'], 99)):
        if nm == 'modexp' and p != 5: continue
        r = R(); body = setup + call('CALL', p, io=0, isz=isz, oo=0x200, osz=64) + r.rec() + ['RETURNDATASIZE'] + r.rec() + [0x200, 'MLOAD'] + r.rec() + [0x220, 'MLOAD'] + r.rec()
        case(f'precompile_{p:#x}_{nm}', {A: asm(*body, *r.ret())}, balances={p: 0})
# modexp with a 1025 byte base (EIP-7823, Osaka) and a zero modulus
r = R(); body = [1025, 0, 'MSTORE', 1, 32, 'MSTORE', 1, 64, 'MSTORE'] + call('CALL', 5, io=0, isz=96 + 1025 + 2, oo=0x800, osz=32) + r.rec() + ['RETURNDATASIZE'] + r.rec()
case('precompile_modexp_1025', {A: asm(*body, *r.ret())}, balances={5: 0})

# 14. ecrecover with a well formed input shorter than 128 bytes (missing bytes read as zero)
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
priv = 0x1234567; h = int.from_bytes(keccak(b'cycle 17'), 'big')
pub = P3._mul(priv, G); addr = int.from_bytes(keccak(pub[0].to_bytes(32, 'big') + pub[1].to_bytes(32, 'big'))[12:], 'big')
for k in range(1, 100000):
    Rp = P3._mul(k, G); rr = Rp[0] % _N; ss = pow(k, -1, _N) * (h + rr * priv) % _N; v = 27 + (Rp[1] & 1)
    if ss > _N // 2: ss = _N - ss; v = 55 - v
    if ss & 0xff == 0 and ss: break
r = R(); body = [h, 0, 'MSTORE', v, 32, 'MSTORE', rr, 64, 'MSTORE', ss, 96, 'MSTORE'] + call('CALL', 1, io=0, isz=127, oo=0x200, osz=32) + r.rec() + ['RETURNDATASIZE'] + r.rec() + [0x200, 'MLOAD'] + r.rec()
case('ecrecover_short', {A: asm(*body, *r.ret())}, note=f'expected signer {addr:#x}')

# 15. CALLCODE
r = R(); body = call('CALLCODE', B, osz=128) + r.rec() + [0, 'MLOAD'] + r.rec() + [32, 'MLOAD'] + r.rec() + [64, 'MLOAD'] + r.rec() + [3, 'SLOAD'] + r.rec()
case('callcode', {A: asm(*body, *r.ret()), B: INFO}, value=5, balances={FROM: 10 ** 18, A: 1000})

# 16. logs of a reverted frame (observable only through eth_simulateV1; the interpreters are read for their count)
r = R(); body = call('CALL', B) + r.rec() + [0, 0, 'LOG0']
case('logs_rollback', {A: asm(*body, *r.ret()), B: asm(0, 0, 'LOG0', 0, 0, 'REVERT')})


# --- runners ------------------------------------------------------------------------------------------------
class Base:
    def storage(self, a, k): return 0
    def balance(self, a): return 0
    def code(self, a): return b''
    def exthash_empty(self, a): return 0


def run_local(mod, c):
    codes = {a: v for a, v in c['codes'].items()}
    bal = dict(c['balances']); bal.setdefault(FROM, 10 ** 18)
    try:
        if mod is P2:
            w = mod.World({}, {}); w.base = Base(); w.loglist = []
            w.base.code = lambda a: codes.get(a, b''); w.base.balance = lambda a: bal.get(a, 0)
            w.env = {}
        else:
            w = mod.World(codes, bal)
            if mod is P4: w.ctx = {'osaka': True}
        ok, ret = w.call(FROM, A, c['value'], c['data'], False, 0)
        logs = len(w.logs) if mod in (P3, P4) else (len(w.loglist) if mod is P2 else w.logs)
        return {'ok': ok, 'ret': ret.hex(), 'logs': logs}
    except Exception as e:
        return {'raise': f'{type(e).__name__}: {e}'}


def rpc(method, params):
    req = urllib.request.Request(RPC, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 {'content-type': 'application/json', 'user-agent': 'opdiff'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def overrides(c):
    o = {}
    for a, code in c['codes'].items(): o.setdefault('0x%040x' % a, {})['code'] = '0x' + code.hex()
    bal = dict(c['balances']); bal.setdefault(FROM, 10 ** 18)
    for a, b in bal.items():
        if a in c.get('keep', ()): continue
        o.setdefault('0x%040x' % a, {})['balance'] = hex(b)
    return o


def run_chain(c, block):
    tx = {'from': '0x%040x' % FROM, 'to': '0x%040x' % A, 'data': '0x' + c['data'].hex(), 'value': hex(c['value']), 'gas': hex(30_000_000)}
    r = rpc('eth_call', [tx, block, overrides(c)])
    if 'result' in r: return {'ok': True, 'ret': r['result'][2:]}
    err = r.get('error', {}); d = err.get('data')
    return {'ok': False, 'ret': (d[2:] if isinstance(d, str) and d.startswith('0x') else ''), 'error': err.get('message')}


def run_sim(c, block):
    o = overrides(c)
    calls = [{'from': '0x%040x' % FROM, 'to': '0x%040x' % A, 'data': '0x' + c['data'].hex(), 'value': hex(c['value']), 'gas': hex(30_000_000)}]
    r = rpc('eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': o, 'calls': calls}]}, block])
    try: return len(r['result'][0]['calls'][0]['logs'])
    except Exception: return r.get('error')


def main():
    blk = rpc('eth_getBlockByNumber', ['latest', False])['result']; block = blk['number']
    out = {'rpc': RPC, 'client': rpc('web3_clientVersion', [])['result'], 'block': int(block, 16), 'cases': []}
    for c in CASES:
        ch = run_chain(c, block)
        if c['name'] == 'logs_rollback': ch['logs'] = run_sim(c, block)
        row = {'name': c['name'], 'note': c['note'], 'chain': ch}
        for nm, m in (('pyevm', P1), ('pyevm2', P2), ('pyevm_tx', P3), ('pyevm_tx17', P4)):
            lr = run_local(m, c); row[nm] = lr
            if 'raise' in lr: lr['verdict'] = 'raises'
            else:
                same = lr['ok'] == ch['ok'] and (lr['ret'] == ch['ret'] or not ch['ok'] and ch['ret'] == '' and lr['ret'] == '')
                if c['name'] == 'logs_rollback': same = same and lr['logs'] == ch.get('logs')
                lr['verdict'] = 'match' if same else 'DIFF'
        out['cases'].append(row)
        print(f"{c['name']:34s} chain ok={ch['ok']!s:5s} " + ' '.join(f"{nm}={row[nm]['verdict']}" for nm in ('pyevm', 'pyevm2', 'pyevm_tx', 'pyevm_tx17')), file=sys.stderr)
    json.dump(out, sys.stdout, indent=1)


if __name__ == '__main__':
    main()
