"""Cycle 38, Task 3 for erigon v3.8.2: the jump destination analysis of the released binary in the x86-64 model.
erigon keeps a bit per JUMPDEST byte outside push data (bitvec []uint64, bit pos%64 of word pos/64;
execution/vm/analysis.go). The kernel is chosen at start-up: codeBitmapSSE4 (the assembly routine jumpdestBitmapSSE4
for every 32-byte step, then markJumpdestsTail) when the CPU has SSSE3 and SSE4.1, codeBitmapGeneric otherwise
(analysis_amd64.go). Both are run from the binary through their Go entry points; codeBitmapSSE4 reads the table
sse4TabInit, a global computed at start-up, which the model writes at its symbol address from the formula in
analysis_amd64.go. validJumpdest(c, dest) is then run for every offset, past the end and for words of 2^64 and
more, with the Contract fields this build reads (Code at +0x28/+0x30, analysis at +0x10/+0x18/+0x20).
The analysed bitmap is cached by erigon in jumpDestCache keyed by the 32-byte code hash (contract.go
jumpdestAnalysis); a contract without a code hash is analysed per frame.
Programs: the PoolManager runtime, that runtime cut inside each of its last 40 PUSH instructions, programs that end
inside PUSH1..PUSH32 at every alignment to the 32-byte steps, every prefix length 0..130 of the runtime, and 400
random programs dense in 0x5b and PUSH bytes (seed 38_1128_04).
Faults: 'opcode' raises the PUSH1 bound of codeBitmapGeneric; 'bit' flips the bit of one JUMPDEST the build jumps
to, after the kernel ran and before validJumpdest; 'sse' changes the first pshufb of jumpdestBitmapSSE4 into pxor.
usage: python3 -I ejd.py <out.json> [none|opcode|bit|sse]
"""
import json, os, random, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'emu'))
import goshim as G, models, targets, faults as F
from gloop import LoopCPU, nobits
from x86emu2 import rewrite_rip, lanes, pack
from x86emu import Prog as XProg, Stop
import x86emu

OUT = sys.argv[1]; FAULT = sys.argv[2] if len(sys.argv) > 2 else 'none'
T = targets.get('erigon-amd64'); BIN = T['bin']
VMP = 'github.com/erigontech/erigon/execution/vm.'
fns = G.fnlist(T['fns'])
names = [VMP + n for n in ('codeBitmapSSE4', 'codeBitmapGeneric', 'markJumpdestsTail', 'jumpdestBitmapSSE4', '(*Contract).validJumpdest') if VMP + n in fns]  # markJumpdestsTail is inlined in this build
text = G.disasm(BIN, 'amd64', [fns[n] for n in names])
PATCH = None
if FAULT in ('opcode', 'sse'):
    lo, hi = fns[VMP + ('codeBitmapGeneric' if FAULT == 'opcode' else 'jumpdestBitmapSSE4')][:2]
    for l in text.splitlines():
        try:
            ad = int(l.split(':')[0], 16)
        except ValueError:
            continue
        if lo <= ad < hi and ((FAULT == 'opcode' and 'cmp' in l and '0x60' in l) or (FAULT == 'sse' and '\tpshufb' in l)):
            old, new = ('0x60', '0x61') if FAULT == 'opcode' else ('pshufb', 'pxor')
            text = F.text_patcher([(ad, old, new)])(text); PATCH = {'addr': hex(ad), 'line': l.strip(), 'old': old, 'new': new}
            break
    if PATCH is None:
        raise SystemExit('fault site not found')
prog = XProg(rewrite_rip(text))
img = G.Image(BIN)
bss = nobits(BIN)
sym = {}
for l in subprocess.run(['nm', BIN], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) == 3 and p[2] in (VMP + 'sse4TabInit',):
        sym[p[2]] = int(p[0], 16)
TAB = sym[VMP + 'sse4TabInit']


def tabinit():
    t = [0] * 384
    ta, pt, t0, t2 = 0, 48, 96, 144
    for i in range(8, 40):
        t[t0 + i] = 0x78 + i - 8; t[t2 + i] = 0x78 + i - 8
    for i in range(16, 40):
        t[ta + i] = 0x80 + i - 16
    for i in range(32, 40):
        t[pt + i] = 0x80 + i - 32
    return bytes(t)


class SSECPU(LoopCPU):
    def i_pshufb(self, o, pc, n):
        self._bin128(o, lambda a, b: pack([0 if (s & 0x80) else lanes(a, 8, 16)[s & 15] for s in lanes(b, 8, 16)], 8))

    def i_pmaxub(self, o, pc, n): self._lw(o, 8, lambda x, y: max(x, y))

    def i_pmaxsb(self, o, pc, n):
        sg = lambda v: v - 256 if v & 0x80 else v
        self._lw(o, 8, lambda x, y: (max(sg(x), sg(y))) & 0xff)


CODE, BITS, CONTRACT, DEST, HEAP = G.SCOPE, G.SCOPE + 0x80000, G.SCOPE + 0x90000, G.SCOPE + 0x91000, G.SCOPE + 0xa0000


def new_cpu():
    ext = {}
    for n in G.STOPS + ['runtime.gcWriteBarrier2']:
        if n in fns:
            ext[fns[n][0]] = (lambda cpu, n=n: (_ for _ in ()).throw(Stop('call ' + n)))
    st = {'heap': HEAP}

    def makeslice(cpu):
        size = img.read(cpu.r['rax'], 8) * cpu.r['rcx']
        p = st['heap']; st['heap'] += (size + 63) & ~63
        for i in range(0, size + 8, 8):
            cpu.write(p + i, 8, 0)
        cpu.r['rax'] = p
    ext[fns['runtime.makeslice'][0]] = makeslice
    cpu = SSECPU(prog, img, ext, {}, bss)
    cpu.write(G.GSTRUCT, 8, 0); cpu.write(G.GSTRUCT + 0x10, 8, 0); cpu.write(cpu.fs - 0x10, 8, G.GSTRUCT)
    tb = tabinit()
    for i in range(0, 384, 8):
        cpu.write(TAB + i, 8, int.from_bytes(tb[i:i + 8], 'little'))
    return cpu


def call(cpu, name, regs):
    for k, v in regs.items():
        cpu.r[k] = v
    cpu.r['r14'] = G.GSTRUCT; cpu.y[15] = 0
    x86emu.VISITED.clear()
    cpu.call(fns[VMP + name][0], [], maxsteps=50_000_000)
    if name.startswith('codeBitmap') and cpu.r['r14'] != G.GSTRUCT:
        raise Stop('g register not restored')


def ref_bits(code):
    words = [0] * ((len(code) + 63) // 64)
    pc = 0
    while pc < len(code):
        op = code[pc]
        if 0x60 <= op <= 0x7f:
            pc += op - 0x5e
            continue
        if op == 0x5b:
            words[pc // 64] |= 1 << (pc % 64)
        pc += 1
    return words


def kernel(code, name):
    cpu = new_cpu()
    for i in range(0, len(code), 8):
        cpu.write(CODE + i, 8, int.from_bytes(code[i:i + 8].ljust(8, b'\0'), 'little'))
    call(cpu, name, {'rax': CODE, 'rbx': len(code), 'rcx': len(code)})
    p, n = cpu.r['rax'], cpu.r['rbx']
    return [cpu.read(p + 8 * i, 8) for i in range(n)], cpu


def check_valid(cpu, code, words, flip=None):
    """validJumpdest for every offset, a few past the end and wide words; returns mismatching offsets."""
    if flip is not None:
        words = list(words); words[flip // 64] ^= 1 << (flip % 64)
    for i, w in enumerate(words):
        cpu.write(BITS + 8 * i, 8, w)
    for i in range(0, 0x40, 8):
        cpu.write(CONTRACT + i, 8, 0)
    cpu.write(CONTRACT + 0x28, 8, CODE); cpu.write(CONTRACT + 0x30, 8, len(code)); cpu.write(CONTRACT + 0x38, 8, len(code))
    cpu.write(CONTRACT + 0x10, 8, BITS); cpu.write(CONTRACT + 0x18, 8, len(words)); cpu.write(CONTRACT + 0x20, 8, len(words))
    ref = ref_bits(code)
    bad = []
    dests = list(range(len(code) + 3)) + [1 << 64, (1 << 64) + 0x5b, (1 << 255) | 0x10, (1 << 256) - 1]
    for d in dests:
        cpu.write(DEST, 32, d)
        call(cpu, '(*Contract).validJumpdest', {'rax': CONTRACT, 'rbx': DEST})
        got = cpu.r['rax'] & 0xff
        want = int(d < len(code) and (ref[d // 64] >> (d % 64)) & 1 == 1)
        if got != want:
            bad.append({'dest': hex(d), 'model': got, 'reference': want})
    return bad, len(dests)


pm = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
progs = [('pm-runtime', pm)]
pushes = []
pc = 0
while pc < len(pm):
    op = pm[pc]
    if 0x60 <= op <= 0x7f:
        pushes.append((pc, op - 0x5f)); pc += op - 0x5e
    else:
        pc += 1
for p, w in pushes[-40:]:
    progs.append(('pm-cut-%d' % p, pm[:p + 1 + w // 2]))
for w in range(1, 33):
    for align in (0, 5, 31, 32, 33, 63):
        progs.append(('end-in-push%d-at%d' % (w, align), b'\x5b' * align + bytes([0x5f + w]) + b'\x5b' * (w - 1)))
for n in list(range(0, 131)):
    progs.append(('pm-prefix-%d' % n, pm[:n]))
rnd = random.Random(381128_04)
for i in range(400):
    n = rnd.choice((31, 32, 33, 64, 95, 96, 97, 128, rnd.randrange(1, 700)))
    alphabet = [0x5b] * 6 + list(range(0x60, 0x80)) + [0x00, 0x56, 0x57, 0x5a, 0x5c, 0x5f, 0x80, 0xfe]
    progs.append(('random-%d' % i, bytes(rnd.choice(alphabet) for _ in range(n))))

res = {'target': 'erigon-amd64', 'fault': FAULT, 'patch': PATCH, 'seed': 381128_04, 'programs': 0, 'bitmapMismatch': [],
       'validMismatch': [], 'validCalls': 0, 'errors': [], 'pm': {}}
t0 = time.time()
fullcheck = {'pm-runtime'} | {n for n, c in progs if n.startswith(('pm-cut', 'end-in'))}
for name, code in progs:
    ref = ref_bits(code)
    for kern in ('codeBitmapSSE4', 'codeBitmapGeneric'):
        try:
            words, cpu = kernel(code, kern)
        except Exception as e:
            res['errors'].append({'program': name, 'kernel': kern, 'error': '%s: %s' % (type(e).__name__, e)}); continue
        res['programs'] += 1
        if words != ref:
            diff = [i for i in range(max(len(words), len(ref))) if (words[i:i + 1] or [None]) != (ref[i:i + 1] or [None])]
            res['bitmapMismatch'].append({'program': name, 'kernel': kern, 'len': len(code), 'words': diff[:20],
                                          'model': [hex(words[i]) if i < len(words) else None for i in diff[:5]],
                                          'reference': [hex(ref[i]) if i < len(ref) else None for i in diff[:5]]})
        if name == 'pm-runtime':
            res['pm'][kern] = {'jumpdestsMarked': sum(bin(w).count('1') for w in words),
                               'pushDataJumpdestBytes': sum(1 for i, b in enumerate(code) if b == 0x5b) - sum(bin(w).count('1') for w in ref)}
        if name in fullcheck or (FAULT == 'bit' and name == 'pm-runtime'):
            flip = None
            if FAULT == 'bit' and name == 'pm-runtime':
                flip = [i for i in range(len(code)) if (ref[i // 64] >> (i % 64)) & 1][300]
                res['flipped'] = flip
            try:
                bad, n = check_valid(cpu, code, words, flip)
            except Exception as e:
                res['errors'].append({'program': name, 'kernel': kern, 'stage': 'validJumpdest', 'error': '%s: %s' % (type(e).__name__, e)}); continue
            res['validCalls'] += n
            if bad:
                res['validMismatch'].append({'program': name, 'kernel': kern, 'count': len(bad), 'first': bad[:10]})
    if FAULT != 'none' and (res['bitmapMismatch'] or res['validMismatch']) and res['programs'] > 2:
        break
res['seconds'] = time.time() - t0
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, 'programs', res['programs'], 'bitmapMismatch', len(res['bitmapMismatch']), 'validCalls', res['validCalls'],
      'validMismatch', len(res['validMismatch']), 'errors', len(res['errors']), res['pm'], flush=True)
