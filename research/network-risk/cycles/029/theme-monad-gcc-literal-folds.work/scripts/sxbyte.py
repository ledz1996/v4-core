"""Cycle 29, Tasks 2 and 3 for SIGNEXTEND and BYTE. Runs Emitter::signextend() 0x388440 (with
signextend_avx_reg_by_int8 0x37ba80; signextend_by_literal_ix and signextend_general_reg_or_stack_offset_by_int8 are
inlined) and Emitter::byte() 0x37f1f0 (with byte_literal_ix_stack_offset_src 0x370830, byte_literal_ix_avx_reg_src
0x37ea20 and test_high_bits192 0x39dcb0; byte_literal_ix_general_reg_src and byte_non_literal_ix_literal_or_stack_offset_src
are inlined) of monad 0.16.7 in the x86 model with stubs, for literal indexes in every source location, for the
PoolManager's literal BYTE tables indexed by a run-time value in every index location, and for the compile-time fold
of two literals. Emitted sequences are rebuilt and run on operand words and compared with pyevm.py.
usage: python3 -I sxbyte.py <outdir> [operands-per-case] [fault]"""
import sys, os, re, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emdrv import *
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
OUT = sys.argv[1]; NOP = int(sys.argv[2]) if len(sys.argv) > 2 else 600; FAULT = sys.argv[3] if len(sys.argv) > 3 else None
M = (1 << 256) - 1; SEED = 2931
SX = ([0x388440, 0x37ba80], 0x388440)
BY = ([0x37f1f0, 0x370830, 0x37ea20, 0x39dcb0], 0x37f1f0)
FAULTS = {  # one instruction each, as text replacements in the objdump text
    'sx-limb': (0x388440, ('3889df:\tshr    rax,0x3', '3889df:\tshr    rax,0x4')),       # sign limb index ix/8 becomes ix/16
    'sx-fill': (0x388440, ('388d1e:\tcall   63c6e0', '388d1e:\tnop')),                    # 'sar dst_ones, 63' not emitted
    'sx-avx': (0x37ba80, ('37bb03:\tmov    edx,0x1f', '37bb03:\tmov    edx,0x1e')),       # shuffle mask fill one byte short
    'by-off': (0x37f1f0, ('37fad4:\tmov    ebx,0x1f', '37fad4:\tmov    ebx,0x1e')),       # byte index 31 - i off by one
    'byv-hi': (0x37f1f0, ('3801be:\tmov    esi,0x68', '3801be:\tmov    esi,0x6e')),       # cmovnz after test_high_bits192 becomes cmovz
}
world = pyevm.World({0xaa: b''})
def evm1(op, a, x):
    code = b'\x7f' + x.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0); assert ok
    return int.from_bytes(ret, 'big')
def words(rnd, n):
    base = [0, 1, M, 1 << 255, (1 << 255) - 1, 0x7f, 0x80, 0xff, 0x7fff, 0x8000, 0xffff, 0x7fffff, 0x800000, 0xffffff,
            (-887272) & M, 887272, (1 << 127) - 1, 1 << 127, (1 << 128) - 1, (-(1 << 127)) & M]
    out = list(base)
    while len(out) < n:
        k = rnd.randrange(7)
        if k == 0: v = rnd.getrandbits(256)
        elif k == 1: v = rnd.getrandbits(256) | 1 << 255
        elif k == 2: b = rnd.randrange(256); v = rnd.getrandbits(b + 1) | (1 << b)
        elif k == 3: v = rnd.getrandbits(64) << 192
        elif k == 4: v = (-rnd.getrandbits(rnd.randrange(1, 129))) & M
        elif k == 5: v = rnd.getrandbits(8 * rnd.randrange(1, 33))
        else: v = M ^ rnd.getrandbits(rnd.randrange(1, 256))
        out.append(v)
    return out
def idxwords(rnd, n):
    out = list(range(0, 70)) + [255, 256, 1 << 64, (1 << 64) + 3, 1 << 128, (1 << 192) + 1, 1 << 255, M, 0xffffffff, 1 << 32, (1 << 63) + 2]
    while len(out) < n:
        k = rnd.randrange(3)
        out.append(rnd.randrange(64) if k == 0 else (rnd.getrandbits(256) if k == 1 else rnd.getrandbits(64) << (64 * rnd.randrange(1, 4)) | rnd.randrange(32)))
    return out
def mkdrv(spec, pol, fault):
    fns, entry = spec
    faults = {FAULTS[fault][0]: FAULTS[fault][1]} if fault and FAULTS[fault][0] in fns else {}
    d = Drv(fns, entry, pol, faults)
    nxt = [1]
    def alloc_avx(c):
        el = d.elem(avx=nxt[0]); nxt[0] += 1; d.events.append('alloc_avx_reg'); d._pair(c, el)
    d.c.externs[0x36aa80] = alloc_avx
    for a in fns: d.c.externs.pop(a, None)
    return d
def mk(d, loc):
    if loc[0] in ('reuse', 'new', 'gen'): return d.elem(gen=loc[1])
    if loc[0] == 'stack': return d.elem(stack=loc[1])
    if loc[0] == 'avx': return d.elem(avx=loc[1])
    return d.elem(lit=loc[1])
def result(d, v):
    r = d.pushed[-1]
    if isinstance(r, tuple): return ('literal', r[1]), None
    if r == v and not d.emitted: return ('identity',), None
    if r == 0xdead1000: return ('literal', d.lits[-1]), None
    if d.c.read(r + 0x57, 1): return ('seq',), ('gen', d.table()[d.c.read(r + 0x56, 1)])
    if d.c.read(r + 0x55, 1): return ('seq',), ('avx', d.c.read(r + 0x54, 1))
    raise Stop('result location')
def pol(loc):
    if loc[0] == 'reuse': return {'reuse': True}
    if loc[0] == 'new': return {'dst': loc[2]}
    return {'dst': 0}
def load(c, loc, x):
    L = [(x >> (64 * i)) & M64 for i in range(4)]
    if loc[0] in ('reuse', 'new', 'gen'):
        for i in range(4): c.r[GPQREGS[loc[1]][i]] = L[i]
    elif loc[0] == 'stack':
        for i in range(4): c.write(c.r['rbp'] + 32 * loc[1] + 8 * i, 8, L[i])
    elif loc[0] == 'avx': c.y[loc[1]] = x
def runseq(d, text, inputs, where, rnd):
    if text not in SCACHE: SCACHE[text] = Prog(text)
    c = C(SCACHE[text])
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in d.rodmem.items(): c.write(ROD + a, 1, b)
    c.r['rbp'] = 0x7fff00000000; c.r['rbx'] = 0x7ffe00000000
    for loc, x in inputs: load(c, loc, x)
    c.call(0x1000, [])
    if where[0] == 'avx': return c.y[where[1]]
    return sum(c.r[where[1][i]] << (64 * i) for i in range(4))
def main():
    res = {'seed': SEED, 'fault': FAULT, 'cases': [], 'mismatches': [], 'decisionMismatches': []}
    rnd = random.Random(SEED); t0 = time.time(); nrun = 0
    srclocs = [('reuse', 0), ('reuse', 1), ('reuse', 2), ('new', 1, 0), ('new', 2, 1), ('new', 0, 2), ('stack', 0), ('stack', 6), ('avx', 0), ('avx', 9)]
    bigix = [32, 33, 255, 256, 1 << 64, (1 << 64) + 1, 1 << 128, 1 << 255, M]
    def emit_case(tag, d, dec, where, inputs_fn, op, ref_args, nops, extra):
        nonlocal nrun
        try: emitted = [[m, [optext(o) for o in ops]] for m, ops in d.emitted]
        except Stop as e:
            res['mismatches'].append(dict(extra, stop=str(e))); return
        case = dict(extra, decision=dec[0], events=[e if isinstance(e, str) else repr(e) for e in d.events], emitted=emitted, result=where)
        if dec[0] == 'seq':
            text = seqtext(d.emitted); bad = 0
            for xs in inputs_fn(nops):
                try: got = runseq(d, text, xs[0], where, rnd)
                except Stop as e: got = 'stop: %s' % e
                exp = evm1(op, *xs[1]); nrun += 1
                if got != exp:
                    bad += 1; res['mismatches'].append(dict(extra, input=[hex(v) for v in xs[1]], got=got if isinstance(got, str) else hex(got), want=hex(exp), seq=emitted))
            case['operands'] = nops; case['bad'] = bad
        res['cases'].append(case)
    # SIGNEXTEND with a literal index
    sxix = list(range(0, 32)) + bigix
    for ix in sxix:
        for loc in srclocs:
            d = mkdrv(SX, pol(loc), FAULT); s = d.elem(lit=ix); v = mk(d, loc); d.popq = [s, v]
            try: d.run([E]); dec, where = result(d, v)
            except Stop as e:
                res['decisionMismatches'].append({'op': 'SIGNEXTEND', 'ix': hex(ix), 'loc': loc, 'stop': str(e)}); continue
            want = 'identity' if ix >= 31 else 'seq'
            if dec[0] != want: res['decisionMismatches'].append({'op': 'SIGNEXTEND', 'ix': hex(ix), 'loc': loc, 'got': repr(dec), 'want': want})
            r2 = random.Random(SEED + ix % 9973 + 31 * len(res['cases']))
            emit_case('sx', d, dec, where, lambda n: [([(loc, x)], (ix, x)) for x in words(r2, n)], 0x0b, None, NOP,
                      {'op': 'SIGNEXTEND', 'ix': hex(ix), 'pmIndex': ix in (1, 2, 15), 'loc': loc})
            if dec[0] == 'identity':
                for x in words(random.Random(ix % 9973), 40):
                    nrun += 1
                    if evm1(0x0b, ix, x) != x: res['mismatches'].append({'op': 'SIGNEXTEND', 'ix': hex(ix), 'x': hex(x), 'decision': 'identity'})
    # BYTE with a literal index (no PoolManager site; limb and lane boundaries)
    for ix in list(range(0, 32)) + bigix:
        for loc in srclocs:
            d = mkdrv(BY, pol(loc), FAULT); s = d.elem(lit=ix); v = mk(d, loc); d.popq = [s, v]
            try: d.run([E]); dec, where = result(d, v)
            except Stop as e:
                res['decisionMismatches'].append({'op': 'BYTE', 'ix': hex(ix), 'loc': loc, 'stop': str(e)}); continue
            want = ('literal', 0) if ix >= 32 else ('seq',)
            if dec != want: res['decisionMismatches'].append({'op': 'BYTE', 'ix': hex(ix), 'loc': loc, 'got': repr(dec), 'want': repr(want)})
            r2 = random.Random(SEED + 7 + ix % 9973 + 31 * len(res['cases']))
            emit_case('by', d, dec, where, lambda n: [([(loc, x)], (ix, x)) for x in words(r2, n)], 0x1a, None, NOP // 2,
                      {'op': 'BYTE', 'ix': hex(ix), 'loc': loc})
    # BYTE of a literal value at a run-time index: the PoolManager's two tables and edge words
    sa = json.load(open('/home/user/v4-core/research/network-risk/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']
    tables = sorted({int(r['values'][1], 16) for r in sa if r['op'] == 'BYTE'})
    vals = tables + ([0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20, M, 1 << 255, 0xff] if not FAULT else [])
    for val in vals:
        for loc in [('gen', 0), ('gen', 1), ('gen', 2), ('stack', 0), ('stack', 4), ('avx', 0), ('avx', 7)]:
            for free in (False, True):
                # the destination register is never the one that holds the index (it is reserved by RegReserv)
                d = mkdrv(BY, {'dst': (loc[1] + 1) % 3 if loc[0] == 'gen' else 0}, FAULT)
                if free: d.c.write(E + 0x2e8, 8, 8)
                s = mk(d, loc); v = d.elem(lit=val); d.popq = [s, v]
                try: d.run([E]); dec, where = result(d, v)
                except Stop as e:
                    res['decisionMismatches'].append({'op': 'BYTE', 'value': hex(val), 'ixloc': loc, 'stop': str(e)}); continue
                if dec[0] != 'seq': res['decisionMismatches'].append({'op': 'BYTE', 'value': hex(val), 'ixloc': loc, 'got': repr(dec)})
                r2 = random.Random(SEED + 11 + 31 * len(res['cases']))
                emit_case('byv', d, dec, where, lambda n: [([(loc, i)], (i, val)) for i in idxwords(r2, n)], 0x1a, None, NOP,
                          {'op': 'BYTE', 'value': hex(val), 'pmTable': val in tables, 'ixloc': loc, 'free': free})
    # compile-time folds of two literals
    fold = {'cases': 0, 'mismatches': []}
    if not FAULT:
        fr = random.Random(SEED + 3)
        xs = words(fr, 60) + tables
        for spec, op, ixs in ((SX, 0x0b, list(range(0, 34)) + bigix), (BY, 0x1a, list(range(0, 34)) + bigix)):
            for ix in ixs:
                for x in xs:
                    d = mkdrv(spec, {'dst': 0}, None); s = d.elem(lit=ix); v = d.elem(lit=x); d.popq = [s, v]
                    d.run([E]); dec, _ = result(d, v); fold['cases'] += 1
                    exp = evm1(op, ix, x)
                    if dec != ('literal', exp): fold['mismatches'].append({'op': hex(op), 'ix': hex(ix), 'x': hex(x), 'got': repr(dec), 'want': hex(exp)})
    
    fnset = {}
    for a, t in PCACHE.items():
        pass
    reach = {}
    import glob
    for f in [0x388440, 0x37ba80, 0x37f1f0, 0x370830, 0x37ea20, 0x39dcb0]:
        txt = load_fn(f); addrs = [int(m, 16) for m in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        hit = sum(1 for a in addrs if a in x86emu.VISITED)
        reach['%x' % f] = [hit, len(addrs)]
    res['instructionCoverage'] = reach
    res['compileTimeFold'] = fold; res['runs'] = nrun; res['seconds'] = round(time.time() - t0, 1)
    name = 'sxbyte%s.json' % ('-' + FAULT if FAULT else '')
    json.dump(res, open(os.path.join(OUT, name), 'w'), indent=0)
    print(name, 'cases', len(res['cases']), 'runs', nrun, 'mismatches', len(res['mismatches']), 'decision', len(res['decisionMismatches']), 'fold', fold['cases'], len(fold['mismatches']), res['seconds'])
    for m in (res['decisionMismatches'] + res['mismatches'] + fold['mismatches'])[:6]: print(str(m)[:500])
main()
