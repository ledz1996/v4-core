"""Cycle 39: the arithmetic, comparison and shift handlers of the released reth v2.11.0 aarch64 binary
(reth-v2.11.0-aarch64-unknown-linux-gnu.tar.gz) in the cycle 28 AArch64 model, compared with Python integers.

Port of cycle 38's rarith.py (x86_64) to the aarch64 release. Handlers come from the instruction tables found through
the R_AARCH64_RELATIVE relocations (rrel.py of this directory): one run of 7695 slots at 0x72f5408, 13 tables per
family, X at 0x72f5480.. and Y at 0x72fcc80.., 0x800 bytes each, the same layout as on x86_64. Handler ABI read from
the ADD handler at 0x2957d88: x0 = (pc << 11) | stack length, x1 = stack base (32-byte little-endian words, bottom
first), x2 = gas left, x3 = interpreter context; status byte at context+0x147; x0 returns the new pc and length, x1 the
gas left. Functions were disassembled by cycle 38's extract2.py through the .eh_frame ranges (arith.s). bcmp, memcpy,
memset and memmove are modelled in Python; abort stops the run. The binary is read as data only.
usage: python3 -I ra64.py <dl dir> <set> <out.json> [shard nshard]
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
C38 = os.path.join(HERE, '..', '..', '..', '038', 'theme-ethereum-client-binaries-lift.work', 'scripts')
sys.path.insert(0, C38); sys.path.insert(0, os.path.join(C38, 'emu'))
from a64emu import CPU, Prog, Mem, Stop
import goshim as G

DL, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SHARD, NSHARD = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
BIN = os.path.join(DL, 'x/reth')
M = G.M
rel = {}
for l in open(os.path.join(DL, 'relative.txt')):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
BASES = {'X': 0x72f5480, 'Y': 0x72fcc80}
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
UNDEF = {'X': 0x295b704, 'Y': 0x296025c}
LAST = {f: b + 0x800 * 12 for f, b in BASES.items()}
HANDLER = {(f, op): rel[t + 8 * c] for f, t in LAST.items() for op, c in OPS.items()}
for f, b in BASES.items():
    for k in range(13):
        t = b + 0x800 * k
        for op, c in OPS.items():
            assert rel[t + 8 * c] in (HANDLER[(f, op)], UNDEF[f]), (hex(t), op)

TEXT = open(os.path.join(DL, 'arith.s')).read()
FAULT = os.environ.get('FAULT', '')  # 'hexaddr|old|new': planted fault, one text substitution on one instruction line
if FAULT:
    fa, fo, fn = FAULT.split('|'); lines = TEXT.split('\n')
    hit = [i for i, l in enumerate(lines) if l.strip().startswith(fa + ':')]
    assert len(hit) == 1 and fo in lines[hit[0]], FAULT
    lines[hit[0]] = lines[hit[0]].replace(fo, fn, 1); TEXT = '\n'.join(lines)
prog = Prog([TEXT])
img = G.Image(BIN)
STACK, CTX, PARAMS, SPLO, SPTOP = 0x30000000, 0x32000000, 0x33000000, 0x7fff00000000, 0x7fff00100000
GUARD = G.GUARD


class IMem(Mem):
    def read(self, a, n):
        b, o = self._find(a, n)
        if b is not None:
            return int.from_bytes(b[o:o + n], 'little')
        if a in rel and n == 8:
            return rel[a]
        v = img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        return v


def ext_memcpy(cpu):
    d, s_, n = cpu.x[0], cpu.x[1], cpu.x[2]
    data = [cpu.m.read(s_ + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.m.write(d + i, 1, v)


def ext_memset(cpu):
    d, v, n = cpu.x[0], cpu.x[1] & 0xff, cpu.x[2]
    for i in range(n):
        cpu.m.write(d + i, 1, v)


def ext_bcmp(cpu):
    a, b, n = cpu.x[0], cpu.x[1], cpu.x[2]
    r = 0
    for i in range(n):
        x, y = cpu.m.read(a + i, 1), cpu.m.read(b + i, 1)
        if x != y:
            r = (x - y) & 0xffffffff; break
    cpu.x[0] = r


def stop(cpu): raise Stop('abort reached')


EXT = {0x247b9b0: ext_memcpy, 0x247ae40: ext_memcpy, 0x247b810: ext_memset, 0x247b770: ext_bcmp, 0x247bad0: stop,
       0x247c680: stop, 0x247c780: stop}
visited = set()


def run(fam, op, a, b, c):
    k = ARITY.get(op, 2)
    words = [a, b, c][:k]
    mem = IMem(None, 0, 0)
    mem.add(STACK, 0x10000); mem.add(CTX, 0x10000); mem.add(PARAMS, 0x10000);
    # EXP reads its per-byte gas from a parameter block at *(ctx+0xb0)+0x2f8 (handler 0x465ed74); 50 as on mainnet
    mem.write(CTX + 0xb0, 8, PARAMS); mem.write(PARAMS + 0x2f8, 4, 50); mem.write(CTX + 0xf8, 8, 1 << 40)
    mem.add(SPLO, SPTOP - SPLO + 0x1000)
    cpu = CPU(prog, mem, externs=EXT)
    cpu._pc_next = 0
    stack = [GUARD, GUARD] + list(reversed(words))
    for i, w in enumerate(stack):
        mem.write(STACK + 32 * i, 32, w)
    for i in range(len(stack), 8):
        mem.write(STACK + 32 * i, 32, GUARD)
    cpu.x[31] = SPTOP
    pc0 = 0x123; gas0 = 1 << 40
    r = cpu.call(HANDLER[(fam, op)], [(pc0 << 11) | len(stack), STACK, gas0, CTX], maxsteps=5_000_000)
    visited.update(cpu.visited)
    st = mem.read(CTX + 0x147, 1)
    if st:
        raise Stop('status byte %#x' % st)
    newlen = r & 0x7ff
    if newlen != len(stack) - k + 1:
        raise Stop('stack length %d' % newlen)
    if (r >> 11) != pc0 + 1:
        raise Stop('pc %#x' % (r >> 11))
    for i in list(range(2)) + list(range(len(stack), 8)):
        if mem.read(STACK + 32 * i, 32) != GUARD:
            raise Stop('guard word %d changed' % i)
    return mem.read(STACK + 32 * (newlen - 1), 32), cpu.steps, gas0 - cpu.x[1]


def ref(op, a, b, c):
    if op == 'AND': return a & b
    if op == 'OR': return a | b
    if op == 'XOR': return a ^ b
    if op == 'NOT': return a ^ M
    return G.ref(op, a, b, c)


src = open(os.path.join(C38, 'drive.py')).read(); src = src[:src.index('fspec = F.get')]
saved = sys.argv; sys.argv = ['drive.py', 'geth-amd64', SET, '0', '1', '/dev/null']
g = {'__name__': 'gen', '__file__': os.path.join(C38, 'drive.py')}
exec(compile(src, 'drive.py', 'exec'), g)
sys.argv = saved
FAMS = os.environ.get('FAMS', 'X,Y').split(',')
LIMIT = int(os.environ.get('LIMIT', '0'))
res = {'target': 'reth v2.11.0 aarch64', 'fault': FAULT, 'set': SET, 'seed': g['SEEDS'].get(SET), 'families': FAMS,
       'handlers': {'%s:%s' % k: hex(v) for k, v in HANDLER.items()},
       'shard': SHARD, 'nshard': NSHARD, 'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0, 'byOp': {}, 'records': []}
t0 = time.time(); n = 0
for k, (tag, op, a, b, c) in enumerate(g['GEN'][SET]()):
    if k % NSHARD != SHARD or op not in OPS:
        continue
    n += 1
    if LIMIT and n > LIMIT:
        break
    want = ref(op, a, b, c)
    for fam in FAMS:
        key = fam + ':' + op
        st = res['byOp'].setdefault(key, [0, 0, 0]); st[0] += 1; res['cases'] += 1
        try:
            got, steps, gas = run(fam, op, a, b, c)
            res['steps'] += steps
        except Exception as e:
            st[2] += 1; res['errors'] += 1
            if len(res['records']) < 300:
                res['records'].append({'index': k, 'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': '%s: %s' % (type(e).__name__, e)})
            continue
        if got != want:
            st[1] += 1; res['mismatches'] += 1
            res['records'].append({'index': k, 'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'model': hex(got), 'reference': hex(want)})
res['seconds'] = time.time() - t0
res['visited'] = len(visited)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'steps', res['steps'], flush=True)
