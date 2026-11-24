"""List every MUL, MULMOD, ADDMOD and EXP of the PoolManager runtime and the operands that
Monad's compiler sees as literals.

The block rules follow category/vm/compiler (v0.16.5): a block starts at every JUMPDEST and
after JUMP, JUMPI and the terminators. Literal tracking of the virtual stack starts empty at
a block that is a jump destination. After JUMPI the stack is kept for the fall-through block
when that block is not a jump destination (Emitter::jumpi, emitter.cpp:3407-3427).
Literal folding is modelled for the pure opcodes the emitter folds when all inputs are
literals. Unknown values are None.

Usage: python3 sites.py <build/PoolManager.json> <cycles/009/.../instrs.json> <out.json>
"""
import sys, json

M = 2 ** 256
def s(x): return x - M if x >> 255 else x

FOLD = {
    0x01: lambda a, b: (a + b) % M, 0x02: lambda a, b: (a * b) % M, 0x03: lambda a, b: (a - b) % M,
    0x04: lambda a, b: a // b if b else 0, 0x06: lambda a, b: a % b if b else 0,
    0x10: lambda a, b: int(a < b), 0x11: lambda a, b: int(a > b), 0x14: lambda a, b: int(a == b),
    0x16: lambda a, b: a & b, 0x17: lambda a, b: a | b, 0x18: lambda a, b: a ^ b,
    0x1b: lambda a, b: (b << a) % M if a < 256 else 0, 0x1c: lambda a, b: b >> a if a < 256 else 0,
    0x0a: lambda a, b: pow(a, b, M),
}
UN = {0x15: lambda a: int(a == 0), 0x19: lambda a: M - 1 - a}
NAMES = {0x02: 'MUL', 0x09: 'MULMOD', 0x08: 'ADDMOD', 0x0a: 'EXP'}
# stack inputs, outputs for opcodes that are not modelled explicitly
def io(op):
    if 0x01 <= op <= 0x0b or 0x10 <= op <= 0x1d:
        if op in (0x08, 0x09): return 3, 1
        if op in (0x15, 0x19): return 1, 1
        return 2, 1
    tab = {0x20: (2, 1), 0x30: (0, 1), 0x31: (1, 1), 0x32: (0, 1), 0x33: (0, 1), 0x34: (0, 1),
           0x35: (1, 1), 0x36: (0, 1), 0x37: (3, 0), 0x38: (0, 1), 0x39: (3, 0), 0x3a: (0, 1),
           0x3b: (1, 1), 0x3c: (4, 0), 0x3d: (0, 1), 0x3e: (3, 0), 0x3f: (1, 1), 0x40: (1, 1),
           0x41: (0, 1), 0x42: (0, 1), 0x43: (0, 1), 0x44: (0, 1), 0x45: (0, 1), 0x46: (0, 1),
           0x47: (0, 1), 0x48: (0, 1), 0x49: (1, 1), 0x4a: (0, 1), 0x50: (1, 0), 0x51: (1, 1),
           0x52: (2, 0), 0x53: (2, 0), 0x54: (1, 1), 0x55: (2, 0), 0x58: (0, 1), 0x59: (0, 1),
           0x5a: (0, 1), 0x5c: (1, 1), 0x5d: (2, 0), 0x5e: (3, 0), 0xa0: (2, 0), 0xa1: (3, 0),
           0xa2: (4, 0), 0xa3: (5, 0), 0xa4: (6, 0), 0xf0: (3, 1), 0xf1: (7, 1), 0xf2: (7, 1),
           0xf4: (6, 1), 0xf5: (4, 1), 0xfa: (6, 1)}
    return tab.get(op, (0, 0))


def main():
    code = bytes.fromhex(json.load(open(sys.argv[1]))['runtime'].removeprefix('0x'))
    instrs = {e['pc']: e for e in json.load(open(sys.argv[2]))}
    ins = []; i = 0
    while i < len(code):
        op = code[i]; k = op - 0x5f if 0x60 <= op <= 0x7f else 0
        ins.append((i, op, int.from_bytes(code[i + 1:i + 1 + k], 'big') if k else (0 if op == 0x5f else None)))
        i += 1 + k
    jd = {pc for pc, op, _ in ins if op == 0x5b}
    stack = []; base = 0  # stack is a list of known values or None; base counts unknown entries below
    sites = []
    def pop():
        return stack.pop() if stack else None
    for idx, (pc, op, imm) in enumerate(ins):
        if op == 0x5b:
            stack = []
        if op in NAMES:
            n = 3 if op in (0x08, 0x09) else 2
            ops = [stack[-1 - j] if j < len(stack) else None for j in range(n)]
            e = instrs.get(pc, {})
            sites.append({'pc': pc, 'op': NAMES[op],
                          'operandsTopFirst': [None if v is None else hex(v) for v in ops],
                          'src': e.get('src'), 'fn': e.get('fn'), 'yul': e.get('yul'),
                          'text': (e.get('text') or '')[:120]})
        if 0x5f <= op <= 0x7f:
            stack.append(imm)
        elif 0x80 <= op <= 0x8f:
            d = op - 0x7f
            stack.append(stack[-d] if d <= len(stack) else None)
        elif 0x90 <= op <= 0x9f:
            d = op - 0x8f
            while len(stack) < d + 1: stack.insert(0, None)
            stack[-1], stack[-1 - d] = stack[-1 - d], stack[-1]
        elif op in FOLD:
            a = pop(); b = pop()
            stack.append(FOLD[op](a, b) if a is not None and b is not None else None)
        elif op in UN:
            a = pop(); stack.append(UN[op](a) if a is not None else None)
        elif op in (0x56,):
            pop(); stack = []
        elif op == 0x57:
            pop(); pop()
            nxt = ins[idx + 1][0] if idx + 1 < len(ins) else None
            if nxt in jd: stack = []
        elif op in (0x00, 0xf3, 0xfd, 0xfe, 0xff):
            stack = []
        else:
            a, b = io(op)
            for _ in range(a): pop()
            for _ in range(b): stack.append(None)
    lit = [x for x in sites if any(v is not None for v in x['operandsTopFirst'])]
    json.dump({'codeBytes': len(code), 'sites': sites, 'withLiteral': len(lit)}, open(sys.argv[3], 'w'), indent=1)
    for x in sites:
        print(x['pc'], x['op'], x['operandsTopFirst'], x['src'], x['fn'])


if __name__ == '__main__':
    main()
