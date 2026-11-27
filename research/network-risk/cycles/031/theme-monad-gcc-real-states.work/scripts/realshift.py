"""Cycle 31, Task 2 and 3 for the shift sites of the 128 un-entered value blocks. For each SHL/SHR/SAR site, the
virtual stack logged by the hooked clang harness (out/states.jsonl, Task 1) is laid out as the gcc 15.2.0 build of
monad 0.16.7 reads it (cycle 30 allocdrv.py / shiftfull.py Full model: elements, every location, stack indices,
reserve counts, negative and positive element vectors, top_index, min_delta, max_delta, available stack offsets,
free general and AVX register queues). The package's Emitter::shl()/shr()/sar() then runs in the x86 model with
every asmjit call recorded. The stream is compared with the clang listing body of the same pc
(cycles/027/theme-monad-engine-agreement.work/out/pm-asm-0.16.7.txt) up to consistent renaming (cycle 30 cmpclang.canon),
and run on NW operand sets; every element's words in every recorded location are compared with pyevm.py.
The register limb table of the gcc model is the default one; the clang listing's table can differ, which the
renaming absorbs. usage: python3 -I realshift.py <outdir> <nw> [fault]"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NW = int(sys.argv[2]); FAULT = sys.argv[3] if len(sys.argv) > 3 else None
C30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-monad-gcc-allocator-model.work/scripts'
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.argv = [os.path.join(C30, 'shiftfull.py'), OUTD, '0', '0', '-']
src = open(os.path.join(C30, 'shiftfull.py')).read().replace('\nmain()\n', '\n')
g = {'__file__': os.path.join(C30, 'shiftfull.py'), '__name__': 'sf'}
exec(compile(src, 'shiftfull.py', 'exec'), g)
csrc = open(os.path.join(C30, 'cmpclang.py')).read().split('\ndef main')[0]
csrc = 'import re\nALIAS = x86emu.ALIAS\n' + csrc[csrc.index("FIXED = "):]
cg = dict(g); cg['x86emu'] = g['x86emu']; exec(compile(csrc, 'cmpclang.py', 'exec'), cg); canon = cg['canon']
Full = g['Full']; S = g['S']; E = g['E']; ENTRY = g['ENTRY']; Stop = g['Stop']; allocdrv = g['allocdrv']
run_seq = g['run_seq']; word_at = g['word_at']; seqtext = g['seqtext']; evm1 = g['evm1']; FAULTS = g['FAULTS']
sys.path.insert(0, HERE)
from blockops import opname
SEED = 3131
M = (1 << 256) - 1
LST = open('/home/user/v4-core/research/network-risk/cycles/027/theme-monad-engine-agreement.work/out/pm-asm-0.16.7.txt').read().splitlines()


def clang_body(pc, op):
    tag = '//       0x%02x: %s' % (pc, op)
    i = LST.index(tag); out = []
    for l in LST[i + 1:]:
        if l.startswith('//'): break
        if l.endswith(':'): continue
        out.append(l)
    return out


def cstr(c, a):
    out = b''
    while len(out) < 200:
        x = c.read(a + len(out), 1)
        if not x: break
        out += bytes([x])
    return out.decode(errors='replace')


def s32(x): return x - (1 << 32) if x >> 31 else x


def model_state(m):
    """The Stack after the gcc call, in the hook's terms (logical register numbers, offsets, literals)."""
    c = m.c
    top = s32(c.read(S + 8, 4)); nb, ne = c.read(S + 0x140, 8), c.read(S + 0x148, 8)
    pb, pe = c.read(S + 0x158, 8), c.read(S + 0x160, 8)
    nneg = (ne - nb) // 8; npos = (pe - pb) // 8
    el = []
    for i in range(-nneg, top + 1):
        b = c.read(nb + 8 * (-i - 1), 8) if i < 0 else (c.read(pb + 8 * i, 8) if i < npos else 0)
        if not b: el.append((i, None)); continue
        d = m.loc(b)
        el.append((i, tuple(sorted((k, v) for k, v in d.items() if k in ('gen', 'avx', 'stack', 'lit')))))
    fa = [c.read(a, 1) for a in range(c.read(S + 0x50, 8), c.read(S + 0x58, 8))]
    return {'top': top, 'min': s32(c.read(S + 0xc, 4)), 'max': s32(c.read(S + 0x10, 4)), 'elems': el,
            'avail': sorted(m.keys(S + 0x28)), 'fgen': sorted(m.free_general()), 'favx': sorted(fa)}


def hook_state(st):
    el = []
    for e in st['elems']:
        if e.get('null') or e.get('absent'): el.append((e['i'], None)); continue
        d = {}
        if 'gen' in e: d['gen'] = e['gen']
        if 'avx' in e: d['avx'] = e['avx']
        if 'so' in e: d['stack'] = e['so'][0]
        if 'lit' in e: d['lit'] = int(e['lit'], 16)
        el.append((e['i'], tuple(sorted(d.items()))))
    return {'top': st['top'], 'min': st['min'], 'max': st['max'], 'elems': el, 'avail': sorted(st['avail']),
            'fgen': sorted(st['fgen']), 'favx': sorted(st['favx'])}


def build(kind, st, faults):
    m = Full(kind, faults)
    def assert_(c, m=m):
        raise Stop('monad_assertion_failed %s:%d in %s' % (cstr(c, c.r['rdx']), c.r['rcx'] & 0xffffffff, cstr(c, c.r['rdi'])))
    m.c.externs[0x131ad0] = assert_
    if FAULT == 'rodata-shared-label': m.rod_collide = True
    ids = {}; info = {}
    for e in st['elems']:
        if e.get('null') or e.get('absent'): raise Stop('null element in state')
        if e['id'] not in ids:
            info[e['id']] = e
            ids[e['id']] = m.elem(len(e['ix']), gen=e.get('gen'), avx=e.get('avx'), stack=e['so'][0] if 'so' in e else None,
                                 lit=int(e['lit'], 16) if 'lit' in e else None, indices=e['ix'], resv=e['rv'][1])
            if e['rv'][0]: m.c.write(ids[e['id']] + 0x40, 4, e['rv'][0])
            if 'so' in e: m.c.write(ids[e['id']] + 0x4c, 4, e['so'][1])
    neg = [0] * st['nneg']                       # position k holds index -(k+1); popped entries above top stay null
    for e in st['elems']:
        if e['i'] < 0: neg[-e['i'] - 1] = ids[e['id']]
    pos = [ids[e['id']] for e in st['elems'] if e['i'] >= 0]
    assert st['npos'] >= len(pos)
    v = m.alloc(8 * 64)
    for i, b in enumerate(pos): m.c.write(v + 8 * i, 8, b)
    m.c.write(S + 0x158, 8, v); m.c.write(S + 0x160, 8, v + 8 * len(pos)); m.c.write(S + 0x168, 8, v + 8 * 64)
    nv = m.alloc(8 * 64)
    for i, b in enumerate(neg): m.c.write(nv + 8 * i, 8, b)
    m.c.write(S + 0x140, 8, nv); m.c.write(S + 0x148, 8, nv + 8 * len(neg)); m.c.write(S + 0x150, 8, nv + 8 * 64)
    for off, k in ((0x08, 'top'), (0x0c, 'min'), (0x10, 'max'), (0x14, 'delta')): m.c.write(S + off, 4, st[k] & 0xffffffff)
    m.set_available(st['avail']); m.set_free_general(st['fgen']); m.set_free_avx(st['favx'])
    if st['dc'][0] != '(nil)' or st['dc'][1] != '(nil)': raise Stop('deferred comparison present: not modelled')
    return m, ids, info


def main():
    states = [json.loads(l) for l in open(os.path.join(W, 'out/states.jsonl'))]
    ops = json.load(open(os.path.join(W, 'out/value128-ops.json')))['blocks']
    want = {int(k, 16) for k in ops}
    sites = [(s, states[i + 1]) for i, s in enumerate(states) if s['w'] == 'i' and s['b'] in want and opname(s['pc']) in ('SHL', 'SHR', 'SAR')]
    faults = {}
    if FAULT and FAULT not in ('rodata-shared-label', 'state-dup-swap'):
        FF = dict(FAULTS); FF.update(json.load(open(os.path.join(HERE, 'faults31.json'))))
        for a, old, new in FF.get(FAULT, []): faults.setdefault(int(a, 16), []).append((old, new))
    rnd = random.Random(SEED)
    out = {'seed': SEED, 'fault': FAULT, 'sites': [], 'runs': 0, 'mismatchRuns': 0, 'clobberRuns': 0, 'stops': 0}
    t0 = time.time()
    for st, nxt in sites:
        if FAULT == 'state-dup-swap':
            st = json.loads(json.dumps(st)); a, b = st['elems'][-2], st['elems'][-3]
            for k in ('id', 'so', 'gen', 'avx', 'lit'):
                a[k], b[k] = b.get(k), a.get(k)
            for e in (a, b):
                for k in [k for k, v in e.items() if v is None]: del e[k]
        kind = opname(st['pc']); row = {'block': hex(st['b']), 'pc': hex(st['pc']), 'op': kind}
        try:
            m, ids, info = build(kind, st, faults)
            tab_pre = m.table(); allocdrv.TAB[:] = tab_pre
            m.c.call(ENTRY[kind][0], [E], maxsteps=2000000)
            tab_post = m.table(); row['tableChanged'] = tab_pre != tab_post
        except Stop as e:
            row['stop'] = str(e); row['flagged'] = True; out['stops'] += 1; out['flaggedSites'] = out.get('flaggedSites', 0) + 1
            out['sites'].append(row); continue
        gtxt = seqtext(m.emitted).splitlines()
        cb = clang_body(st['pc'], kind)
        row['gccStream'] = gtxt; row['clangStream'] = cb
        if canon(gtxt) == canon(cb): row['stream'] = 'equal-up-to-renaming'
        else:
            cg['FIXED'] = {'rax', 'rbx', 'rbp', 'rsp'}
            row['stream'] = 'equal-up-to-renaming-incl-rcx-row' if canon(gtxt) == canon(cb) else 'different'
            cg['FIXED'] = {'rax', 'rcx', 'rbx', 'rbp', 'rsp'}
        ms, hs = model_state(m), hook_state(nxt)
        row['postState'] = 'equal' if ms == hs else 'different'
        if ms != hs: row['postStateDiff'] = {k: [repr(ms[k]), repr(hs[k])] for k in ms if ms[k] != hs[k]}
        liveb = [b for b in set(ids.values()) if m.loc(b)['onstack']]
        bad = m.invariants(liveb)
        if bad: row['invariant'] = bad
        # top element after the call (positive vector) or the negative vector when top < 0
        tix = m.c.read(S + 8, 4); tix = tix - (1 << 32) if tix >> 31 else tix
        if tix >= 0: rb = m.c.read(m.c.read(S + 0x158, 8) + 8 * tix, 8)
        else: rb = m.c.read(m.c.read(S + 0x140, 8) + 8 * (-tix - 1), 8)
        cnt_e = st['elems'][-1]; val_e = st['elems'][-2]
        live = set(ids.values()) | {rb}
        post = {b: m.loc(b) for b in live}
        nmis = ncl = 0; ex = []
        for i in range(NW):
            w = {}
            for k, b in ids.items():
                e = info[k]; w[b] = int(e['lit'], 16) if 'lit' in e else rnd.choice([0, 1, M, 1 << 255, rnd.getrandbits(256), rnd.getrandbits(128), rnd.getrandbits(64)])
            init = [(w[ids[k]], {kk: (vv[0] if kk == 'so' else vv) for kk, vv in [('gen', info[k].get('gen')), ('avx', info[k].get('avx')), ('so', info[k].get('so'))] if vv is not None}) for k in ids]
            init = [(x, {('stack' if kk == 'so' else kk): vv for kk, vv in d.items()}) for x, d in init]
            allocdrv.TAB[:] = tab_pre
            try: c = run_seq(m, m.emitted, init, rnd)
            except Stop as e:
                nmis += 1; ex.append('seq stop ' + str(e)); break
            out['runs'] += 1
            allocdrv.TAB[:] = tab_post
            exp = evm1({'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}[kind], w[ids[cnt_e['id']]], w[ids[val_e['id']]])
            ww = dict(w); ww[rb] = exp
            for b in live:
                if b == rb or b in ids.values() and m.loc(b)['onstack']:
                    d = {k2: v2 for k2, v2 in post[b].items() if k2 in ('gen', 'avx', 'stack')}
                    for where, got in word_at(c, d).items():
                        if got != ww[b]:
                            if b == rb: nmis += 1
                            else: ncl += 1
                            if len(ex) < 5: ex.append({'elem': 'result' if b == rb else 'other', 'where': where, 'got': hex(got), 'want': hex(ww[b])})
        row.update({'runs': NW, 'mismatchRuns': nmis, 'clobberRuns': ncl, 'examples': ex})
        out['mismatchRuns'] += nmis; out['clobberRuns'] += ncl
        caught = row['stream'] == 'different' or row['postState'] != 'equal' or nmis or ncl or bool(row.get('invariant'))
        row['flagged'] = bool(caught); out['flaggedSites'] = out.get('flaggedSites', 0) + int(caught)
        out['sites'].append(row)
    x86emu = g['x86emu']; load_fn = g['load_fn']; cov = {}
    for f in sorted(set(sum(ENTRY.values(), [])) | set(g['EXTRA']) | set(g['LIFT'])):
        try: txt = load_fn(f)
        except FileNotFoundError: continue
        addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        hit = sum(1 for a in addrs if a in x86emu.VISITED)
        if hit: cov['%x' % f] = [hit, len(addrs), txt.splitlines()[0][:120]]
    out['instructionCoverage'] = cov
    out['seconds'] = round(time.time() - t0, 1)
    name = 'realshift%s.json' % ('-' + FAULT if FAULT else '')
    json.dump(out, open(os.path.join(OUTD, name), 'w'), indent=1)
    print(name, {k: v for k, v in out.items() if k not in ('sites', 'instructionCoverage')})
    for r in out['sites']: print(r['block'], r['pc'], r['op'], r.get('stream'), r.get('postState'), r.get('postStateDiff'), r.get('invariant'), r.get('stop'), r.get('mismatchRuns'), r.get('clobberRuns'), (r.get('examples') or [])[:1])
main()
