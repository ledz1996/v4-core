"""Run the shipped arithmetic, comparison and shift handlers of an op-reth or base binary in the x86-64 or
AArch64 model and compare with Python integers. The disassembly text is interpreted; no code from the
binary runs on the CPU.

usage: python3 -I arith.py <config.json> <out.json> <set> [fault] [shard nshards]
config: {"bin", "arch": "x86"|"a64", "asm", "table", "rel", "stack_ptr", "stack_len", "gas", "host_params",
         "exp_byte_off", "got": {"hex": "memcpy|memset|memmove|panic"}, "externs": {...}, "faults": {...}}
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from image import image
CFG = json.load(open(sys.argv[1])); OUT, SET = sys.argv[2:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SHARD, NSHARD = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (0, 1)
M = (1 << 256) - 1; SIGN = 1 << 255
IMG, SEGS = image(CFG['bin'])
rel = {}
for l in open(CFG['rel']):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
T = int(CFG['table'], 16)
HANDLER = {op: rel[T + 8 * code] for op, code in OPS.items()}
X86 = CFG['arch'] == 'x86'
STACK, CTX, HOST, PARAMS, SP = 0x70000000, 0x71000000, 0x72000000, 0x73000000, 0x7ff000000000
GUARD = int('a5' * 32, 16)
ASMS = CFG['asm'] if isinstance(CFG['asm'], list) else [CFG['asm']]
ONLY = set(os.environ['ONLY'].split(',')) if os.environ.get('ONLY') else None
if X86:
    from x86emu2 import CPU2 as _CPU2, Prog, Stop, rewrite_rip
    import re as _re
    class CPU2(_CPU2):
        def _regtarget(self, o):
            if _re.match(r'^[a-z0-9]+$', o[0]) and not _re.match(r'^[0-9a-f]+$', o[0]):
                v = self.getr(o[0])[0]
                if v in self.externs: return self.externs[v]
                raise Stop('indirect to %x' % v)
            return None
        def i_call(self, o, pc, n):
            f = self._regtarget(o)
            if f is not None: f(self); return n
            return super().i_call(o, pc, n)
        def i_jmp(self, o, pc, n):
            f = self._regtarget(o)
            if f is not None:
                f(self); return self.i_ret([], pc, n)
            return super().i_jmp(o, pc, n)
    prog = Prog(rewrite_rip('\n'.join(open(a).read() for a in ASMS)))
else:
    from a64emu import Prog, Mem, CPU, Stop
    prog = Prog([open(a).read() for a in ASMS])
# planted faults: {"name": [[hex addr, replacement text or [mn, [ops]]], ...]}
faults = {}
if FAULT != 'none':
    for a, rep in CFG['faults'][FAULT]:
        if X86: faults[int(a, 16)] = rep
        else: faults[int(a, 16)] = (lambda cpu, mn, ops, rep=rep: (rep[0], rep[1]))

def s(x): return x - (1 << 256) if x & SIGN else x
def u(x): return x & M
def ref(op, a, b, c):
    if op == 'ADD': return (a + b) & M
    if op == 'MUL': return (a * b) & M
    if op == 'SUB': return (a - b) & M
    if op == 'DIV': return a // b if b else 0
    if op == 'MOD': return a % b if b else 0
    if op == 'SDIV':
        if b == 0: return 0
        q = abs(s(a)) // abs(s(b)); return u(-q if (s(a) < 0) != (s(b) < 0) else q)
    if op == 'SMOD':
        if b == 0: return 0
        r = abs(s(a)) % abs(s(b)); return u(-r if s(a) < 0 else r)
    if op == 'ADDMOD': return (a + b) % c if c else 0
    if op == 'MULMOD': return (a * b) % c if c else 0
    if op == 'EXP': return pow(a, b, 1 << 256)
    if op == 'SIGNEXTEND':
        if a >= 31: return b
        bit = 8 * a + 7
        return (b | (M ^ ((1 << bit) - 1))) if (b >> bit) & 1 else b & ((1 << bit) - 1)
    if op == 'LT': return int(a < b)
    if op == 'GT': return int(a > b)
    if op == 'SLT': return int(s(a) < s(b))
    if op == 'SGT': return int(s(a) > s(b))
    if op == 'EQ': return int(a == b)
    if op == 'ISZERO': return int(a == 0)
    if op == 'AND': return a & b
    if op == 'OR': return a | b
    if op == 'XOR': return a ^ b
    if op == 'NOT': return a ^ M
    if op == 'BYTE': return 0 if a >= 32 else (b >> (8 * (31 - a))) & 0xff
    if op == 'SHL': return (b << a) & M if a < 256 else 0
    if op == 'SHR': return b >> a if a < 256 else 0
    if op == 'SAR': return u(s(b) >> min(a, 256))
    raise KeyError(op)

def A(cpu, i): return cpu.r[['rdi', 'rsi', 'rdx'][i]] if X86 else cpu.x[i]
def RD(cpu, a, n): return cpu.read(a, n) if X86 else cpu.m.read(a, n)
def WR(cpu, a, n, v): return cpu.write(a, n, v) if X86 else cpu.m.write(a, n, v)
def ext_memcpy(cpu):
    d, src, n = A(cpu, 0), A(cpu, 1), A(cpu, 2)
    data = [RD(cpu, src + i, 1) for i in range(n)]
    for i, v in enumerate(data): WR(cpu, d + i, 1, v)
    if X86: cpu.r['rax'] = d
def ext_memset(cpu):
    d, v, n = A(cpu, 0), A(cpu, 1) & 0xff, A(cpu, 2)
    for i in range(n): WR(cpu, d + i, 1, v)
    if X86: cpu.r['rax'] = d
def panic(cpu): raise Stop('panic or abort called')
KIND = {'memcpy': ext_memcpy, 'memmove': ext_memcpy, 'memset': ext_memset, 'panic': panic}
GOT = {int(k, 16): KIND[v] for k, v in CFG.get('got', {}).items()}
EXT = {int(k, 16): KIND[v] for k, v in CFG.get('externs', {}).items()}
# GOT slots hold sentinel values so that a call through a register loaded from a slot reaches the model
IMG = bytearray(IMG)
for i, (slot, fn) in enumerate(sorted(GOT.items())):
    sv = 0xfeed0000 + 16 * i; IMG[slot:slot + 8] = sv.to_bytes(8, 'little'); EXT[sv] = fn
IMG = bytes(IMG)
visited = set()
OFF_P, OFF_L, OFF_G = int(CFG['stack_ptr'], 16), int(CFG['stack_len'], 16), int(CFG['gas'], 16)
OFF_H, OFF_E = int(CFG['host_params'], 16), int(CFG['exp_byte_off'], 16)

def run(op, a, b, c):
    k = ARITY.get(op, 2)
    stack = [GUARD, GUARD] + list(reversed([a, b, c][:k]))
    if X86:
        cpu = CPU2(prog, IMG, len(IMG), externs=EXT, got=GOT, faults=faults)
        wr = cpu.write; rd = cpu.read
    else:
        mem = Mem(IMG, 0, len(IMG))
        mem.add(STACK, 32 * 8); mem.add(CTX, 0x1000); mem.add(HOST, 0x1000); mem.add(PARAMS, 0x400)
        mem.add(SP - 0x20000, 0x20000)
        cpu = CPU(prog, mem, externs={**EXT, **GOT}, faults=faults); cpu.x[31] = SP
        wr = mem.write; rd = mem.read
    for i, w in enumerate(stack): wr(STACK + 32 * i, 32, w)
    for i in range(len(stack), 8): wr(STACK + 32 * i, 32, 0)
    wr(CTX + OFF_P, 8, STACK); wr(CTX + OFF_L, 8, len(stack)); wr(CTX + OFF_G, 8, 1 << 40)
    wr(CTX + int(CFG['spec_off'], 16), 1, int(CFG['spec_val'], 16))
    wr(HOST + OFF_H, 8, PARAMS); wr(PARAMS + OFF_E, 8, 50)
    r = cpu.call(HANDLER[op], [CTX, HOST])
    if r & 0xff: raise Stop('status %#x' % (r & 0xff))
    visited.update(cpu.visited)
    newlen = rd(CTX + OFF_L, 8)
    if newlen != len(stack) - k + 1: raise Stop('stack length %d' % newlen)
    for i in range(2):
        if rd(STACK + 32 * i, 32) != GUARD: raise Stop('guard word changed')
    return rd(STACK + 32 * (newlen - 1), 32), cpu.steps

def vectors():
    if SET in ('battery', 'all'):
        import battery
        for op, a, b, c in battery.vectors():
            if op in OPS: yield 'battery', op, a, b, c
            elif op == 'MULDIV512':
                yield 'battery-muldiv', 'MULMOD', a, b, c; yield 'battery-muldiv', 'MULMOD', a, b, M
                yield 'battery-muldiv', 'MUL', a, b, 0
            elif op == 'DIVUP':
                yield 'battery-divup', 'DIV', a, b, 0; yield 'battery-divup', 'MOD', a, b, 0
    if SET in ('targeted', 'all'):
        import targeted
        for op, a, b, c in targeted.vectors():
            if op in OPS: yield 'targeted', op, a, b, c
            elif op == 'MULDIV512':
                yield 'targeted-muldiv', 'MULMOD', a, b, c; yield 'targeted-muldiv', 'MULMOD', a, b, M
    if SET in ('maxmod', 'all', 'faultshape'):
        base = '/home/user/v4-core/research/network-risk/cycles/025/stablecoin-l1.work/'
        for name in ('maxmod', 'maxmod2'):
            g = {'__file__': base + name + '.py', '__name__': name + '_vectors'}
            exec(open(base + name + '.py').read().split("\nif __name__")[0], g)
            for a, b, n in g['vecs']():
                yield name, 'MULMOD', a, b, n; yield name, 'ADDMOD', a, b, n; yield name + '-prod1', 'MULMOD', a, b, M
    if SET in ('v4math', 'all'):
        import v4shapes
        for tag, op, a, b, c in v4shapes.vectors(): yield tag, op, a, b, c

res = {'config': sys.argv[1], 'set': SET, 'fault': FAULT, 'shard': [SHARD, NSHARD], 'cases': 0, 'mismatches': 0,
       'errors': 0, 'steps': 0, 'byOp': {}, 'records': [], 'vectorCount': {}}
k = -1
LIMIT = int(os.environ.get('LIMIT', '0'))
for tag, op, a, b, c in vectors():
    k += 1
    res['vectorCount'][tag] = res['vectorCount'].get(tag, 0) + 1
    if k % NSHARD != SHARD: continue
    if ONLY and op not in ONLY: continue
    if LIMIT and res['cases'] >= LIMIT: break
    want = ref(op, a, b, c)
    st = res['byOp'].setdefault(op, [0, 0, 0]); st[0] += 1; res['cases'] += 1
    try:
        got, steps = run(op, a, b, c); res['steps'] += steps
    except Stop as e:
        st[2] += 1; res['errors'] += 1
        res['records'].append({'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': str(e)}); continue
    if got != want:
        st[1] += 1; res['mismatches'] += 1
        res['records'].append({'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'model': hex(got), 'reference': hex(want)})
    if FAULT != 'none' and res['mismatches'] + res['errors'] >= 20: break
res['visited'] = len(visited)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'steps', res['steps'])
