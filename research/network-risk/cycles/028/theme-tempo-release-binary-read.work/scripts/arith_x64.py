"""Runs the shipped x86_64 arithmetic instruction handlers of tempo v1.19.1 in the x86emu2 model.

Same method as arith_a64.py: the handlers come from the three interpreter dispatch tables of the x86_64
release binary (R_X86_64_RELATIVE relocations), with every routine they call (ruint 1.21.1
div_rem_by_ref 0x19145b0, rem_by_ref 0x1913350, add_mod_by_ref 0x4af2910, div_rem_bits_plus_one 0x4af2a60,
mul_mod_by_ref 0x4af3d90). memcpy, memset and memmove are reached through GOT slots and modelled in Python.

usage: python3 -I arith_x64.py <build dir> <bin> <out.json> <set> [fault] [shard nshards]
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x86emu2 import CPU2, Prog, Stop, rewrite_rip, M64

BUILD, BIN, OUT, SET = sys.argv[1:5]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
SHARD, NSHARD = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 1)
M = (1 << 256) - 1
SIGN = 1 << 255

fb = open(BIN, 'rb').read()
prog = Prog(rewrite_rip(open(os.path.join(BUILD, 'x64_arith.s')).read()))
rel = {}
for l in open(os.path.join(BUILD, 'x64_relative.txt')):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
TABLES = {'A': 0x6c09a28, 'B': 0x6becbf8, 'C': 0x6c09228}
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
HANDLER = {(fam, op): rel[base + 8 * code] for fam, base in TABLES.items() for op, code in OPS.items()}

# planted one-instruction faults, one per routine family, to show the comparison can fail
FAULTS = {
    # mul_mod_by_ref: the first carry of the end-around-carry sum for modulus 2^256-1 is dropped
    'mulmod_carry': None,
    # reciprocal on x86_64 is a div instruction: its dividend high word !d becomes d-1
    'recip_div': None,
    # SHR handler bound
    'shr_bound': None,
}
faults = {}
FAULT_AT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'x64_faults.json')))
if FAULT != 'none':
    a, rep = FAULT_AT[FAULT]
    faults[int(a, 16)] = rep


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


STACK, LENP, CTX, PARAMS, SP = 0x30000000, 0x31000000, 0x32000000, 0x33000000, 0x7ff000000000
GUARD = 0xa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5


def ext_memcpy(cpu):
    d, src, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    data = [cpu.read(src + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.write(d + i, 1, v)
    cpu.r['rax'] = d


def ext_memset(cpu):
    d, v, n = cpu.r['rdi'], cpu.r['rsi'] & 0xff, cpu.r['rdx']
    for i in range(n):
        cpu.write(d + i, 1, v)
    cpu.r['rax'] = d


def panic(cpu):
    raise Stop('abort called')


GOT = {0x6c84570: ext_memcpy, 0x6c84580: ext_memcpy, 0x6c84578: ext_memset, 0x6c84558: panic}

visited = set()


def run(fam, op, a, b, c):
    k = ARITY.get(op, 2)
    words = [a, b, c][:k]
    cpu = CPU2(prog, fb, 0x189aab8, got=GOT, faults=faults)
    stack = [GUARD, GUARD] + list(reversed(words))
    for i, w in enumerate(stack):
        cpu.write(STACK + 32 * i, 32, w)
    cpu.write(LENP, 8, len(stack))
    cpu.write(CTX + 0xb0, 8, PARAMS)
    cpu.write(PARAMS + 0x340, 4, 50)
    cpu.write(CTX + 0xf8, 8, 1 << 40)
    cpu.write(CTX + 0x147, 1, 0)
    h = HANDLER[(fam, op)]
    if fam == 'B':
        r = cpu.call(h, [0, STACK, LENP, CTX])
        if r & 0xff:
            raise Stop('status %d' % (r & 0xff))
        newlen = cpu.read(LENP, 8)
    else:
        r = cpu.call(h, [len(stack), STACK, 1 << 40, CTX])
        if cpu.read(CTX + 0x147, 1):
            raise Stop('status byte %d' % cpu.read(CTX + 0x147, 1))
        newlen = r & 0x7ff
    visited.update(cpu.visited)
    if newlen != len(stack) - k + 1:
        raise Stop('stack length %d' % newlen)
    for i in range(2):
        if cpu.read(STACK + 32 * i, 32) != GUARD:
            raise Stop('guard word changed')
    return cpu.read(STACK + 32 * (newlen - 1), 32), cpu.steps


def vectors():
    sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
    if SET in ('battery', 'all'):
        import battery
        for op, a, b, c in battery.vectors():
            if op in OPS:
                yield 'battery', op, a, b, c
            elif op == 'MULDIV512':
                yield 'battery-muldiv', 'MULMOD', a, b, c
                yield 'battery-muldiv', 'MULMOD', a, b, M
            elif op == 'DIVUP':
                yield 'battery-divup', 'DIV', a, b, 0
                yield 'battery-divup', 'MOD', a, b, 0
    if SET in ('targeted', 'all'):
        import targeted
        for op, a, b, c in targeted.vectors():
            if op in OPS:
                yield 'targeted', op, a, b, c
            elif op == 'MULDIV512':
                yield 'targeted-muldiv', 'MULMOD', a, b, c
                yield 'targeted-muldiv', 'MULMOD', a, b, M
    if SET in ('maxmod', 'all'):
        base = '/home/user/v4-core/research/network-risk/cycles/025/stablecoin-l1.work/'
        g = {'__file__': base + 'maxmod.py', '__name__': 'maxmod_vectors'}
        exec(open(base + 'maxmod.py').read().split("\nif __name__")[0], g)
        V1 = g['vecs']()
        g2 = {'__file__': base + 'maxmod2.py', '__name__': 'maxmod2_vectors'}
        exec(open(base + 'maxmod2.py').read().split("\nif __name__")[0], g2)
        V2 = g2['vecs']()
        for tag, V in (('maxmod', V1), ('maxmod2', V2)):
            for a, b, n in V:
                yield tag, 'MULMOD', a, b, n
                yield tag, 'ADDMOD', a, b, n
                yield tag + '-prod1', 'MULMOD', a, b, M


FAMS = os.environ.get('FAMS', 'B,A,C').split(',')
res = {'set': SET, 'fault': FAULT, 'families': FAMS, 'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0,
       'byOp': {}, 'records': [], 'vectorCount': {}}
k = -1
for tag, op, a, b, c in vectors():
    k += 1
    res['vectorCount'][tag] = res['vectorCount'].get(tag, 0) + 1
    if k % NSHARD != SHARD:
        continue
    want = ref(op, a, b, c)
    for fam in FAMS:
        key = fam + ':' + op
        st = res['byOp'].setdefault(key, [0, 0, 0])
        st[0] += 1
        res['cases'] += 1
        try:
            got, steps = run(fam, op, a, b, c)
            res['steps'] += steps
        except Stop as e:
            st[2] += 1
            res['errors'] += 1
            if len(res['records']) < 200:
                res['records'].append({'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': str(e)})
            continue
        if got != want:
            st[1] += 1
            res['mismatches'] += 1
            if len(res['records']) < 200:
                res['records'].append({'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c),
                                       'model': hex(got), 'reference': hex(want)})
res['visited'] = sorted(visited)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'steps', res['steps'])
