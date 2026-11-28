"""Cycle 38: the arithmetic, comparison and shift handlers of the released reth v2.11.0 x86_64 binary (evm2 rev
66687c18, ruint 1.21.1, rustc 1.99.1) in the x86-64 model, compared with Python integers.

Handlers come from the instruction tables of the binary, found through its R_X86_64_RELATIVE relocations
(rrel.py): 26 tables in two handler families, X at 0x7f2fdd0..0x7f35dd0 and Y at 0x7f375d0..0x7f3d5d0, one table
per fork. Every table maps the 25 opcodes below to one handler per family, so the handler of the latest table of
each family (X 0x7f35dd0, Y 0x7f3d5d0) is the handler of every fork. The functions they reach were disassembled by
extract2.py through the .eh_frame ranges (dl/build/reth/arith.s). memcpy, memset, memmove and bcmp are reached
through GOT slots and modelled in Python; abort and the panic paths stop the run.

Handler ABI, read from the ADD handlers of both families: rdi = (pc << 11) | stack length, rsi = stack base
(32-byte little-endian words, bottom first), rdx = gas left, rcx = interpreter context; the status byte is at
context+0x147 (0 = continue); the return value in rax packs the new pc and stack length the same way, rdx the
gas left. The binary is read as data only; its disassembly text is interpreted.
usage: python3 -I rarith.py <set> <out.json> [fault] [shard nshard]
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'emu'))
from x86emu2 import CPU2, rewrite_rip
from x86emu import Prog, Stop, M64
import goshim as G

W = os.path.dirname(HERE)
BIN = os.path.join(W, 'dl/reth/reth')
SET, OUT = sys.argv[1], sys.argv[2]
FAULT = sys.argv[3] if len(sys.argv) > 3 else 'none'
SHARD, NSHARD = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
M = G.M
rel = {}
for l in open(os.path.join(W, 'dl/build/reth/relative.txt')):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
TABLES = {'X': 0x7f35dd0, 'Y': 0x7f3d5d0}
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
HANDLER = {(f, op): rel[t + 8 * c] for f, t in TABLES.items() for op, c in OPS.items()}
UNDEF = {'X': 0x29c9510, 'Y': 0x29cf1e0}  # the handler of undefined opcodes in each family (most frequent entry)
# every fork table of a family gives the same handler for these opcodes, or the undefined handler before the fork that
# introduced the opcode (checked at start)
for f, rng in (('X', range(0x7f2fdd0, 0x7f35dd1, 0x800)), ('Y', range(0x7f375d0, 0x7f3d5d1, 0x800))):
    for t in rng:
        for op, c in OPS.items():
            assert rel[t + 8 * c] in (HANDLER[(f, op)], UNDEF[f]), (hex(t), op, hex(rel[t + 8 * c]))

text = open(os.path.join(W, 'dl/build/reth/arith.s')).read()
FAULTS = json.load(open(os.path.join(HERE, 'rfaults.json'))) if os.path.exists(os.path.join(HERE, 'rfaults.json')) else {}
PATCH = None
if FAULT != 'none':
    addr, old, new, ops = FAULTS[FAULT]
    lines = text.split('\n'); hit = [i for i, l in enumerate(lines) if re.match(r'^\s*%s:' % addr[2:], l)]
    if len(hit) != 1 or old not in lines[hit[0]]:
        raise SystemExit('fault %s did not match' % FAULT)
    PATCH = {'addr': addr, 'line': lines[hit[0]].strip(), 'old': old, 'new': new}
    lines[hit[0]] = lines[hit[0]].replace(old, new, 1); text = '\n'.join(lines)
prog = Prog(rewrite_rip(text))
fb = open(BIN, 'rb').read()
img = G.Image(BIN)
STACK, CTX, PARAMS, HEAP = 0x30000000, 0x32000000, 0x33000000, 0x34000000
GUARD = G.GUARD


def lanes(v, w, n): return [(v >> (w * i)) & ((1 << w) - 1) for i in range(n)]
def pack(ls, w): return sum((x & ((1 << w) - 1)) << (w * i) for i, x in enumerate(ls))


class RCPU(CPU2):
    def read(self, a, n):
        a &= M64
        for lo, hi in ((STACK, STACK + 0x10000), (CTX, CTX + 0x10000), (PARAMS, PARAMS + 0x10000), (HEAP, HEAP + 0x100000),
                       (0x7fff00000000, 0x7ffff0001000), (self.fs - 0x1000, self.fs + 0x1000)):
            if lo <= a and a + n <= hi:
                return super().read(a, n)
        v = img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        return v

    def write(self, a, n, v):
        a &= M64
        for lo, hi in ((STACK, STACK + 0x10000), (CTX, CTX + 0x10000), (PARAMS, PARAMS + 0x10000), (HEAP, HEAP + 0x100000),
                       (0x7fff00000000, 0x7ffff0001000), (self.fs - 0x1000, self.fs + 0x1000)):
            if lo <= a and a + n <= hi:
                return super().write(a, n, v)
        raise Stop('write %d at %x outside memory' % (n, a))

    def _target(self, s):
        if re.match(r'^(0x)?[0-9a-f]+$', s):
            return int(s, 16)
        m = re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', s)
        if m and int(m.group(1), 16) in self.got:
            return ('got', int(m.group(1), 16))
        return self.get(self.opnd(s))

    def i_call(self, o, pc, n):
        t = self._target(o[0])
        if isinstance(t, tuple):
            self.got[t[1]](self); return n
        if t in self.externs:
            self.externs[t](self); return n
        self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t

    def i_jmp(self, o, pc, n):
        t = self._target(o[0])
        if isinstance(t, tuple):
            self.got[t[1]](self); a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        return t

    # AVX and bit instructions on these paths that the base model lacks
    def i_vinsertf128(self, o, pc, n): return self.i_vinserti128(o, pc, n)
    def i_vxorps(self, o, pc, n): return self.i_vpxor(o, pc, n)
    def i_vorps(self, o, pc, n): return self.i_vpor(o, pc, n)
    def i_vandps(self, o, pc, n): return self.i_vpand(o, pc, n)

    def _vw(self, o):
        return self.opnd(o[0])[2]

    def _v3(self, o, w, fn):
        d = self.opnd(o[0]); b = d[2]
        a = self.get(self.opnd(o[1]), b); c = self.get(self.opnd(o[2]), b)
        self.put(d, pack([fn(x, y) for x, y in zip(lanes(a, w, b // w), lanes(c, w, b // w))], w))

    def i_vpaddq(self, o, pc, n): self._v3(o, 64, lambda x, y: x + y)
    def i_vpcmpeqd(self, o, pc, n): self._v3(o, 32, lambda x, y: 0xffffffff if x == y else 0)
    def i_vpcmpeqq(self, o, pc, n): self._v3(o, 64, lambda x, y: M64 if x == y else 0)

    def i_vpcmpgtq(self, o, pc, n):
        sg = lambda v: v - (1 << 64) if v >> 63 else v
        self._v3(o, 64, lambda x, y: M64 if sg(x) > sg(y) else 0)

    def i_vpunpcklqdq(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        a = lanes(self.get(self.opnd(o[1]), b), 64, b // 64); c = lanes(self.get(self.opnd(o[2]), b), 64, b // 64)
        out = []
        for k in range(b // 128):
            out += [a[2 * k], c[2 * k]]
        self.put(d, pack(out, 64))

    def i_vpblendd(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        a = lanes(self.get(self.opnd(o[1]), b), 32, b // 32); c = lanes(self.get(self.opnd(o[2]), b), 32, b // 32); k = int(o[3], 0)
        self.put(d, pack([c[i] if (k >> i) & 1 else a[i] for i in range(b // 32)], 32))

    def i_vpbroadcastq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = self.read(s[1], 8) if s[0] == 'm' else self.get(s) & M64
        self.put(d, pack([v] * (d[2] // 64), 64))

    def i_vmovmskpd(self, o, pc, n):
        s = self.opnd(o[1]); b = s[2]; v = self.get(s)
        self.put(self.opnd(o[0]), sum(((x >> 63) & 1) << i for i, x in enumerate(lanes(v, 64, b // 64))))

    def i_popcnt(self, o, pc, n):
        d = self.opnd(o[0]); v = self.get(self.opnd(o[1]), d[2]); c = bin(v).count('1')
        self.zf = int(v == 0); self.cf = self.of = self.sf = 0; self.put(d, c)

    def i_rol(self, o, pc, n): self._rot(o, True)
    def i_ror(self, o, pc, n): self._rot(o, False)

    def _rot(self, o, left):
        d = self.opnd(o[0]); w = d[2]
        k = self.get(self.opnd(o[1])) % w if len(o) > 1 else 1
        v = self.get(d)
        if k:
            v = ((v << k) | (v >> (w - k))) & ((1 << w) - 1) if left else ((v >> k) | (v << (w - k))) & ((1 << w) - 1)
        self.put(d, v)


def ext_memcpy(cpu):
    d, s_, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    data = [cpu.read(s_ + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.write(d + i, 1, v)
    cpu.r['rax'] = d


def ext_memset(cpu):
    d, v, n = cpu.r['rdi'], cpu.r['rsi'] & 0xff, cpu.r['rdx']
    for i in range(n):
        cpu.write(d + i, 1, v)
    cpu.r['rax'] = d


def ext_bcmp(cpu):
    a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    r = 0
    for i in range(n):
        x, y = cpu.read(a + i, 1), cpu.read(b + i, 1)
        if x != y:
            r = (x - y) & 0xffffffff; break
    cpu.r['rax'] = r


def stop(cpu): raise Stop('abort or panic reached')


GOT = {0x81481b8: ext_memcpy, 0x8148218: ext_memset, 0x8148288: ext_memcpy, 0x8148210: ext_bcmp, 0x8148208: ext_bcmp,
       0x8148588: stop, 0x81492d8: stop}
visited = set()


def run(fam, op, a, b, c):
    k = ARITY.get(op, 2)
    words = [a, b, c][:k]
    cpu = RCPU(prog, fb, 0, got=GOT, faults={})
    stack = [GUARD, GUARD] + list(reversed(words))
    for i, w in enumerate(stack):
        cpu.write(STACK + 32 * i, 32, w)
    for i in range(len(stack), 8):
        cpu.write(STACK + 32 * i, 32, GUARD)
    for i in range(0, 0x400, 8):
        cpu.write(CTX + i, 8, 0)
    cpu.write(CTX + 0x147, 1, 0)
    pc0 = 0x123
    gas0 = 1 << 40
    r = cpu.call(HANDLER[(fam, op)], [(pc0 << 11) | len(stack), STACK, gas0, CTX], maxsteps=5_000_000)
    visited.update(cpu.visited)
    st = cpu.read(CTX + 0x147, 1)
    if st:
        raise Stop('status byte %#x' % st)
    newlen = r & 0x7ff
    if newlen != len(stack) - k + 1:
        raise Stop('stack length %d' % newlen)
    if (r >> 11) != pc0 + 1:
        raise Stop('pc %#x' % (r >> 11))
    for i in list(range(2)) + list(range(len(stack), 8)):
        if cpu.read(STACK + 32 * i, 32) != GUARD:
            raise Stop('guard word %d changed' % i)
    return cpu.read(STACK + 32 * (newlen - 1), 32), cpu.steps, gas0 - cpu.r['rdx']


def ref(op, a, b, c):
    if op == 'AND': return a & b
    if op == 'OR': return a | b
    if op == 'XOR': return a ^ b
    if op == 'NOT': return a ^ M
    return G.ref(op, a, b, c)


# vector sets: those of drive.py (exec of its generator part)
src = open(os.path.join(HERE, 'drive.py')).read(); src = src[:src.index('fspec = F.get')]
saved = sys.argv; sys.argv = ['drive.py', 'geth-amd64', SET, '0', '1', '/dev/null']
g = {'__name__': 'gen', '__file__': os.path.join(HERE, 'drive.py')}
exec(compile(src, 'drive.py', 'exec'), g)
sys.argv = saved
FAMS = os.environ.get('FAMS', 'X,Y').split(',')
ONLY = set(FAULTS[FAULT][3]) if FAULT != 'none' else None
res = {'target': 'reth v2.11.0 x86_64', 'set': SET, 'seed': g['SEEDS'].get(SET), 'fault': FAULT, 'patch': PATCH, 'families': FAMS,
       'shard': SHARD, 'nshard': NSHARD, 'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0, 'byOp': {}, 'records': []}
t0 = time.time()
for k, (tag, op, a, b, c) in enumerate(g['GEN'][SET]()):
    if k % NSHARD != SHARD or op not in OPS or (ONLY and op not in ONLY):
        continue
    want = ref(op, a, b, c)
    for fam in FAMS:
        key = fam + ':' + op
        st = res['byOp'].setdefault(key, [0, 0, 0]); st[0] += 1; res['cases'] += 1
        try:
            got, steps, gas = run(fam, op, a, b, c)
            res['steps'] += steps
        except Exception as e:
            st[2] += 1; res['errors'] += 1
            res['records'].append({'index': k, 'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': '%s: %s' % (type(e).__name__, e)})
            continue
        if got != want:
            st[1] += 1; res['mismatches'] += 1
            res['records'].append({'index': k, 'tag': tag, 'family': fam, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'model': hex(got), 'reference': hex(want)})
    if FAULT != 'none' and res['mismatches'] >= 20:
        break
res['seconds'] = time.time() - t0
res['visited'] = len(visited)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'steps', res['steps'], flush=True)
