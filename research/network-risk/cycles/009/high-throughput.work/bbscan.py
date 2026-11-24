"""Basic block scan of the built PoolManager runtime (research/network-risk/build/PoolManager.json).

Within each basic block (as the Monad compiler forms them: a block ends after JUMP, JUMPI,
STOP, RETURN, REVERT, INVALID, SELFDESTRUCT and before every JUMPDEST) the stack is tracked
abstractly: PUSH gives a literal, DUP and SWAP move items, ADD/SUB/MUL/AND/OR/XOR/NOT/SHL/SHR
on literals fold, every other result and every item from before the block is unknown.
For each opcode of interest it records which operands are literals at that point, which
is what decides the code path the x86 emitter takes. It also records comparisons whose
result is consumed directly by JUMPI or by ISZERO then JUMPI (deferred comparisons).

Usage: python3 bbscan.py <build json> <out json>
"""
import sys, json
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
from pyevm import NAMES

M = (1 << 256) - 1
END = {0x56, 0x57, 0x00, 0xf3, 0xfd, 0xfe, 0xff}
FOLD = {0x01: lambda a, b: (a + b) & M, 0x02: lambda a, b: (a * b) & M, 0x03: lambda a, b: (a - b) & M,
        0x16: lambda a, b: a & b, 0x17: lambda a, b: a | b, 0x18: lambda a, b: a ^ b,
        0x1b: lambda s, v: (v << s) & M if s < 256 else 0, 0x1c: lambda s, v: v >> s if s < 256 else 0}
# stack in/out counts for the opcodes the PoolManager uses
def io(op):
    if 0x60 <= op <= 0x7f or op == 0x5f: return 0, 1
    if 0x80 <= op <= 0x8f: return op - 0x7f, op - 0x7f + 1
    if 0x90 <= op <= 0x9f: return op - 0x8e, op - 0x8e
    if 0xa0 <= op <= 0xa4: return op - 0xa0 + 2, 0
    t = {0x00: (0, 0), 0x01: (2, 1), 0x02: (2, 1), 0x03: (2, 1), 0x04: (2, 1), 0x05: (2, 1), 0x06: (2, 1), 0x07: (2, 1),
         0x08: (3, 1), 0x09: (3, 1), 0x0a: (2, 1), 0x0b: (2, 1), 0x10: (2, 1), 0x11: (2, 1), 0x12: (2, 1), 0x13: (2, 1),
         0x14: (2, 1), 0x15: (1, 1), 0x16: (2, 1), 0x17: (2, 1), 0x18: (2, 1), 0x19: (1, 1), 0x1a: (2, 1), 0x1b: (2, 1),
         0x1c: (2, 1), 0x1d: (2, 1), 0x1e: (1, 1), 0x20: (2, 1), 0x30: (0, 1), 0x31: (1, 1), 0x32: (0, 1), 0x33: (0, 1),
         0x34: (0, 1), 0x35: (1, 1), 0x36: (0, 1), 0x37: (3, 0), 0x38: (0, 1), 0x39: (3, 0), 0x3a: (0, 1), 0x3b: (1, 1),
         0x3c: (4, 0), 0x3d: (0, 1), 0x3e: (3, 0), 0x3f: (1, 1), 0x40: (1, 1), 0x41: (0, 1), 0x42: (0, 1), 0x43: (0, 1),
         0x44: (0, 1), 0x45: (0, 1), 0x46: (0, 1), 0x47: (0, 1), 0x48: (0, 1), 0x49: (1, 1), 0x4a: (0, 1), 0x50: (1, 0),
         0x51: (1, 1), 0x52: (2, 0), 0x53: (2, 0), 0x54: (1, 1), 0x55: (2, 0), 0x56: (1, 0), 0x57: (2, 0), 0x58: (0, 1),
         0x59: (0, 1), 0x5a: (0, 1), 0x5b: (0, 0), 0x5c: (1, 1), 0x5d: (2, 0), 0x5e: (3, 0), 0xf0: (3, 1), 0xf1: (7, 1),
         0xf2: (7, 1), 0xf3: (2, 0), 0xf4: (6, 1), 0xf5: (4, 1), 0xfa: (6, 1), 0xfd: (2, 0), 0xfe: (0, 0), 0xff: (1, 0)}
    return t.get(op, (0, 0))


INTEREST = {0x05: 'SDIV', 0x07: 'SMOD', 0x08: 'ADDMOD', 0x09: 'MULMOD', 0x0b: 'SIGNEXTEND', 0x1a: 'BYTE',
            0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR', 0x0a: 'EXP', 0x04: 'DIV', 0x06: 'MOD', 0x10: 'LT', 0x11: 'GT',
            0x12: 'SLT', 0x13: 'SGT', 0x14: 'EQ', 0x15: 'ISZERO', 0x02: 'MUL'}


def scan(code):
    ins = []; i = 0
    while i < len(code):
        op = code[i]; k = op - 0x5f if 0x60 <= op <= 0x7f else 0
        ins.append((i, op, int.from_bytes(code[i + 1:i + 1 + k], 'big') if k else (0 if op == 0x5f else None)))
        i += 1 + k
    rec = {}; lit_shift_values = {}; deferred = {}
    st = []  # top at end; items: ('L', v) or ('U',)
    def get(d):  # d=0 top
        return st[-1 - d] if d < len(st) else ('U',)
    for idx, (pc, op, imm) in enumerate(ins):
        if op == 0x5b: st = []
        name = NAMES.get(op, hex(op))
        nin, nout = io(op)
        args = [get(d) for d in range(nin)]
        if op in INTEREST:
            key = INTEREST[op] + ' ' + ','.join('L' if a[0] == 'L' else 'R' for a in args)
            rec[key] = rec.get(key, 0) + 1
            if op in (0x1b, 0x1c, 0x1d) and args[1][0] == 'L' and args[0][0] != 'L':
                lit_shift_values.setdefault(INTEREST[op], {}).setdefault(hex(args[1][1]), []).append(pc)
            if op in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15):
                nxt = [o for _, o, _ in ins[idx + 1:idx + 3]]
                if nxt and nxt[0] == 0x57 or (len(nxt) > 1 and nxt[0] == 0x15 and nxt[1] == 0x57) or \
                        (len(nxt) > 1 and 0x60 <= nxt[0] <= 0x7f and nxt[1] == 0x57):
                    deferred[INTEREST[op]] = deferred.get(INTEREST[op], 0) + 1
        # apply
        if 0x80 <= op <= 0x8f:
            st = ([('U',)] * max(0, nin - len(st))) + st; st.append(st[-nin])
        elif 0x90 <= op <= 0x9f:
            st = ([('U',)] * max(0, nin - len(st))) + st; st[-1], st[-nin] = st[-nin], st[-1]
        else:
            for _ in range(nin):
                if st: st.pop()
            if nout:
                if imm is not None and (0x60 <= op <= 0x7f or op == 0x5f): st.append(('L', imm))
                elif op in FOLD and all(a[0] == 'L' for a in args): st.append(('L', FOLD[op](args[0][1], args[1][1])))
                elif op == 0x19 and args[0][0] == 'L': st.append(('L', M ^ args[0][1]))
                else: st.append(('U',))
        if op in END: st = []
    return rec, lit_shift_values, deferred


if __name__ == '__main__':
    b = json.load(open(sys.argv[1])); code = bytes.fromhex(b['runtime'])
    rec, lsv, dfr = scan(code)
    out = {'operandKinds': dict(sorted(rec.items())), 'literalValueShiftedByVariable': lsv, 'comparisonsIntoJumpi': dfr}
    print(json.dumps(out, indent=1))
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
