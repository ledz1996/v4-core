"""Runs the shipped x86_64 jump destination analysis of tempo v1.19.1 in the x86 model, once per kernel.

Routines lifted (addresses in tempo-v1.19.1-x86_64-unknown-linux-gnu, sha256 77ea6e60...):
  0x1e29620  CPU dispatch (reads the std_detect feature cache word at 0x6cba970)
  0x1e29770  analyze_avx512vbmi, 0x1e29cf0 analyze_avx2, 0x1e29fa0 analyze_sse41
  0x1e294c0  the lazy jump table builder with the inlined analyze_scalar tail (0x1e295ad..0x1e295ff)
The feature word is set in the model to force each path; the model starts at 0x1e29586 (after calloc)
and stops at 0x1e29514.

usage: python3 -I jd_x64.py <build dir> <bin> <out.json> <kernel> [fault] [shard nshards]
  kernel: avx512 | avx2 | sse41 | none
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x86emu import Prog, Stop
from x86emu2 import rewrite_rip
from x86vec import VCPU

BUILD, BIN, OUT, KERNEL = sys.argv[1:5]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
SHARD, NSHARD = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, 1)
FEAT = {'avx512': (1 << 10) | (1 << 15) | (1 << 19) | (1 << 23) | (1 << 27), 'avx2': (1 << 10) | (1 << 15),
        'sse41': 1 << 10, 'none': 1 << 40}[KERNEL]
fb = open(BIN, 'rb').read()
text = open(os.path.join(BUILD, 'x64_jd.s')).read() + open(os.path.join(BUILD, 'x64_legacy_1e294c0.s')).read()
prog = Prog(rewrite_rip(text))
ENTRY, STOP = 0x1e29586, 0x1e29514
RANGES = {'avx512': (0x1e29770, 0x1e29cef), 'avx2': (0x1e29cf0, 0x1e29fa0), 'sse41': (0x1e29fa0, 0x1e2a67f),
          'none': (0x1e295ad, 0x1e29600)}

FAULTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jd_x64_faults.json')))
faults = {}
if FAULT != 'none':
    a, rep = FAULTS[FAULT]
    faults[int(a, 16)] = rep


def reference(code):
    t = bytearray((len(code) + 7) // 8)
    i = 0
    while i < len(code):
        b = code[i]
        if b == 0x5b:
            t[i // 8] |= 1 << (i % 8)
        i += 1 + (b - 0x5f if 0x60 <= b <= 0x7f else 0)
    return bytes(t)


visited = set()
CODE, TAB = 0x10000000, 0x20000000


def model(code):
    n = len(code); tl = (n + 7) // 8
    cpu = VCPU(prog, fb, 0x189aab8, faults=faults)
    for i, b in enumerate(code):
        cpu.mem[CODE + i] = b
    for i in range(tl):
        cpu.mem[TAB + i] = 0
    cpu.write(0x6cba970, 8, FEAT)
    cpu.r['r12'] = CODE; cpu.r['r14'] = n; cpu.r['rbx'] = tl
    cpu.r['rax'] = TAB if tl else 1
    cpu.call(ENTRY, [], ret_addr=STOP)
    visited.update(cpu.visited)
    # every byte the model touched must be inside the code or the table (no reads or writes past them)
    for a in cpu.mem:
        if CODE + n <= a < CODE + 0x1000000 or TAB + tl <= a < TAB + 0x1000000:
            raise Stop('touched %x outside the buffers' % a)
    return bytes(cpu.mem[TAB + i] for i in range(tl))


def cases():
    pm = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
    yield 'poolmanager', pm
    rng = random.Random(28_0282)
    for cut in sorted(rng.sample(range(len(pm)), 100)) + list(range(0, 130)):
        yield 'pm-suffix', pm[cut:cut + 600]
    for n in range(1, 33):
        for off in range(0, 130, 3):
            for tail in (0, 1, 16, 33, 64):
                c = bytes([0x5b] * off + [0x5f + n] + [0x5b] * n + [0x5b] * tail)
                yield 'push-lanes', c
                yield 'push-lanes0', bytes([0x00] * off + [0x5f + n] + [0x5b] * n + [0x5b] * tail)
                yield 'truncated', c[:off + 1 + n // 2]
    for len_ in range(0, 200, 3):
        for fill in (0x5b, 0x60, 0x7f, 0x00, 0x5f, 0x80):
            yield 'uniform', bytes([fill] * len_)
    for i in range(1500):
        len_ = 16 + rng.randrange(400); mode = rng.randrange(4); c = bytearray()
        while len(c) < len_:
            x = rng.getrandbits(32)
            if mode == 0: b = x & 0xff
            elif mode == 1: b = 0x5b if x % 3 == 0 else 0x60 + (x >> 8) % 32
            elif mode == 2: b = 0x7f if x % 2 == 0 else 0x5b
            else: b = [0x5b, 0x60, 0x7f, 0x5f, 0x80, 0x00, 0xfe][x % 7]
            c.append(b)
        yield 'random', bytes(c)


res = {'kernel': KERNEL, 'featureWord': hex(FEAT), 'fault': FAULT, 'seed': 280282, 'cases': 0, 'mismatches': 0,
       'errors': 0, 'byTag': {}, 'records': []}
for k, (tag, code) in enumerate(cases()):
    if k % NSHARD != SHARD:
        continue
    st = res['byTag'].setdefault(tag, [0, 0, 0]); st[0] += 1; res['cases'] += 1
    try:
        got = model(code)
    except Stop as e:
        st[2] += 1; res['errors'] += 1
        if len(res['records']) < 50:
            res['records'].append({'tag': tag, 'code': code.hex(), 'error': str(e)})
        continue
    ref = reference(code)
    if got != ref:
        st[1] += 1; res['mismatches'] += 1
        if len(res['records']) < 50:
            res['records'].append({'tag': tag, 'code': code.hex(), 'model': got.hex(), 'reference': ref.hex()})
lo, hi = RANGES[KERNEL]
allins = set(a for a in prog.ins if lo <= a < hi and prog.ins[a].split()[0] not in ('int3', 'nop', 'data16', 'cs'))
res['coverage'] = {'range': [hex(lo), hex(hi)], 'instructions': len(allins), 'reached': len(allins & visited),
                   'unreached': sorted(hex(a) for a in allins - visited)}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, res['cases'], res['mismatches'], res['errors'], res['coverage']['reached'], '/', res['coverage']['instructions'])
