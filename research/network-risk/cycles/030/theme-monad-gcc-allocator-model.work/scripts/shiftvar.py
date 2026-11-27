"""Cycle 30, Task 3 with Task 1: SHL, SHR and SAR of a register value by a run-time count, from the gcc code of
shift_general_reg_by_non_literal<0,1,2> (0x38e8c0, 0x38c8d0, 0x389c90) with the register allocator, spill path and
element release of the same build lifted (allocdrv.py). Each case is a Stack state: which of the three general
register rows hold the value, the count, other live stack elements or nothing, whether those are on the EVM stack,
whether they also have a stack offset, an AVX register or a literal, and which stack offsets are free.
The emitted sequence is then run on many operand sets and checked:
  - the result row equals pyevm.py for the opcode,
  - every element still live after the call holds its own word in every location the Stack now records for it
    (a destination or a spill that overwrote a live operand, a missing spill store or a wrong spill offset fails this),
  - rbx (reg_context), rbp and rsp are restored, and the Stack's bookkeeping is consistent.
usage: python3 -I shiftvar.py <outdir> <ncases> <nwords> [fault]"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import *
import allocdrv
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
OUT = sys.argv[1]; NC = int(sys.argv[2]); NW = int(sys.argv[3]); FAULT = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None
PERM = len(sys.argv) > 5 and sys.argv[5] == 'perm'
SEED = 3030
M = (1 << 256) - 1
OPC = {'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
world = pyevm.World({0xaa: b''})
def evm1(op, a, x):
    code = b'\x7f' + x.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0); assert ok
    return int.from_bytes(ret, 'big')

FAULTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults.json'))) if os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults.json')) else {}

EDGE = [0, 1, 2, 7, 8, 63, 64, 65, 127, 128, 129, 191, 192, 193, 254, 255, 256, 257, 511, 1 << 32, (1 << 64) - 1,
        1 << 64, (1 << 64) + 1, (1 << 64) + 64, 1 << 128, (1 << 128) + 5, 1 << 192, (1 << 192) + 255, 1 << 255, M]


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


def scenario(rnd):
    """A random but valid Stack state for one call."""
    sc = {}
    rows = [0, 1, 2]; rnd.shuffle(rows)
    vrow = rows[0]
    same = rnd.random() < 0.12
    shloc = 'same' if same else rnd.choice(['gen', 'gen', 'avx', 'stack', 'gen+stack', 'avx+stack'])
    used_rows = [vrow]
    sc['value'] = {'gen': vrow}
    if rnd.random() < 0.3: sc['value']['avx'] = 3
    if rnd.random() < 0.25: sc['value']['stack'] = None
    sc['value_onstack'] = rnd.random() < 0.3
    if not same:
        sh = {}
        if 'gen' in shloc: sh['gen'] = rows[1]; used_rows.append(rows[1])
        if 'avx' in shloc: sh['avx'] = 5
        if 'stack' in shloc: sh['stack'] = None
        sc['shift'] = sh; sc['shift_onstack'] = rnd.random() < 0.3
    sc['shloc'] = shloc
    others = []
    for r in rows:
        if r in used_rows: continue
        if rnd.random() < 0.6:
            o = {'gen': r}
            t = rnd.random()
            if t < 0.25: o['stack'] = None
            elif t < 0.4: o['avx'] = 7 + r
            elif t < 0.55: o['lit'] = rnd.getrandbits(256)
            others.append(o)
    sc['others'] = others
    if rnd.random() < 0.4:
        # register pressure: every row held, the value live on the EVM stack, others in a register only,
        # so the allocator must spill a register-only element to a stack offset
        sc['value_onstack'] = True
        if 'shift' in sc and 'gen' in sc['shift']: sc['shift_onstack'] = True
        sc['others'] = [{'gen': r} if rnd.random() < 0.8 else o for r, o in [(r, {'gen': r, 'stack': None}) for r in rows if r not in used_rows]]
    return sc


def build(kind, sc, rnd, fault):
    faults = {}
    if fault:
        for a, old, new in FAULTS[fault]: faults.setdefault(int(a, 16), []).append((old, new))
    m = Model([SHIFT[kind]], faults)
    if fault == 'rodata-shared-label': m.rod_collide = True
    # stack indices and offsets
    idx = iter(rnd.sample(range(-4, 24), 20)); offs = iter(rnd.sample(range(-4, 40), 30))
    def mk(d, onstack, extra_refs):
        d = dict(d)
        if 'stack' in d: d['stack'] = next(offs)
        ind = [next(idx)] if onstack else []
        b = m.elem(extra_refs + (1 if onstack else 0), gen=d.get('gen'), avx=d.get('avx'), stack=d.get('stack'), lit=d.get('lit'), indices=ind)
        return b, d
    live = []
    vb, vd = mk(sc['value'], sc['value_onstack'], 2 if sc['shloc'] == 'same' else 1)
    if sc['shloc'] == 'same': sb, sd = vb, vd
    else: sb, sd = mk(sc['shift'], sc['shift_onstack'], 1)
    ob = []
    for o in sc['others']:
        b, d = mk(o, True, 0); ob.append((b, d))
    usedoff = {d['stack'] for _, d in [(vb, vd), (sb, sd)] + ob if 'stack' in d}
    avail = sorted(set(rnd.sample(range(-4, 40), rnd.randrange(1, 6))) - usedoff) or [99]
    m.set_available(avail)
    held = {d['gen'] for _, d in [(vb, vd), (sb, sd)] + ob if 'gen' in d}
    m.set_free_general([r for r in range(3) if r not in held])
    m.set_free_avx([r for r in range(16) if r not in {d.get('avx') for _, d in [(vb, vd), (sb, sd)] + ob}])
    m.c.write(S + 0xc, 4, rnd.randrange(-3, 3) & 0xffffffff)
    if PERM and rnd.random() < 0.5: m.permute_rows(rnd)
    pv = m.alloc(8); ps = m.alloc(8); res = m.alloc(16)
    m.c.write(pv, 8, vb); m.c.write(ps, 8, sb)
    return m, (vb, vd), (sb, sd), ob, res, pv, ps, avail


def main():
    rnd = random.Random(SEED + (hash(FAULT) % 1000 if FAULT else 0))
    out = {'seed': SEED, 'fault': FAULT, 'cases': 0, 'runs': 0, 'stops': [], 'mismatches': [], 'invariant': [],
           'clobbers': [], 'byKind': {}, 'paths': {}}
    t0 = time.time()
    for n in range(NC):
        kind = ['SHL', 'SHR', 'SAR'][n % 3]
        sc = scenario(rnd)
        m, (vb, vd), (sb, sd), ob, res, pv, ps, avail = build(kind, sc, rnd, FAULT)
        tab0 = m.table_sigs()
        try:
            m.c.call(SHIFT[kind], [res, E, ps, pv], maxsteps=400000)
        except Stop as e:
            out['stops'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'stop': str(e)}); continue
        rb = m.c.read(res, 8)
        if m.table_sigs() != tab0: out['invariant'].append({'case': n, 'bad': ['register table not restored']})
        allocdrv.TAB[:] = m.table()
        post = {b: m.loc(b) for b in {vb, sb, rb} | {b for b, _ in ob}}
        liveafter = [b for b in post if post[b]['onstack'] > 0 and b != rb]
        bad = m.invariants(liveafter + [rb])
        if bad: out['invariant'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'bad': bad})
        rl = post[rb]
        path = '%s/%s/vstk%d/oth%d/free%d/spill%d' % (kind, sc['shloc'], sc['value_onstack'], len(ob), 3 - len({d['gen'] for _, d in [(vb, vd), (sb, sd)] + ob if 'gen' in d}),
                                                     int(any(e[0] == 'rb_erase' for e in m.events)))
        out['paths'][path] = out['paths'].get(path, 0) + 1
        if 'gen' not in rl:
            out['mismatches'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'why': 'result has no general register', 'post': repr(rl)}); continue
        seq = m.emitted
        cs = counts(random.Random(SEED + n), NW); vs = values(random.Random(SEED + 7 * n), NW)
        nbad = 0
        for i in range(NW):
            cnt, val = cs[i], vs[i]
            words = {vb: val, sb: cnt if sb != vb else val}
            if sb == vb: cnt = val
            for b, d in ob: words[b] = d['lit'] if 'lit' in d else rnd.getrandbits(256)
            init = [(val, vd)] + ([(cnt, sd)] if sb != vb else []) + [(words[b], d) for b, d in ob]
            try: c = run_seq(m, seq, init, rnd)
            except Stop as e:
                out['mismatches'].append({'case': n, 'kind': kind, 'why': 'seq stop ' + str(e)}); nbad += 1; break
            out['runs'] += 1
            exp = evm1(OPC[kind], cnt, val)
            got = word_at(c, {'gen': rl['gen']})['gen']
            if got != exp:
                nbad += 1
                if len(out['mismatches']) < 200:
                    out['mismatches'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'count': hex(cnt), 'value': hex(val), 'got': hex(got), 'want': hex(exp),
                                              'seq': [[mn, [optext(o) for o in ops]] for mn, ops in seq]})
            for b in liveafter:
                d = {k: v for k, v in post[b].items() if k in ('gen', 'avx', 'stack')}
                for where, w in word_at(c, d).items():
                    if w != words[b]:
                        nbad += 1
                        if len(out['clobbers']) < 200:
                            out['clobbers'].append({'case': n, 'kind': kind, 'sc': repr(sc), 'elem': 'value' if b == vb else 'shift' if b == sb else 'other',
                                                    'where': where, 'loc': repr(post[b]), 'got': hex(w), 'want': hex(words[b]),
                                                    'seq': [[mn, [optext(o) for o in ops]] for mn, ops in seq]})
        out['cases'] += 1
        out['byKind'][kind] = out['byKind'].get(kind, 0) + 1
    fns = [SHIFT[k] for k in SHIFT] + LIFT
    cov = {}
    for f in fns:
        txt = load_fn(f); addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        cov['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    out['instructionCoverage'] = cov
    out['seconds'] = round(time.time() - t0, 1)
    name = 'shiftvar%s%s.json' % ('-' + FAULT if FAULT else '', '-perm' if PERM else '')
    json.dump(out, open(os.path.join(OUT, name), 'w'), indent=0)
    print(name, 'cases', out['cases'], 'runs', out['runs'], 'stops', len(out['stops']), 'mismatch', len(out['mismatches']),
          'clobber', len(out['clobbers']), 'invariant', len(out['invariant']), out['seconds'], 's')
    for x in (out['stops'] + out['mismatches'] + out['clobbers'] + out['invariant'])[:5]: print(str(x)[:600])
main()
