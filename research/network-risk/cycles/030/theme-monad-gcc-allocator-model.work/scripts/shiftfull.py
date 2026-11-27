"""Cycle 30, Task 3 with Task 1: whole Emitter::shl() 0x391590 (with shl<> 0x38f190), Emitter::shr() 0x38d1a0 and
Emitter::sar() 0x38a5d0 of the gcc 15.2.0 build, run in the x86 model on a virtual EVM stack whose two top elements
are both non-literal. This reaches the inlined shift_avx_reg_by_non_literal arms (value in an AVX register), the
stack-offset value path (mov_stack_offset_to_general_reg, then the general register arm), and the general register
arm, together with Stack::pop and Stack::push, the AVX and general register allocators, both spill paths,
destructive_mov_stack_elem_to_bounded_rax and discharge_deferred_comparison, all lifted from the package.
Only asmjit's _emitI (recorded), RoData::add4/add8/add32/add96 (recorded), operator new/delete, memcpy and the
libstdc++ red-black tree routines are stubs (allocdrv.py).
Checks per case: the pushed result equals pyevm.py, every element left on the virtual stack holds its own word in
every location the Stack records for it, rbx/rbp/rsp are restored, and the Stack bookkeeping is consistent.
usage: python3 -I shiftfull.py <outdir> <ncases> <nwords> [fault]"""
import sys, os, json, random, time, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import *
import allocdrv
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
OUT = sys.argv[1]; NC = int(sys.argv[2]); NW = int(sys.argv[3]); FAULT = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None
PERM = len(sys.argv) > 5 and sys.argv[5] == 'perm'
SEED = 3031
M = (1 << 256) - 1
OPC = {'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ENTRY = {'SHL': [0x391590, 0x38f190, 0x38e8c0, 0x372dc0, 0x39acd0], 'SHR': [0x38d1a0, 0x38c8d0, 0x374090, 0x39bf90],
         'SAR': [0x38a5d0, 0x389c90, 0x39e1d0]}
EXTRA = [0x389330, 0x3a7790, 0x36aa80, 0x3ad620, 0x3ad070, 0x3aaa40, 0x3ac590, 0x3ac620, 0x36c860, 0x36b280, 0x36bbe0,
         0x3694d0, 0x3977a0, 0x3977d0, 0x36b800, 0x36b650, 0x3ac3b0, 0x3ac400, 0x36ac20, 0x3ad190, 0x3abb50, 0x3abc30,
         0x3ab9e0]
FAULTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults.json')))
world = pyevm.World({0xaa: b''})
def evm1(op, a, x):
    code = b'\x7f' + x.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0); assert ok
    return int.from_bytes(ret, 'big')

EDGE = [0, 1, 2, 7, 8, 31, 32, 33, 63, 64, 65, 127, 128, 129, 191, 192, 193, 254, 255, 256, 257, 511, 1 << 32,
        (1 << 64) - 1, 1 << 64, (1 << 64) + 1, (1 << 64) + 64, 1 << 128, (1 << 128) + 5, 1 << 192, (1 << 192) + 255, 1 << 255, M]


def counts(rnd, n):
    out = list(EDGE)
    while len(out) < n:
        k = rnd.randrange(4)
        if k == 0: out.append(rnd.randrange(257))
        elif k == 1: out.append(rnd.getrandbits(256))
        elif k == 2: out.append((rnd.getrandbits(64) << (64 * rnd.randrange(1, 4))) | rnd.randrange(300))
        else: out.append(rnd.randrange(256, 1 << 20))
    return out


def values(rnd, n):
    out = [0, 1, M, 1 << 255, (1 << 255) - 1, (1 << 64) - 1, 1 << 64, 1 << 127, (1 << 192) | 1]
    while len(out) < n:
        x = rnd.getrandbits(256)
        if rnd.random() < 0.4: x |= 1 << 255
        out.append(x)
    return out


class Full(Model):
    def __init__(self, kind, faults):
        super().__init__(ENTRY[kind] + EXTRA, faults)
        self.c.externs.update({0x3810b0: self.add4, 0x373800: self.add96, 0x3ad360: self.nolit})
    def add4(self, c):
        x = c.r['rdx'] & 0xffffffff; self.rodconst.append(('add4', x)); self._rodata(c, x.to_bytes(4, 'little'), 4, 4)
    def add96(self, c): raise Stop('add96 reached (literal value path)')
    def nolit(self, c): raise Stop('alloc_literal reached')
    def set_stack(self, elems):
        """elems: list of block pointers from the bottom (index 0) to the top."""
        v = self.alloc(8 * 64)
        for i, b in enumerate(elems): self.c.write(v + 8 * i, 8, b)
        self.c.write(S + 0x158, 8, v); self.c.write(S + 0x160, 8, v + 8 * 64); self.c.write(S + 0x168, 8, v + 8 * 64)
        nv = self.alloc(8 * 8)
        self.c.write(S + 0x140, 8, nv); self.c.write(S + 0x148, 8, nv); self.c.write(S + 0x150, 8, nv)
        self.c.write(S + 8, 4, (len(elems) - 1) & 0xffffffff)
    def stack_elems(self):
        top = self.c.read(S + 8, 4); top = top - (1 << 32) if top >> 31 else top
        v = self.c.read(S + 0x158, 8)
        return [self.c.read(v + 8 * i, 8) for i in range(top + 1)]


AVXN = 16


def scenario(rnd):
    """Locations for value (second from top), shift (top) and up to five deeper elements."""
    gen_free = [0, 1, 2]; rnd.shuffle(gen_free)
    avx_free = list(range(AVXN)); rnd.shuffle(avx_free)
    pressure_avx = rnd.random() < 0.25
    pressure_gen = rnd.random() < 0.3
    def loc(allow):
        d = {}
        while not d:
            if 'gen' in allow and gen_free and rnd.random() < 0.45: d['gen'] = gen_free.pop()
            if 'avx' in allow and avx_free and rnd.random() < 0.45: d['avx'] = avx_free.pop()
            if 'stack' in allow and rnd.random() < 0.35: d['stack'] = None
        return d
    sc = {'value': loc(('gen', 'avx', 'stack')), 'same': rnd.random() < 0.08}
    sc['shift'] = None if sc['same'] else loc(('gen', 'avx', 'stack'))
    deep = []
    for _ in range(rnd.randrange(0, 6)):
        d = {}
        t = rnd.random()
        if t < 0.4 and gen_free: d['gen'] = gen_free.pop()
        elif t < 0.8 and avx_free: d['avx'] = avx_free.pop()
        if rnd.random() < 0.3 or not d: d['stack'] = None
        if rnd.random() < 0.15 and ('gen' in d or 'avx' in d): d['lit'] = rnd.getrandbits(256); d.pop('stack', None)
        deep.append(d)
    if pressure_gen:
        while gen_free: deep.append({'gen': gen_free.pop()})
    if pressure_avx:
        while avx_free: deep.append({'avx': avx_free.pop()})
    sc['deep'] = deep
    sc['dup_value'] = rnd.random() < 0.15     # the value element also sits deeper on the stack (a DUP)
    sc['dup_shift'] = (not sc['same']) and rnd.random() < 0.15   # the count element also sits deeper
    return sc


def build(kind, sc, rnd, fault):
    faults = {}
    if fault:
        for a, old, new in FAULTS[fault]: faults.setdefault(int(a, 16), []).append((old, new))
    m = Full(kind, faults)
    if fault == 'rodata-shared-label': m.rod_collide = True
    offs = iter(rnd.sample(range(0, 60), 50))
    layout = []                    # (dict, role) bottom to top
    for d in sc['deep']: layout.append((dict(d), 'deep'))
    n_deep = len(layout)
    if sc['dup_value']: layout.insert(rnd.randrange(0, n_deep + 1), ('VALUE', 'dupvalue'))
    layout.append(('VALUE', 'value'))
    if sc['same']: layout.append(('VALUE', 'shift'))
    else:
        sd = dict(sc['shift'])
        if sc['dup_shift']: layout.insert(rnd.randrange(0, len(layout)), (sd, 'dupshift'))
        layout.append((sd, 'shift'))
    vdict = dict(sc['value'])
    for d in [vdict] + [x for x, _ in layout if isinstance(x, dict)]:
        if 'stack' in d: d['stack'] = next(offs)
    # indices per element
    idx = {}
    order = []
    for i, (d, role) in enumerate(layout):
        key = 'VALUE' if d == 'VALUE' else id(d)
        idx.setdefault(key, []).append(i); order.append(key)
    blocks = {}; words = {}
    dicts = {'VALUE': vdict}
    for d, _ in layout:
        if isinstance(d, dict): dicts[id(d)] = d
    for key, ind in idx.items():
        d = dicts[key]
        blocks[key] = m.elem(len(ind), gen=d.get('gen'), avx=d.get('avx'), stack=d.get('stack'), lit=d.get('lit'), indices=ind)
    m.set_stack([blocks[k] for k in order])
    used = {d['stack'] for d in dicts.values() if 'stack' in d}
    avail = sorted(set(rnd.sample(range(-3, 64), rnd.randrange(4, 12))) - used) or [70]
    m.set_available(avail)
    m.set_free_general([r for r in range(3) if r not in {d.get('gen') for d in dicts.values()}])
    m.set_free_avx([r for r in range(AVXN) if r not in {d.get('avx') for d in dicts.values()}])
    m.c.write(S + 0xc, 4, rnd.randrange(-3, 3) & 0xffffffff)
    if PERM and rnd.random() < 0.5: m.permute_rows(rnd)
    return m, blocks, dicts, order


def main():
    rnd = random.Random(SEED + (sum(map(ord, FAULT)) if FAULT else 0))
    out = {'seed': SEED, 'fault': FAULT, 'cases': 0, 'runs': 0, 'stops': [], 'mismatches': [], 'nMismatchRuns': 0,
           'invariant': [], 'clobbers': [], 'nClobberRuns': 0, 'paths': {}}
    t0 = time.time()
    for n in range(NC):
        kind = ['SHL', 'SHR', 'SAR'][n % 3]
        sc = scenario(rnd)
        m, blocks, dicts, order = build(kind, sc, rnd, FAULT)
        tab0 = m.table_sigs(); allocdrv.TAB[:] = m.table()
        try:
            m.c.call(ENTRY[kind][0], [E], maxsteps=2000000)
        except Stop as e:
            out['stops'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'stop': str(e)}); continue
        if m.table_sigs() != tab0: out['invariant'].append({'case': n, 'bad': ['register table not restored']})
        st = m.stack_elems()
        if len(st) != len(order) - 1:
            out['invariant'].append({'case': n, 'bad': ['stack height %d, want %d' % (len(st), len(order) - 1)]}); continue
        rb = st[-1]
        bad = m.invariants(list(dict.fromkeys(st)))
        if bad: out['invariant'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'bad': bad})
        rl = m.loc(rb)
        arm = 'avx' if 'avx' in dicts['VALUE'] else ('gen' if 'gen' in dicts['VALUE'] else 'stack')
        spills = sum(1 for e in m.events if e[0] == 'rb_erase')
        path = '%s/value-%s/res-%s/spill%d/dupv%d/dups%d' % (kind, arm, '+'.join(k for k in ('gen', 'avx', 'stack') if k in rl), min(spills, 2), int(sc['dup_value']), int(sc['dup_shift']))
        out['paths'][path] = out['paths'].get(path, 0) + 1
        seq = m.emitted
        cs = counts(random.Random(SEED + n), NW); vs = values(random.Random(SEED + 7 * n), NW)
        post = {b: m.loc(b) for b in set(st)}
        for i in range(NW):
            cnt, val = cs[i], vs[i]
            if sc['same']: cnt = val
            w = {}
            for key, b in blocks.items():
                d = dicts[key]
                w[b] = val if key == 'VALUE' else d['lit'] if 'lit' in d else rnd.getrandbits(256)
            if not sc['same']:
                w[blocks[order[-1]]] = cnt
            init = [(w[blocks[k]], dicts[k]) for k in blocks]
            try: c = run_seq(m, seq, init, rnd)
            except Stop as e:
                out['mismatches'].append({'case': n, 'kind': kind, 'why': 'seq stop ' + str(e), 'seq': seqtext(seq)}); out['nMismatchRuns'] += 1; break
            out['runs'] += 1
            exp = evm1(OPC[kind], cnt, val)
            ww = dict(w); ww[rb] = exp
            for b in set(st):
                d = {k: v for k, v in post[b].items() if k in ('gen', 'avx', 'stack')}
                for where, got in word_at(c, d).items():
                    if got != ww[b]:
                        if b == rb:
                            out['nMismatchRuns'] += 1
                            if len(out['mismatches']) < 100:
                                out['mismatches'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'where': where, 'count': hex(cnt), 'value': hex(val), 'got': hex(got), 'want': hex(exp), 'seq': seqtext(seq)})
                        else:
                            out['nClobberRuns'] += 1
                            if len(out['clobbers']) < 100:
                                out['clobbers'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'where': where, 'loc': repr(post[b]), 'got': hex(got), 'want': hex(ww[b]), 'seq': seqtext(seq)})
        out['cases'] += 1
    cov = {}
    for f in sorted(set(sum(ENTRY.values(), [])) | set(EXTRA) | set(LIFT)):
        try: txt = load_fn(f)
        except FileNotFoundError: continue
        addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        cov['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    out['instructionCoverage'] = cov
    out['seconds'] = round(time.time() - t0, 1)
    name = 'shiftfull%s%s.json' % ('-' + FAULT if FAULT else '', '-perm' if PERM else '')
    json.dump(out, open(os.path.join(OUT, name), 'w'), indent=0)
    print(name, 'cases', out['cases'], 'runs', out['runs'], 'stops', len(out['stops']), 'mismatchRuns', out['nMismatchRuns'],
          'clobberRuns', out['nClobberRuns'], 'invariant', len(out['invariant']), out['seconds'], 's')
    import collections
    print(collections.Counter(s['stop'][:60] for s in out['stops']).most_common(8))
    for x in (out['mismatches'] + out['clobbers'] + out['invariant'])[:3]: print(str(x)[:1500])
main()
