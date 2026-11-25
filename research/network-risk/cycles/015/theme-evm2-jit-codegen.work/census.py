"""Opcode census of the PoolManager runtime and a block-local constant tracker.

For every instruction that the evm2 JIT lowers with a rule of its own (inline code or a
peephole that depends on constant operands), record which operands are constants that a
PUSH in the same basic block supplies. The JIT's block analysis can only know more constants
than this (it also propagates across blocks), so the second table is a lower bound on the
peephole paths the build reaches; the opcode list is exact.

Usage: python3 census.py <PoolManager.json> <out.json>
"""
import json, sys, collections
MASK = (1 << 256) - 1

NAMES = {0x00: 'STOP', 0x01: 'ADD', 0x02: 'MUL', 0x03: 'SUB', 0x04: 'DIV', 0x05: 'SDIV', 0x06: 'MOD', 0x07: 'SMOD', 0x08: 'ADDMOD',
         0x09: 'MULMOD', 0x0a: 'EXP', 0x0b: 'SIGNEXTEND', 0x10: 'LT', 0x11: 'GT', 0x12: 'SLT', 0x13: 'SGT', 0x14: 'EQ', 0x15: 'ISZERO',
         0x16: 'AND', 0x17: 'OR', 0x18: 'XOR', 0x19: 'NOT', 0x1a: 'BYTE', 0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR', 0x1e: 'CLZ', 0x20: 'KECCAK256',
         0x30: 'ADDRESS', 0x31: 'BALANCE', 0x32: 'ORIGIN', 0x33: 'CALLER', 0x34: 'CALLVALUE', 0x35: 'CALLDATALOAD', 0x36: 'CALLDATASIZE',
         0x37: 'CALLDATACOPY', 0x38: 'CODESIZE', 0x39: 'CODECOPY', 0x3a: 'GASPRICE', 0x3b: 'EXTCODESIZE', 0x3c: 'EXTCODECOPY', 0x3d: 'RETURNDATASIZE',
         0x3e: 'RETURNDATACOPY', 0x3f: 'EXTCODEHASH', 0x40: 'BLOCKHASH', 0x41: 'COINBASE', 0x42: 'TIMESTAMP', 0x43: 'NUMBER', 0x44: 'PREVRANDAO',
         0x45: 'GASLIMIT', 0x46: 'CHAINID', 0x47: 'SELFBALANCE', 0x48: 'BASEFEE', 0x49: 'BLOBHASH', 0x4a: 'BLOBBASEFEE',
         0x50: 'POP', 0x51: 'MLOAD', 0x52: 'MSTORE', 0x53: 'MSTORE8', 0x54: 'SLOAD', 0x55: 'SSTORE', 0x56: 'JUMP', 0x57: 'JUMPI',
         0x58: 'PC', 0x59: 'MSIZE', 0x5a: 'GAS', 0x5b: 'JUMPDEST', 0x5c: 'TLOAD', 0x5d: 'TSTORE', 0x5e: 'MCOPY', 0x5f: 'PUSH0',
         0xa0: 'LOG0', 0xa1: 'LOG1', 0xa2: 'LOG2', 0xa3: 'LOG3', 0xa4: 'LOG4', 0xf0: 'CREATE', 0xf1: 'CALL', 0xf2: 'CALLCODE', 0xf3: 'RETURN',
         0xf4: 'DELEGATECALL', 0xf5: 'CREATE2', 0xfa: 'STATICCALL', 0xfd: 'REVERT', 0xfe: 'INVALID', 0xff: 'SELFDESTRUCT'}
for i in range(1, 33): NAMES[0x5f + i] = f'PUSH{i}'
for i in range(1, 17): NAMES[0x7f + i] = f'DUP{i}'; NAMES[0x8f + i] = f'SWAP{i}'
IO = {'ADD': 2, 'MUL': 2, 'SUB': 2, 'DIV': 2, 'SDIV': 2, 'MOD': 2, 'SMOD': 2, 'EXP': 2, 'SIGNEXTEND': 2, 'LT': 2, 'GT': 2, 'SLT': 2,
      'SGT': 2, 'EQ': 2, 'AND': 2, 'OR': 2, 'XOR': 2, 'BYTE': 2, 'SHL': 2, 'SHR': 2, 'SAR': 2, 'ADDMOD': 3, 'MULMOD': 3, 'ISZERO': 1, 'NOT': 1}
TRACK = ['DIV', 'SDIV', 'MOD', 'SMOD', 'ADDMOD', 'MULMOD', 'EXP', 'SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR', 'CALLDATALOAD', 'SLOAD',
         'KECCAK256', 'RETURN', 'REVERT']
NIN = {'CALLDATALOAD': 1, 'SLOAD': 1, 'KECCAK256': 2, 'RETURN': 2, 'REVERT': 2}


def disasm(code):
    out, pc = [], 0
    while pc < len(code):
        op = code[pc]; name = NAMES.get(op, f'UNKNOWN_{op:02x}')
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f; imm = int.from_bytes(code[pc + 1:pc + 1 + n].ljust(n, b'\0'), 'big'); out.append((pc, name, imm)); pc += 1 + n
        else:
            out.append((pc, name, None)); pc += 1
    return out


def main(src, dst):
    code = bytes.fromhex(json.load(open(src))['runtime'].removeprefix('0x'))
    ins = disasm(code)
    # Solidity appends CBOR metadata; stop the census at the first INVALID after the last JUMPDEST-reachable code is hard to
    # tell, so count everything and also count up to the metadata marker separately.
    meta = code.rfind(bytes.fromhex('a264697066735822'))
    census = collections.Counter(n for pc, n, _ in ins if meta < 0 or pc < meta)
    shapes = collections.defaultdict(collections.Counter)
    sites = collections.defaultdict(list)
    stack = []  # block-local: None unknown, int constant
    for pc, n, imm in ins:
        if meta >= 0 and pc >= meta: break
        if n == 'JUMPDEST' or n in ('JUMP', 'JUMPI', 'STOP', 'RETURN', 'REVERT', 'INVALID') and False:
            stack = []
        if n.startswith('PUSH'):
            stack.append(imm if n != 'PUSH0' else 0); continue
        if n.startswith('DUP'):
            k = int(n[3:]); stack.append(stack[-k] if len(stack) >= k else None); continue
        if n.startswith('SWAP'):
            k = int(n[4:])
            while len(stack) < k + 1: stack.insert(0, None)
            stack[-1], stack[-1 - k] = stack[-1 - k], stack[-1]; continue
        nin = IO.get(n, NIN.get(n))
        if n in TRACK:
            ops = [stack[-1 - i] if len(stack) > i else None for i in range(nin)]
            key = tuple('c' if o is not None else '-' for o in ops)
            shapes[n][''.join(key)] += 1
            consts = [hex(o) if o is not None else None for o in ops]
            sites[n].append({'pc': pc, 'constOperandsTopFirst': consts})
        if n in ('JUMP', 'JUMPI', 'STOP', 'RETURN', 'REVERT', 'INVALID', 'SELFDESTRUCT'):
            stack = []; continue
        if nin is not None and n in IO:
            ops = [stack.pop() if stack else None for _ in range(nin)]
            stack.append(None)  # results are not folded here; only PUSH constants count
            continue
        # anything else: unknown effect on the local stack, reset
        stack = []
    json.dump({'runtimeBytes': len(code), 'metadataOffset': meta, 'census': dict(sorted(census.items())),
               'constShapesTopFirst': {k: dict(v) for k, v in shapes.items()}, 'sites': sites}, open(dst, 'w'), indent=1)
    print(len(code), meta)
    for k in sorted(census): print(k, census[k], end='; ')
    print()
    for k, v in shapes.items(): print(k, dict(v))


if __name__ == '__main__':
    main(*sys.argv[1:])
