"""Cycle 29, Tasks 2 and 3 for a literal shifted by a run-time count (shift_literal_by_non_literal, inlined into
Emitter::shl<>, Emitter::shr() and Emitter::sar() of monad 0.16.7) and for the compile-time fold of a shift whose
count and value are both literals. Entry points: shl() 0x391590 (which calls shl<> 0x38f190), shr() 0x38d1a0,
sar() 0x38a5d0; destructive_mov_stack_elem_to_bounded_rax 0x389330 / 0x3a7790 is run from its gcc code too.
RoData::add32/add4/add<8>/add96 are stubs that record the words the gcc code passes and place them where the emitted
loads find them. The emitted sequence is run in the x86 model and compared with pyevm.py.
usage: python3 -I litshift.py <outdir> [counts-per-case] [fault]"""
import sys, os, re, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emdrv import *
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
OUT = sys.argv[1]; NC = int(sys.argv[2]) if len(sys.argv) > 2 else 600; FAULT = sys.argv[3] if len(sys.argv) > 3 else None
M = (1 << 256) - 1; SEED = 2930
COMMON = [0x389330, 0x3a7790]
KIND = {'SHL': ([0x391590, 0x38f190, 0x372dc0, 0x39acd0] + COMMON, 0x391590, 0x1b),
        'SHR': ([0x38d1a0, 0x374090, 0x39bf90] + COMMON, 0x38d1a0, 0x1c),
        'SAR': ([0x38a5d0, 0x39e1d0] + COMMON, 0x38a5d0, 0x1d)}
FAULTS = {
    'shl-negdrop': (0x38f190, ('38f86d:\tcall   63c6a0', '38f86d:\tnop')),     # drop the emitted 'neg rax' of the SHL window load
}
world = pyevm.World({0xaa: b''})
def evm1(op, a, x):
    code = b'\x7f' + x.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0); assert ok
    return int.from_bytes(ret, 'big')
def counts(rnd, n):
    out = (list(range(0, 300)) if n >= 300 else list(range(0, 300, 7))) + [511, 512, 1 << 64, (1 << 64) + 3, (1 << 128) + 1, 1 << 192, (1 << 255) + 8, M, M - 255]
    while len(out) < n:
        k = rnd.randrange(4)
        if k == 0: out.append(rnd.getrandbits(256))
        elif k == 1: out.append(rnd.getrandbits(64) << (64 * rnd.randrange(1, 4)) | rnd.randrange(256))
        elif k == 2: out.append(rnd.randrange(256, 1 << 16))
        else: out.append(rnd.randrange(256))
    return out
def drive(kind, shloc, val, free, fault=None):
    fns, entry, op = KIND[kind]
    faults = {FAULTS[fault][0]: FAULTS[fault][1]} if fault and FAULTS[fault][0] in fns else {}
    d = Drv(fns, entry, {'dst': 0}, faults)
    nxt = [1]
    def alloc_avx(c):
        el = d.elem(avx=nxt[0]); nxt[0] += 1; d.events.append('alloc_avx_reg'); d._pair(c, el)
    d.c.externs[0x36aa80] = alloc_avx
    for a in fns: d.c.externs.pop(a, None)
    if free: d.c.write(E + 0x2e8, 8, 8)           # Stack::has_free_general_reg(): the free list is not empty
    if shloc[0] == 'gen': s = d.elem(gen=shloc[1])
    elif shloc[0] == 'avx': s = d.elem(avx=shloc[1])
    elif shloc[0] == 'stack': s = d.elem(stack=shloc[1])
    else: s = d.elem(lit=shloc[1])
    v = d.elem(lit=val)
    d.popq = [s, v]; d.run([E])
    r = d.pushed[-1]
    if r == v: return d, ('identity',), None
    if r == 0xdead1000: return d, ('literal', d.lits[-1]), None
    if d.c.read(r + 0x55, 1): return d, ('seq',), ('avx', d.c.read(r + 0x54, 1))
    if d.c.read(r + 0x57, 1): return d, ('seq',), ('gen', d.table()[d.c.read(r + 0x56, 1)])
    raise Stop('result location')
def runseq(d, text, shloc, where, cnt, rnd):
    if text not in SCACHE: SCACHE[text] = Prog(text)
    c = C(SCACHE[text])
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in d.rodmem.items(): c.write(ROD + a, 1, b)
    RBPV = 0x7fff00000000; c.r['rbp'] = RBPV; c.r['rbx'] = 0x7ffe00000000
    L = [(cnt >> (64 * i)) & M64 for i in range(4)]
    if shloc[0] == 'gen':
        for i in range(4): c.r[GPQREGS[shloc[1]][i]] = L[i]
    elif shloc[0] == 'stack':
        for i in range(4): c.write(RBPV + 32 * shloc[1] + 8 * i, 8, L[i])
    else: c.y[shloc[1]] = cnt
    rbx0 = c.r['rbx']; c.call(0x1000, [])
    if c.r['rbx'] != rbx0: raise Stop('reg_context not restored')
    if where[0] == 'avx': return c.y[where[1]]
    return sum(c.r[where[1][i]] << (64 * i) for i in range(4))
def main():
    sa = json.load(open('/home/user/v4-core/research/network-risk/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']
    pmv = {'SHL': set(), 'SHR': set(), 'SAR': set()}
    for r in sa:
        if 'literal_by_non' in r['arm']: pmv[r['op']].add(int(r['values'][1], 16))
    rnd = random.Random(SEED)
    extra = [0, 1, M, 1 << 255, (1 << 255) - 1, 0x8000000000000000, 1 << 64, (1 << 64) - 1, (1 << 192) | 0xff, rnd.getrandbits(256), rnd.getrandbits(256) | (1 << 255)]
    res = {'seed': SEED, 'fault': FAULT, 'pmShiftedLiterals': {k: [hex(x) for x in sorted(v)] for k, v in pmv.items()}, 'cases': [], 'mismatches': [], 'decisionMismatches': []}
    t0 = time.time(); nrun = 0
    locs = [('gen', 0), ('gen', 1), ('gen', 2), ('avx', 0), ('stack', 0), ('stack', 5)]
    for kind in ('SHL', 'SHR', 'SAR'):
        op = KIND[kind][2]
        vals = sorted(pmv[kind] | set(extra)) if not FAULT else sorted(pmv[kind] | {1 << 255})
        for val in vals:
            for shloc in locs:
                for free in (False, True):
                    try: d, dec, where = drive(kind, shloc, val, free, FAULT)
                    except Stop as e:
                        res['decisionMismatches'].append({'kind': kind, 'value': hex(val), 'shloc': shloc, 'free': free, 'stop': str(e)}); continue
                    want = 'identity' if (val == 0 or (kind == 'SAR' and val == M)) else 'seq'
                    if dec[0] != want: res['decisionMismatches'].append({'kind': kind, 'value': hex(val), 'shloc': shloc, 'free': free, 'got': repr(dec), 'want': want})
                    try: emitted = [[m, [optext(o) for o in ops]] for m, ops in d.emitted]
                    except Stop as e:
                        res['mismatches'].append({'kind': kind, 'value': hex(val), 'shloc': shloc, 'stop': str(e)}); continue
                    case = {'kind': kind, 'value': hex(val), 'pmValue': val in pmv[kind], 'shloc': shloc, 'freeGeneralReg': free, 'decision': dec[0],
                            'events': [e if isinstance(e, str) else repr(e) for e in d.events], 'emitted': emitted, 'result': where}
                    if d.add96:
                        w, line = d.add96[-1]
                        if kind == 'SHL': wantw = [7, 0, val]; wantl = 32
                        else:
                            fill = M if (kind == 'SAR' and val >> 255) else 0
                            wantw = [val, fill, (fill & ((1 << 128) - 1)) | (7 << 128)]; wantl = 0
                        case['add96'] = [hex(x) for x in w] + [line]
                        if w != wantw or line != wantl: res['decisionMismatches'].append({'kind': kind, 'value': hex(val), 'add96': case['add96'], 'want': [hex(x) for x in wantw] + [wantl]})
                    if dec[0] == 'seq':
                        text = seqtext(d.emitted); bad = 0
                        cs = counts(random.Random(SEED + len(res['cases'])), NC)
                        for cnt in cs:
                            try: got = runseq(d, text, shloc, where, cnt, rnd)
                            except Stop as e: got = 'stop: %s' % e
                            exp = evm1(op, cnt, val); nrun += 1
                            if got != exp:
                                bad += 1; res['mismatches'].append({'kind': kind, 'value': hex(val), 'shloc': shloc, 'free': free, 'count': hex(cnt), 'got': got if isinstance(got, str) else hex(got), 'want': hex(exp), 'seq': emitted})
                        case['counts'] = len(cs); case['bad'] = bad
                    res['cases'].append(case)
    # compile-time folds: count and value both literals (shl<> 0x38f1e2.., shr() and sar() literal arms)
    fold = {'cases': 0, 'mismatches': []}
    if not FAULT:
        fr = random.Random(SEED + 1)
        vs = sorted(set(extra) | pmv['SHL'] | pmv['SHR'] | {fr.getrandbits(256) for _ in range(20)} | {fr.getrandbits(256) | 1 << 255 for _ in range(20)})
        cs = list(range(0, 260)) + [300, 1 << 64, (1 << 64) + 1, 1 << 128, 1 << 255, M]
        for kind in ('SHL', 'SHR', 'SAR'):
            for val in vs:
                for cnt in cs:
                    d, dec, _ = drive(kind, ('lit', cnt), val, False)
                    exp = evm1(KIND[kind][2], cnt, val); fold['cases'] += 1
                    got = dec[1] if dec[0] == 'literal' else None
                    if got != exp: fold['mismatches'].append({'kind': kind, 'count': hex(cnt), 'value': hex(val), 'got': repr(dec), 'want': hex(exp)})
    reach = {}
    for f in [0x391590, 0x38f190, 0x38d1a0, 0x38a5d0, 0x389330, 0x3a7790]:
        txt = load_fn(f); addrs = [int(m, 16) for m in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        reach['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    res['instructionCoverage'] = reach
    res['compileTimeFold'] = fold
    res['runs'] = nrun; res['seconds'] = round(time.time() - t0, 1)
    name = 'litshift%s.json' % ('-' + FAULT if FAULT else '')
    json.dump(res, open(os.path.join(OUT, name), 'w'), indent=0)
    print(name, 'cases', len(res['cases']), 'runs', nrun, 'mismatches', len(res['mismatches']), 'decision', len(res['decisionMismatches']), 'fold', fold['cases'], len(fold['mismatches']), res['seconds'])
    for m in (res['decisionMismatches'] + res['mismatches'] + fold['mismatches'])[:6]: print(str(m)[:400])
main()
