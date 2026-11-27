"""Runs the shipped aarch64 jump destination analysis of tempo v1.19.1 in the a64emu model.

Routines lifted (addresses in tempo-v1.19.1-aarch64-unknown-linux-gnu, sha256 aa038545...):
  0x1d47980..0x1d47db8  evm2 bytecode/analysis/aarch64.rs analyze_neon (Neonx4 then Neon blocks)
  0x1d477c0..0x1d47980  the lazy jump table builder that calls it, with the inlined
                        analyze_scalar tail loop (0x1d478ec..0x1d47954)
The model starts at 0x1d47890 (right after calloc of the table) and stops at 0x1d47958.

usage: python3 -I jd_a64.py <a64.dis dir> <file.bin> <out.json> [fault] [shard nshards]
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a64emu import Prog, Mem, CPU, Stop

BUILD = sys.argv[1]
BIN = sys.argv[2]
OUT = sys.argv[3]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SHARD, NSHARD = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (0, 1)

fb = open(BIN, 'rb').read()
prog = Prog([open(os.path.join(BUILD, 'a64_jd.s')).read(), open(os.path.join(BUILD, 'a64_legacy1.s')).read()])
ENTRY, STOP = 0x1d47890, 0x1d47958

faults = {}
if FAULT == 'pushx':
    # plant: the Neonx4 and Neon kernels use smax with 0x5f (PUSHX); change the first one to 0x5e
    def f(cpu, mn, ops):
        return ('movi', ['v1.16b', '#0x5e'])
    faults[0x1d47a58] = f
elif FAULT == 'scalar':
    # plant: scalar tail compares a signed byte with 0x5f; use 0x60 (drops PUSH1)
    def f(cpu, mn, ops):
        return ('cmp', ['w12', '#0x60'])
    faults[0x1d4793c] = f
elif FAULT == 'tbx':
    # plant: one composition step looks up the wrong register
    def f(cpu, mn, ops):
        return ('tbx', ['v14.16b', '{ v15.16b }', 'v1.16b'])
    faults[0x1d47b34] = f


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


def model(code):
    n = len(code)
    tl = (n + 7) // 8
    mem = Mem(fb, 0, 0x18742d8)
    CODE, TAB, STK = 0x10000000, 0x20000000, 0x7ff000000000
    if n:
        mem.add(CODE, n)[:] = code
    if tl:
        mem.add(TAB, tl)
    mem.add(STK - 0x10000, 0x20000)
    cpu = CPU(prog, mem, faults=faults)
    cpu.x[31] = STK
    cpu.x[0] = TAB if tl else 1
    cpu.x[19] = tl
    cpu.x[20] = n
    cpu.x[22] = CODE
    cpu.x[23] = 0
    cpu.call(ENTRY, [cpu.x[0]], ret=STOP)
    visited.update(cpu.visited)
    if not tl:
        return b''
    return bytes(mem.regions[1][2]) if n else b''


def cases():
    pm = bytes.fromhex(json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))['runtime'].removeprefix('0x'))
    yield 'poolmanager', pm
    rng = random.Random(28_0281)
    for cut in sorted(rng.sample(range(len(pm)), 300)) + list(range(0, 130)):
        yield 'pm-suffix-%d' % cut, pm[cut:cut + 600]
    for n in range(1, 33):
        for off in range(0, 130):
            for tail in (0, 1, 16, 33, 64):
                c = bytes([0x5b] * off + [0x5f + n] + [0x5b] * n + [0x5b] * tail)
                yield 'push-lanes', c
                d = bytes([0x00] * off + [0x5f + n] + [0x5b] * n + [0x5b] * tail)
                yield 'push-lanes0', d
                yield 'truncated', c[:off + 1 + n // 2]
    for len_ in range(0, 200):
        for fill in (0x5b, 0x60, 0x7f, 0x00, 0x5f, 0x80):
            yield 'uniform', bytes([fill] * len_)
    for i in range(6000):
        len_ = 16 + rng.randrange(400)
        mode = rng.randrange(4)
        c = bytearray()
        while len(c) < len_:
            x = rng.getrandbits(32)
            if mode == 0: b = x & 0xff
            elif mode == 1: b = 0x5b if x % 3 == 0 else 0x60 + (x >> 8) % 32
            elif mode == 2: b = 0x7f if x % 2 == 0 else 0x5b
            else: b = [0x5b, 0x60, 0x7f, 0x5f, 0x80, 0x00, 0xfe][x % 7]
            c.append(b)
        yield 'random', bytes(c)


res = {'fault': FAULT, 'seed': 280281, 'cases': 0, 'mismatches': 0, 'errors': 0, 'byTag': {}, 'records': []}
for k, (tag, code) in enumerate(cases()):
    if k % NSHARD != SHARD:
        continue
    t = tag.split('-')[0] if tag.startswith('pm-suffix') else tag
    st = res['byTag'].setdefault(t, [0, 0])
    st[0] += 1
    res['cases'] += 1
    try:
        got = model(code)
    except Stop as e:
        res['errors'] += 1
        if len(res['records']) < 50:
            res['records'].append({'tag': tag, 'code': code.hex(), 'error': str(e)})
        continue
    ref = reference(code)
    if got != ref:
        res['mismatches'] += 1
        st[1] += 1
        if len(res['records']) < 50:
            res['records'].append({'tag': tag, 'code': code.hex(), 'model': got.hex(), 'reference': ref.hex()})
allins = set(a for a in prog.ins if 0x1d47980 <= a < 0x1d47db8 or 0x1d47890 <= a < 0x1d47958)
res['coverage'] = {'instructions': len(allins), 'reached': len(allins & visited),
                   'unreached': sorted(hex(a) for a in allins - visited)}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, res['cases'], res['mismatches'], res['errors'], res['coverage']['reached'], '/', res['coverage']['instructions'])
