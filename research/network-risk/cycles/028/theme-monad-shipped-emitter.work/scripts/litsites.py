"""Cycle 28, Task 1. List the instruction sites of the deployed PoolManager runtime where Monad's emitter sees a
literal operand. Model: the emitter's virtual stack starts each basic block with unknown words (block boundaries at
JUMPDEST and after JUMP, JUMPI, STOP, RETURN, REVERT, INVALID, SELFDESTRUCT); PUSH gives a literal, DUP and SWAP move
it, and a pure operation whose inputs are all literals gives a literal (the emitter folds these, emitter.cpp at
v0.16.7). The sites found are cross-checked against the harness's emitted listing pm-asm-0.16.7.txt (cycle 27).
Output: out/litsites.json. usage: python3 -I litsites.py <repo-research-root> <outdir>"""
import sys, json, os, re, collections
R = sys.argv[1]; OUT = sys.argv[2]
M = (1 << 256) - 1
code = bytes.fromhex(json.load(open(os.path.join(R, 'build/PoolManager.json')))['runtime'].removeprefix('0x'))
jm = json.load(open(os.path.join(R, 'opcodes/jumpmap.json')))
runs = jm['runs']
def src_of(pc):
    best = None
    for r in runs:
        if r['from'] <= pc <= r['to']:
            if best is None or (r['to'] - r['from']) < (best['to'] - best['from']): best = r
    if best is None: return None
    s = best['src']; return '%s:%s' % (s['file'], s['line']) if s['line'] == s['endLine'] else '%s:%s-%s' % (s['file'], s['line'], s['endLine'])
def sx(v): return v - (1 << 256) if v >> 255 else v
def fold(op, a):
    if op == 0x01: return (a[0] + a[1]) & M
    if op == 0x02: return (a[0] * a[1]) & M
    if op == 0x03: return (a[0] - a[1]) & M
    if op == 0x04: return a[0] // a[1] if a[1] else 0
    if op == 0x05:
        x, y = sx(a[0]), sx(a[1])
        if y == 0: return 0
        q = abs(x) // abs(y); q = q if (x < 0) == (y < 0) else -q
        return q & M
    if op == 0x06: return a[0] % a[1] if a[1] else 0
    if op == 0x07:
        x, y = sx(a[0]), sx(a[1])
        if y == 0: return 0
        r = abs(x) % abs(y); return (-r if x < 0 else r) & M
    if op == 0x08: return (a[0] + a[1]) % a[2] if a[2] else 0
    if op == 0x09: return (a[0] * a[1]) % a[2] if a[2] else 0
    if op == 0x0a: return pow(a[0], a[1], 1 << 256)
    if op == 0x0b:
        b, x = a
        if b >= 31: return x
        bit = 8 * b + 7; m = (1 << (bit + 1)) - 1
        return (x | (M ^ m)) if (x >> bit) & 1 else (x & m)
    if op == 0x10: return int(a[0] < a[1])
    if op == 0x11: return int(a[0] > a[1])
    if op == 0x12: return int(sx(a[0]) < sx(a[1]))
    if op == 0x13: return int(sx(a[0]) > sx(a[1]))
    if op == 0x14: return int(a[0] == a[1])
    if op == 0x15: return int(a[0] == 0)
    if op == 0x16: return a[0] & a[1]
    if op == 0x17: return a[0] | a[1]
    if op == 0x18: return a[0] ^ a[1]
    if op == 0x19: return M ^ a[0]
    if op == 0x1a: return (a[1] >> (8 * (31 - a[0]))) & 0xff if a[0] < 32 else 0
    if op == 0x1b: return (a[1] << a[0]) & M if a[0] < 256 else 0
    if op == 0x1c: return a[1] >> a[0] if a[0] < 256 else 0
    if op == 0x1d: return (sx(a[1]) >> min(a[0], 256)) & M
    return None
NAMES = {0x01: 'ADD', 0x02: 'MUL', 0x03: 'SUB', 0x04: 'DIV', 0x05: 'SDIV', 0x06: 'MOD', 0x07: 'SMOD', 0x08: 'ADDMOD',
         0x09: 'MULMOD', 0x0a: 'EXP', 0x0b: 'SIGNEXTEND', 0x10: 'LT', 0x11: 'GT', 0x12: 'SLT', 0x13: 'SGT', 0x14: 'EQ',
         0x15: 'ISZERO', 0x16: 'AND', 0x17: 'OR', 0x18: 'XOR', 0x19: 'NOT', 0x1a: 'BYTE', 0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR'}
ARITY = {k: 2 for k in NAMES}; ARITY.update({0x08: 3, 0x09: 3, 0x15: 1, 0x19: 1})
# stack effects of other opcodes (in, out)
EFF = {0x30: (0, 1), 0x31: (1, 1), 0x32: (0, 1), 0x33: (0, 1), 0x34: (0, 1), 0x35: (1, 1), 0x36: (0, 1), 0x37: (3, 0),
       0x38: (0, 1), 0x39: (3, 0), 0x3a: (0, 1), 0x3b: (1, 1), 0x3c: (4, 0), 0x3d: (0, 1), 0x3e: (3, 0), 0x3f: (1, 1),
       0x40: (1, 1), 0x41: (0, 1), 0x42: (0, 1), 0x43: (0, 1), 0x44: (0, 1), 0x45: (0, 1), 0x46: (0, 1), 0x47: (0, 1),
       0x48: (0, 1), 0x49: (1, 1), 0x4a: (0, 1), 0x50: (1, 0), 0x51: (1, 1), 0x52: (2, 0), 0x53: (2, 0), 0x54: (1, 1),
       0x55: (2, 0), 0x56: (1, 0), 0x57: (2, 0), 0x58: (0, 1), 0x59: (0, 1), 0x5a: (0, 1), 0x5b: (0, 0), 0x5c: (1, 1),
       0x5d: (2, 0), 0x5e: (3, 0), 0x5f: (0, 1), 0x20: (2, 1), 0xf0: (3, 1), 0xf1: (7, 1), 0xf2: (7, 1), 0xf3: (2, 0),
       0xf4: (6, 1), 0xf5: (4, 1), 0xfa: (6, 1), 0xfd: (2, 0), 0xfe: (0, 0), 0xff: (1, 0), 0x00: (0, 0)}
for i in range(5): EFF[0xa0 + i] = (2 + i, 0)
TERM = {0x00, 0x56, 0x57, 0xf3, 0xfd, 0xfe, 0xff}
U = None  # unknown
sites = []; pc = 0; st = []
counter = collections.Counter()
while pc < len(code):
    op = code[pc]
    if op == 0x5b: st = []
    if 0x60 <= op <= 0x7f:
        n = op - 0x5f; st.append(int.from_bytes(code[pc + 1:pc + 1 + n], 'big')); pc += 1 + n; continue
    if 0x80 <= op <= 0x8f:
        k = op - 0x7f
        while len(st) < k: st.insert(0, U)
        st.append(st[-k])
    elif 0x90 <= op <= 0x9f:
        k = op - 0x8f
        while len(st) < k + 1: st.insert(0, U)
        st[-1], st[-1 - k] = st[-1 - k], st[-1]
    elif op in NAMES:
        n = ARITY[op]
        while len(st) < n: st.insert(0, U)
        args = [st.pop() for _ in range(n)]  # args[0] is top
        lit = [a is not U for a in args]
        if any(lit):
            v = fold(op, args) if all(lit) else U
            sites.append({'pc': pc, 'op': NAMES[op], 'literal': ['%d' % i for i, l in enumerate(lit) if l],
                          'values': [hex(a) if a is not U else None for a in args], 'folded': all(lit), 'src': src_of(pc)})
            counter[(NAMES[op], all(lit))] += 1
            st.append(v)
        else:
            st.append(U)
    else:
        i, o = EFF.get(op, (0, 0))
        while len(st) < i: st.insert(0, U)
        for _ in range(i): st.pop()
        for _ in range(o): st.append(U)
    if op in TERM: st = []
    pc += 1
json.dump({'codeBytes': len(code), 'sites': sites, 'counts': {'%s%s' % (k[0], ' folded' if k[1] else ''): v for k, v in sorted(counter.items())}},
          open(os.path.join(OUT, 'litsites.json'), 'w'), indent=1)
for k, v in sorted(counter.items()): print(k, v)
print('sites', len(sites))
