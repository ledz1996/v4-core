"""Task 3: codeBitmapInternal and (*Contract).validJumpdest of Nitro b72783f in the models.

codeBitmapInternal(code, bits []byte) is called with Go slices (ptr, len, cap) in registers and a zeroed bitmap of
len(code)/8+1+4 bytes, as codeBitmap allocates it (core/vm/analysis_legacy.go of the fork, line 75 per pclntab).
The model bitmap is compared byte for byte with a Python reference of push data. validJumpdest(c, dest) is then
called for every offset of the code plus offsets past the end and words of 2^64 and more, with the Contract fields
the build reads (amd64 and arm64 alike: Code at +0x58/+0x60, analysis at +0x40/+0x48) and analysis set to the model
bitmap, so isCode takes its first branch. The map path of isCode (Load/Store through the jumpDests interface,
makeslice) is not run: it calls into the Go runtime.
Programs: the PoolManager runtime (research/network-risk/build/PoolManager.json), that runtime cut inside each of
its last PUSH instructions, small programs that end inside PUSH1..PUSH32, and 300 random programs (seed 30_1185_04).
Faults: 'opcode' patches the PUSH1 bound of codeBitmapInternal (0x60 -> 0x61); 'bit' flips one bitmap bit at one
JUMPDEST of the PoolManager that the build jumps to, after the model ran and before validJumpdest.
usage: python3 -I jd.py <arch> <out.json> [none|opcode|bit]
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goshim as G
import models
from models import X64, A64Mem, ACPU, AProg, XProg, rewrite_rip, Stop, SP_TOP, SP_LO
import x86emu, faults as F

W = os.path.dirname(HERE)
arch, OUT = sys.argv[1], sys.argv[2]
FAULT = sys.argv[3] if len(sys.argv) > 3 else 'none'
BIN = W + '/dl/%s/usr/local/bin/nitro' % arch
fns = G.fnlist(W + '/dl/build/all-%s.txt' % arch)
names = [G.VM + n for n in ('codeBitmapInternal', '(*Contract).validJumpdest', '(*Contract).isCode')]
text = G.disasm(BIN, arch, [fns[n] for n in names])
PATCH = {'amd64': (0x1264fa7, 'cmp    r9b,0x60', 'cmp    r9b,0x61')}
if FAULT == 'opcode':
    if arch == 'amd64':
        text = F.text_patcher([PATCH['amd64']])(text)
    else:
        a = None
        for l in text.splitlines():
            if 'cmp' in l and '#0x60' in l and int(l.split(':')[0], 16) < fns[names[0]][1]:
                a = int(l.split(':')[0], 16); old = l.split('\t', 1)[1].strip(); break
        if a is None:
            raise SystemExit('no PUSH1 bound found in arm64 codeBitmapInternal')
        text = F.text_patcher([(a, '#0x60', '#0x61')])(text)
        PATCH['arm64'] = (a, '#0x60', '#0x61')
img = G.Image(BIN)
stops = {fns[n][0]: n for n in G.STOPS if n in fns}
prog = XProg(rewrite_rip(text)) if arch == 'amd64' else AProg([text])

CODE, BITS, CONTRACT, DEST = 0x30000000, 0x31000000, 0x32000000, 0x32001000
EXTRA = [(CODE, CODE + 0x100000), (BITS, BITS + 0x10000), (CONTRACT, CONTRACT + 0x2000)]
models.OK_RANGES.extend(EXTRA)


def new_cpu():
    ext = {}
    for a, n in stops.items():
        def stop(cpu, n=n): raise Stop('call ' + n)
        ext[a] = stop
    if arch == 'amd64':
        cpu = X64(prog, img, ext, {})
        cpu.write(G.GSTRUCT + 0x10, 8, 0)
    else:
        mem = A64Mem(img)
        for lo, hi in models.OK_RANGES:
            mem.add(lo, hi - lo)
        cpu = ACPU(prog, mem, externs=ext)
    return cpu


def wr(cpu, a, n, v):
    (cpu.write if arch == 'amd64' else cpu.m.write)(a, n, v)


def rd(cpu, a, n):
    return cpu.read(a, n) if arch == 'amd64' else cpu.m.read(a, n)


def call(cpu, entry, args):
    if arch == 'amd64':
        for k, v in zip(['rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8'], args):
            cpu.r[k] = v
        cpu.r['r14'] = G.GSTRUCT; cpu.y[15] = 0
        cpu.call(entry, [], maxsteps=50_000_000)
        return [cpu.r[k] for k in ('rax', 'rbx', 'rcx')]
    cpu.x[31] = SP_TOP; cpu.x[28] = G.GSTRUCT; cpu.x[29] = 0
    cpu.call(entry, args, maxsteps=50_000_000)
    return cpu.x[0:3]


def ref_bitmap(code):
    bits = bytearray(len(code) // 8 + 1 + 4)
    pc = 0
    while pc < len(code):
        op = code[pc]; pc += 1
        if 0x60 <= op <= 0x7f:
            for i in range(op - 0x5f):
                p = pc + i
                bits[p // 8] |= 1 << (p % 8)
            pc += op - 0x5f
    return bytes(bits)


def ref_valid(code, bits, d):
    return d < len(code) and code[d] == 0x5b and not (bits[d // 8] >> (d % 8)) & 1


def run_program(code, check_all=True, flip=None):
    cpu = new_cpu()
    nb = len(code) // 8 + 1 + 4
    for i, b in enumerate(code):
        wr(cpu, CODE + i, 1, b)
    for i in range(nb):
        wr(cpu, BITS + i, 1, 0)
    r = call(cpu, fns[names[0]][0], [CODE, len(code), len(code), BITS, nb, nb])
    if r[0] != BITS or r[1] != nb:
        raise Stop('returned slice %s' % r)
    model = bytes(rd(cpu, BITS + i, 1) for i in range(nb))
    want = ref_bitmap(code)
    bm = [i for i in range(nb) if model[i] != want[i]]
    if flip is not None:
        wr(cpu, BITS + flip // 8, 1, model[flip // 8] ^ (1 << (flip % 8)))
    steps_bitmap = cpu.steps
    # Contract fields read by validJumpdest / isCode
    for off in range(0, 0x100, 8):
        wr(cpu, CONTRACT + off, 8, 0)
    wr(cpu, CONTRACT + 0x58, 8, CODE); wr(cpu, CONTRACT + 0x60, 8, len(code))
    wr(cpu, CONTRACT + 0x40, 8, BITS); wr(cpu, CONTRACT + 0x48, 8, nb); wr(cpu, CONTRACT + 0x50, 8, nb)
    dests = list(range(len(code) + 3)) if check_all else []
    dests += [1 << 64, (1 << 64) + 0x5b, 1 << 255, G.M, (1 << 63)]
    vm = []
    nvalid = 0
    bits_used = want if flip is None else None
    for d in dests:
        wr(cpu, DEST, 32, d)
        got = call(cpu, fns[names[1]][0], [CONTRACT, DEST])[0] & 1
        exp = int(d < (1 << 64) and ref_valid(code, want, d))
        nvalid += exp
        if got != exp:
            vm.append({'dest': d, 'model': got, 'reference': exp})
    return {'len': len(code), 'bitmapMismatchBytes': [(i, model[i], want[i]) for i in bm], 'validJumpdestMismatches': vm,
            'dests': len(dests), 'validDests': nvalid, 'stepsBitmap': steps_bitmap, 'steps': cpu.steps}


def programs():
    rt = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
    yield 'poolmanager', rt, True
    # cut the runtime inside each of its last 20 PUSH instructions
    pcs = []; pc = 0
    while pc < len(rt):
        op = rt[pc]
        if 0x60 <= op <= 0x7f:
            pcs.append((pc, op - 0x5f)); pc += op - 0x5f
        pc += 1
    for p, n in pcs[-20:]:
        for cut in sorted({p + 1, p + 1 + n // 2, p + n}):
            if cut < len(rt):
                yield 'poolmanager-cut-%d' % cut, rt[:cut], False
    for n in range(1, 33):
        for k in range(0, n):
            yield 'end-in-push%d-%d' % (n, k), bytes([0x5b, 0x60 + n - 1]) + bytes([0x5b] * k), True
            yield 'end-in-push%d-%d-x' % (n, k), bytes([0x5b] * 7 + [0x60 + n - 1]) + bytes([0x5b] * k), True
    rnd = random.Random(301185_04)
    for i in range(300):
        L = rnd.randrange(1, 400)
        yield 'random-%d' % i, bytes(rnd.choice([0x5b, 0x5b, 0x60, 0x7f, 0x61, 0x56, 0x57, rnd.randrange(256)]) for _ in range(L)), True


def jump_targets(rt):
    """PUSH constants directly followed by JUMP or JUMPI."""
    t = set(); pc = 0; prev = None
    while pc < len(rt):
        op = rt[pc]
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f; prev = int.from_bytes(rt[pc + 1:pc + 1 + n], 'big'); pc += n + 1; continue
        if op in (0x56, 0x57) and prev is not None:
            t.add(prev)
        prev = None; pc += 1
    return t


res = {'arch': arch, 'fault': FAULT, 'patch': PATCH.get(arch) if FAULT == 'opcode' else None, 'programs': 0,
       'bitmapMismatchPrograms': 0, 'validMismatchPrograms': 0, 'dests': 0, 'records': [], 'started': time.time()}
rt = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
T = jump_targets(rt)
want_rt = ref_bitmap(rt)
validT = sorted(x for x in T if ref_valid(rt, want_rt, x))
res['poolmanager'] = {'len': len(rt), 'jumpdestBytes': sum(1 for b in rt if b == 0x5b),
                      'jumpdestOutsidePush': sum(1 for i in range(len(rt)) if ref_valid(rt, want_rt, i)),
                      'pushJumpTargets': len(T), 'pushJumpTargetsValid': len(validT)}
flip = validT[len(validT) // 2] if FAULT == 'bit' else None
res['flippedBit'] = flip
for name, code, full in programs():
    if FAULT != 'none' and name != 'poolmanager':
        continue
    try:
        r = run_program(code, full, flip if name == 'poolmanager' else None)
    except Stop as e:
        res['records'].append({'program': name, 'error': str(e)}); continue
    res['programs'] += 1; res['dests'] += r['dests']
    if name == 'poolmanager':
        res['poolmanager'].update({k: r[k] for k in ('dests', 'validDests', 'stepsBitmap', 'steps')})
        modelvalid = r['validDests'] - sum(x['reference'] for x in r['validJumpdestMismatches']) + sum(x['model'] for x in r['validJumpdestMismatches'])
        res['poolmanager']['modelValidDests'] = modelvalid
        res['poolmanager']['pushJumpTargetsModelInvalid'] = [x['dest'] for x in r['validJumpdestMismatches'] if x['dest'] in T]
    if r['bitmapMismatchBytes']:
        res['bitmapMismatchPrograms'] += 1
    if r['validJumpdestMismatches']:
        res['validMismatchPrograms'] += 1
    if r['bitmapMismatchBytes'] or r['validJumpdestMismatches']:
        res['records'].append({'program': name, 'code': code.hex() if len(code) < 2000 else 'poolmanager prefix %d' % len(code), **r})
res['seconds'] = time.time() - res.pop('started')
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, {k: res[k] for k in ('programs', 'bitmapMismatchPrograms', 'validMismatchPrograms', 'dests')}, res['poolmanager'], 'errors', sum(1 for x in res['records'] if 'error' in x))
