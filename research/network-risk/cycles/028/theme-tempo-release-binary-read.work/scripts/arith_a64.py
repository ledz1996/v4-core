"""Runs the shipped aarch64 arithmetic instruction handlers of tempo v1.19.1 in the a64emu model.

The handlers are taken from the three interpreter dispatch tables of the release binary (read from its
R_AARCH64_RELATIVE relocations), with every routine they call (ruint 1.21.1 div_rem_by_ref, rem_by_ref,
add_mod_by_ref, div_rem_bits_plus_one, mul_mod_by_ref, the Knuth helpers). memcpy, memset and memmove are
modelled in Python; panic entry points raise. Results are compared with Python integers.

usage: python3 -I arith_a64.py <build dir> <bin> <out.json> <set> [fault] [shard nshards]
  set: battery | targeted | maxmod | all
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a64emu import Prog, Mem, CPU, Stop, M64

BUILD, BIN, OUT, SET = sys.argv[1:5]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
SHARD, NSHARD = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 1)
M = (1 << 256) - 1
SIGN = 1 << 255

fb = open(BIN, 'rb').read()
prog = Prog([open(os.path.join(BUILD, 'a64_arith.s')).read()])
rel = {}
for l in open(os.path.join(BUILD, 'a64_relative.txt')):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
TABLES = {'A': 0x5dc6098, 'B': 0x5da9a50, 'C': 0x5dc6898}
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
HANDLER = {(fam, op): rel[base + 8 * code] for fam, base in TABLES.items() for op, code in OPS.items()}

# planted one-instruction faults, one per routine family, to show the comparison can fail
FAULTS = {
    # mul_mod_by_ref: the MAX-modulus test (cmn x8, #1) is turned into a test against 0, so the
    # end-around-carry fast path is never taken for modulus 2^256-1
    'mulmod_max': (0x42bab70, ('cmn', ['x8', '#0x2'])),
    # mul_mod_by_ref, end-around-carry path for modulus 2^256-1: one carry of the product is dropped
    'mulmod_carry': (0x42bac1c, ('mov', ['x17', 'x18'])),
    # mul_mod_by_ref, Knuth path: the MG10 reciprocal table is read 16 entries off
    'recip_mulmod': (0x42bb014, ('add', ['x12', 'x12', '#0xfe4'])),
    # div_rem_by_ref: the MG10 reciprocal table is read 16 entries off at its first use
    'recip_div': (0x18ed1ec, ('add', ['x12', 'x12', '#0xfe4'])),
    # mul_mod_by_ref, rem_nxm_spare_limb skip test (knuth.rs 133-136): '<' on the top two limbs becomes
    # '<=', which is the ruint 1.21.0 fault fixed in 1.21.1; three instructions are replaced
    'skip_le': [(0x42baff4, ('cmp', ['x10', 'x15'])), (0x42baff8, ('sbcs', ['xzr', 'x8', 'x14'])),
                (0x42baffc, ('cset', ['w11', 'hs']))],
    # ADDMOD inlined fast path: the final borrow select uses the wrong condition
    'addmod_fast': (0x3b5b0dc, ('csel', ['w12', 'wzr', 'w14', 'hs'])),
    # SHR handler: the 0x100 bound becomes 0xff
    'shr_bound': (0x3b60a58, ('cmp', ['x9', '#0xff'])),
}
faults = {}
if FAULT in FAULTS:
    spec = FAULTS[FAULT]
    for a, rep in (spec if isinstance(spec, list) else [spec]):
        faults[a] = lambda cpu, mn, ops, rep=rep: rep
elif FAULT != 'none':
    raise SystemExit('unknown fault')


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
    d, src, n = cpu.x[0], cpu.x[1], cpu.x[2]
    data = [cpu.m.read(src + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.m.write(d + i, 1, v)


def ext_memset(cpu):
    d, v, n = cpu.x[0], cpu.x[1] & 0xff, cpu.x[2]
    for i in range(n):
        cpu.m.write(d + i, 1, v)


def panic(cpu):
    raise Stop('panic called')


EXTERNS = {0x18855b0: ext_memcpy, 0x1884a50: ext_memcpy, 0x1885410: ext_memset,
           0x1c85030: panic, 0x1c898ec: panic, 0x1c838dc: panic}

visited = set()


def run(fam, op, a, b, c):
    k = ARITY.get(op, 2)
    words = [a, b, c][:k]
    mem = Mem(fb, 0, 0x18742d8)
    st = mem.add(STACK, 32 * 8)
    stack = [GUARD, GUARD] + list(reversed(words))  # bottom .. top; a is the top
    for i, w in enumerate(stack):
        st[32 * i:32 * i + 32] = w.to_bytes(32, 'little')
    mem.add(LENP, 8)
    mem.write(LENP, 8, len(stack))
    mem.add(CTX, 0x400)
    mem.add(PARAMS, 0x400)
    mem.write(CTX + 0xb0, 8, PARAMS)
    mem.write(PARAMS + 0x340, 4, 50)
    mem.write(CTX + 0xf8, 8, 1 << 40)
    mem.add(SP - 0x20000, 0x20000)
    cpu = CPU(prog, mem, externs=EXTERNS, faults=faults)
    cpu.x[31] = SP
    h = HANDLER[(fam, op)]
    if fam == 'B':
        r = cpu.call(h, [0, STACK, LENP, CTX])
        if r & 0xff:
            raise Stop('status %d' % (r & 0xff))
        newlen = mem.read(LENP, 8)
    else:
        r = cpu.call(h, [len(stack), STACK, 1 << 40, CTX])
        st_b = mem.read(CTX + 0x147, 1)
        if st_b:
            raise Stop('status byte %d' % st_b)
        newlen = r & 0x7ff
    visited.update(cpu.visited)
    if newlen != len(stack) - k + 1:
        raise Stop('stack length %d' % newlen)
    for i in range(2):
        if int.from_bytes(st[32 * i:32 * i + 32], 'little') != GUARD:
            raise Stop('guard word changed')
    return int.from_bytes(st[32 * (newlen - 1):32 * newlen], 'little'), cpu.steps


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
