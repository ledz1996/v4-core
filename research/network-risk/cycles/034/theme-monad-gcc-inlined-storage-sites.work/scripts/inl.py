"""Cycle 34, theme-monad-gcc-inlined-storage-sites, Tasks 2, 3 and 5.
The dispatch arms of compile_basic_blocks<MonadTraits<10>> (0x35e020, monad 0.16.7 package, gcc 15.2.0) for
KECCAK256, SLOAD, SSTORE, TLOAD and LOG0-4 are four instructions each: lea rcx,<runtime fn>; mov edx,1; mov rsi,r12;
mov rdi,rbx; call <Emitter::call_runtime<Args...>(long, bool, fn)>. gcc inlined Emitter::sha3<>/sload<>/sstore<>/
tload<>/log<N><> (emitter.hpp:406-534) into the block compiler, but not call_runtime<Args...>: each signature has its
own out-of-line instance that builds the RuntimeImpl (emitter.hpp:150-166) and calls call_runtime_impl 0x3837e0.
TSTORE is the one arm that builds RuntimeImpl inline (0x35e5ff-0x35e66e). This driver runs, from the package's
objdump text in the cycle 27 x86 model, the call_runtime instance the arm calls, with exactly the arm's register
arguments (rdi = Emitter, rsi = remaining_base_gas, edx = 1, rcx = runtime function), on the virtual stack logged
by the cycle 31 hook before each site, and for TSTORE runs call_runtime_impl on the RuntimeImpl the inline arm
writes. Checks: (a) the asmjit stream equals the clang listing body of the pc up to consistent renaming; (b) the
gcc Stack after the call equals the hook state before the next instruction; (c) the emitted stream is run on NW
operand sets with the runtime call served by a Python reference (dicts for storage and transient storage, pyevm's
Keccak-256 over a random memory image, a log list) that also overwrites every caller-saved general and vector
register with random words, as the System V ABI allows; the argument words must be the EVM operands in order, the
result must land where the Stack says, and every other live element must keep its word.
usage: python3 -I inl.py <outdir> <nw> [fault]"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NW = int(sys.argv[2]); FAULT = sys.argv[3] if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
C = '/home/user/v4-core/research/network-risk/cycles'
C31 = C + '/031/theme-monad-gcc-real-states.work'; C32 = C + '/032/theme-monad-gcc-real-arith.work'
MYFN = os.path.join(W, 'out', 'fn'); os.makedirs(MYFN, exist_ok=True)
sys.path.insert(0, C32 + '/scripts')
import closure
closure.FN = MYFN
_argv = list(sys.argv)
src = open(C32 + '/scripts/realarith.py').read().replace('\nmain()', '\n')
ra = {'__file__': C32 + '/scripts/realarith.py', '__name__': 'ra'}
sys.argv = [_argv[0], OUTD, '0']
exec(compile(src, 'realarith.py', 'exec'), ra)
sys.argv = _argv
rs = ra['rs']; g = ra['g']; allocdrv = ra['allocdrv']; x86emu = ra['x86emu']; Stop = ra['Stop']; emdrv = ra['emdrv']
allocdrv.FN = MYFN
helpers = ra['helpers']; pyevm = ra['pyevm']; canon = ra['canon']; normimm = ra['normimm']
S = ra['S']; E = ra['E']; clos = ra['clos']
sys.path.insert(0, C31 + '/scripts')
from blockops import opname
SEED = 3434
M = (1 << 256) - 1; M64 = (1 << 64) - 1
# runtime functions (monad-0.16.7.s symbols) and the call_runtime instance each arm of compile_basic_blocks calls
RT = {'KECCAK256': 0x343f90, 'SLOAD': 0x450670, 'SSTORE': 0x451fd0, 'TLOAD': 0x340570, 'TSTORE': 0x340610,
      'LOG0': 0x44b800, 'LOG1': 0x44bee0, 'LOG2': 0x44c8a0, 'LOG3': 0x44d3c0, 'LOG4': 0x44e020}
CR = {'KECCAK256': 0x351e00, 'SLOAD': 0x351f40, 'SSTORE': 0x352400, 'TLOAD': 0x351f40, 'TSTORE': None,
      'LOG0': 0x352540, 'LOG1': 0x352080, 'LOG2': 0x3521a0, 'LOG3': 0x352660, 'LOG4': 0x352780}
NARG = {'KECCAK256': 2, 'SLOAD': 1, 'SSTORE': 2, 'TLOAD': 1, 'TSTORE': 2, 'LOG0': 2, 'LOG1': 3, 'LOG2': 4, 'LOG3': 5, 'LOG4': 6}
RESULT = {'KECCAK256', 'SLOAD', 'TLOAD'}
GAS = 777          # remaining_base_gas (r12 in the arm); SSTORE passes it to the runtime as its last argument
FAULTS = json.load(open(os.path.join(HERE, 'faults34.json')))
for k, a in CR.items():
    if a: g['ENTRY'][k] = [a] + [x for x in clos if x != a]
g['ENTRY']['TSTORE'] = [0x3837e0] + [x for x in clos if x != 0x3837e0]
# cut every function the model loads from the same objdump text into out/fn
for a in set(v for v in CR.values() if v) | set(clos) | set(g['EXTRA']) | set(sum(g['ENTRY'].values(), [])):
    if a in closure.IDX: closure.get(a)


def emit(kind, st, faults, gas=GAS, table=None):
    m, ids, info = ra['build'](kind, st, faults, table)
    tab = m.table(); allocdrv.TAB[:] = tab
    if kind == 'TSTORE':
        # the RuntimeImpl that 0x35e5ff-0x35e662 writes at rsp+0x80, then call_runtime_impl(Emitter, &rt)
        rt = m.alloc(0x80)
        for off, n, v in ((0, 8, E), (8, 24, 0), (0x20, 8, gas), (0x28, 1, 1), (0x30, 8, RT['TSTORE']), (0x38, 8, 3),
                          (0x40, 8, 0), (0x48, 1, 1), (0x50, 16, 0), (0x60, 16, 0)):
            m.c.write(rt + off, n, v)
        m.c.call(0x3837e0, [E, rt], maxsteps=5000000)
    else:
        fn = RT[kind]
        if FAULT == 'arm-wrong-runtime-fn' and kind == 'SLOAD': fn = RT['TLOAD']
        m.c.call(CR[kind], [E, gas, 1, fn], maxsteps=5000000)
    return m, ids, info, tab, m.table()


class Ref:
    """Python reference for the runtime routines; records every call."""
    def __init__(self, rnd):
        self.rnd = rnd; self.calls = []; self.st = {}; self.tst = {}; self.logs = []
        self.mem = bytes(rnd.getrandbits(8) for _ in range(512))
    def run(self, c, fn):
        rd = lambda p: c.read(p, 32)
        a = [c.r[r] for r in ('rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9')] + [c.read(c.r['rsp'] + 8 * i, 8) for i in range(2)]
        kind = {v: k for k, v in RT.items()}[fn]
        rec = {'kind': kind, 'ctx': a[0], 'rsp_mod16': c.r['rsp'] % 16}
        if kind in ('SLOAD', 'TLOAD'):
            key = rd(a[2]); rec['args'] = [key]
            v = (self.st if kind == 'SLOAD' else self.tst).setdefault(key, self.rnd.getrandbits(256))
            rec['result'] = v; rec['resultPtr'] = a[1]; c.write(a[1], 32, v)
        elif kind == 'KECCAK256':
            off, size = rd(a[2]), rd(a[3]); rec['args'] = [off, size]
            o, s = off % 256, size % 256
            v = int.from_bytes(pyevm.keccak((self.mem * 2)[o:o + s]), 'big')
            rec['result'] = v; rec['resultPtr'] = a[1]; c.write(a[1], 32, v)
        elif kind == 'SSTORE':
            rec['args'] = [rd(a[1]), rd(a[2])]; rec['gas'] = a[3]; self.st[rec['args'][0]] = rec['args'][1]
        elif kind == 'TSTORE':
            rec['args'] = [rd(a[1]), rd(a[2])]; self.tst[rec['args'][0]] = rec['args'][1]
        else:
            n = NARG[kind]; rec['args'] = [rd(a[1 + i]) for i in range(n)]; self.logs.append(rec['args'])
        self.calls.append(rec)
        # System V: rax, rcx, rdx, rsi, rdi, r8-r11 and all vector registers are caller-saved
        for r in ('rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11'): c.r[r] = self.rnd.getrandbits(64)
        for i in range(16): c.y[i] = self.rnd.getrandbits(256)
        for f in ('cf', 'zf', 'sf', 'of'): setattr(c, f, self.rnd.getrandbits(1))


class RefCPU(allocdrv.SeqCPU):
    ref = None
    def i_ret(self, o, pc, n):
        # the emitted code may write outgoing stack arguments at [rsp], which in native code lies in the frame the
        # entry reserved; in this harness that word is the return address of the run, so the final ret ends the run
        if self.r['rsp'] == 0x7ffff0000000 - 8:
            self.r['rsp'] += 8; return 0xdead0000
        return super().i_ret(o, pc, n)
    def i_call(self, o, pc, n):
        s = o[0]
        if 'PTR' in s:
            t = self.get(self.opnd(s))
            if t not in RT.values(): raise Stop('indirect call to %x' % t)
            self.ref.run(self, t); return n
        return super().i_call(o, pc, n)


def run_seq(m, seq, init, rnd, ref, flags):
    rbp = 0x7fff00000000; rbx = 0x7ffe00000000
    text = allocdrv.seqtext(seq)
    if text not in emdrv.SCACHE: emdrv.SCACHE[text] = x86emu.Prog(text)
    c = RefCPU(emdrv.SCACHE[text], {}); c.ref = ref
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in m.rod.items(): c.write(ROD + a, 1, b)
    c.r['rbp'] = rbp; c.r['rbx'] = rbx
    c.cf, c.zf, c.sf, c.of = flags; c.flags0 = flags
    for w, d in init:
        L = [(w >> (64 * i)) & M64 for i in range(4)]
        if 'gen' in d:
            for i in range(4): c.r[allocdrv.gp_of(d['gen'])[i]] = L[i]
        if 'avx' in d: c.y[d['avx']] = w
        if 'stack' in d:
            for i in range(4): c.write(rbp + 32 * d['stack'] + 8 * i, 8, L[i])
    c.call(0x1000, [], maxsteps=200000)
    if c.r['rbx'] != rbx: raise Stop('reg_context not restored')
    if c.r['rbp'] != rbp: raise Stop('rbp changed')
    if c.r['rsp'] != 0x7ffff0000000: raise Stop('rsp not balanced')
    return c
ROD = allocdrv.ROD


def streamcmp(m, gtxt, cb):
    if canon(gtxt) == canon(normimm(cb)): return 'equal-up-to-renaming'
    # asmjit prints a zero displacement from rsp as [rsp+0x0] in the model and [rsp] in the listing
    g2 = [l.replace('[rsp+0x0]', '[rsp]') for l in gtxt]
    if canon(g2) == canon(normimm(cb)): return 'equal-up-to-renaming'
    # the model's RoData stub gives two equal 32-byte literals two addresses; the real RoData (and the clang listing)
    # gives them one. Map every model RoData address to the first address with the same 32 bytes.
    first = {}; rep = {}
    for a in sorted(set(int(x, 16) for l in g2 for x in re.findall(r'\[(0x7000[0-9a-f]+)\]', l))):
        b = bytes(m.rod.get(a - ROD + i, 0) for i in range(32))
        rep[a] = first.setdefault(b, a)
    g3 = [re.sub(r'\[(0x7000[0-9a-f]+)\]', lambda mm: '[0x%x]' % rep[int(mm.group(1), 16)], l) for l in g2]
    if canon(g3) == canon(normimm(cb)): return 'equal-up-to-renaming-after-rodata-dedup'
    return 'different'


def words(rnd):
    r = rnd.random()
    if r < 0.2: return rnd.choice([0, 1, 2, 0x20, 0x40, 0xa0, M, 1 << 255, (1 << 160) - 1, (1 << 128) - 1, 1 << 64])
    if r < 0.5: return rnd.getrandbits(rnd.choice([8, 64, 128, 160, 255]))
    return rnd.getrandbits(256)


def main():
    states = [json.loads(l) for l in open(os.path.join(C31, 'out/states.jsonl'))]
    sites_meta = {(r['block'], r['pc']): r for r in json.load(open(os.path.join(W, 'out/sites.json')))['sites']}
    want = {int(k, 16) for k in json.load(open(os.path.join(C31, 'out/value128-ops.json')))['blocks']}
    ONLY = os.environ.get('ONLY')
    LOGTAB = os.environ.get('LOGTAB') == '1'
    if LOGTAB:
        # Task 4: the limb table of each state from the extended hook (out/states34.jsonl), no table from the listing
        L34 = [json.loads(l) for l in open(os.path.join(W, 'out/states34.jsonl'))]
        GPN = allocdrv.GP
        for a, b in zip(states, L34): a['_tab'] = [[GPN[x] for x in r] for r in b['gpq']]
    sites = [(s, states[i + 1]) for i, s in enumerate(states) if s['w'] == 'i' and s['b'] in want and opname(s['pc']) in RT
             and (not ONLY or opname(s['pc']) in ONLY.split(','))]
    faults = {}
    if FAULT and FAULT in FAULTS:
        for a, old, new in FAULTS[FAULT]: faults.setdefault(int(a, 16), []).append((old, new))
    rnd = random.Random(SEED)
    out = {'seed': SEED, 'fault': FAULT, 'gas': GAS, 'sites': [], 'runs': 0, 'mismatchRuns': 0, 'clobberRuns': 0, 'stops': 0, 'flaggedSites': 0}
    t0 = time.time()
    SYNDC = os.environ.get('SYNDC') == '1'
    if SYNDC:
        # Task 5 only: no logged state holds a deferred comparison at these sites, so make one. The deepest element
        # below the operands that sits only in a stack slot becomes the deferred comparison (its word lives in the
        # flags, cc 0..9 as Stack+0x138), which call_runtime_impl must discharge before the call clobbers the flags.
        syn = []
        for st, nxt in sites:
            n = NARG[opname(st['pc'])]
            cand = [e for e in st['elems'][:-n] if 'so' in e and 'gen' not in e and 'avx' not in e and 'lit' not in e and len(e['ix']) == 1
                    and sum(1 for x in st['elems'] if x['id'] == e['id']) == 1]
            if not cand: continue
            st = json.loads(json.dumps(st)); e = [x for x in st['elems'] if x['id'] == cand[0]['id']][0]
            av = sorted(set(st['avail']) | {e['so'][0]}); st['avail'] = av; del e['so']
            st['dc'] = [e['id'], '(nil)', rnd.randrange(10)]
            syn.append((st, nxt))
        sites = syn
    for st, nxt in sites:
        kind = opname(st['pc']); meta = sites_meta.get((hex(st['b']), hex(st['pc'])), {})
        row = {'block': hex(st['b']), 'pc': hex(st['pc']), 'op': kind, 'src': '%s:%s' % (meta.get('file'), meta.get('line')), 'group': meta.get('group')}
        n = NARG[kind]; args_e = st['elems'][-n:][::-1]
        row['operands'] = [{k: e[k] for k in ('gen', 'avx', 'so', 'lit') if k in e} for e in args_e]
        cb = rs['clang_body'](st['pc'], kind)
        gas = GAS
        if kind == 'SSTORE':
            # remaining_base_gas (r12 in the arm) is not in the hook log; the clang listing prints it as the immediate
            # of the fourth argument, so take it from there and also emit once with another value (only that
            # immediate may change)
            gas = int(re.search(r'mov rcx, (-?\d+)$', [l for l in cb if l.startswith('mov rcx')][0]).group(1))
            try:
                m0 = emit(kind, st, faults, gas + 1000)[0]; g0 = rs['seqtext'](m0.emitted).splitlines()
                m1 = emit(kind, st, faults, gas)[0]; g1 = rs['seqtext'](m1.emitted).splitlines()
                row['gasOnlyInImmediate'] = [a for a, b in zip(g0, g1) if a != b] == [l for l in g0 if 'mov rcx,0x%x' % (gas + 1000) in l] and len(g0) == len(g1)
            except Stop as e: row['gasOnlyInImmediate'] = 'stop ' + str(e)
        row['remainingBaseGas'] = gas
        try:
            m, ids, info, tab_pre, tab_post = emit(kind, st, faults, gas, st.get('_tab'))
            if LOGTAB: row['loggedTable'] = st['_tab']; row['tableAfterEqualsLoggedNext'] = (m.table() == nxt['_tab'])
            gtxt = rs['seqtext'](m.emitted).splitlines()
            if canon(gtxt) != canon(normimm(cb)) and not LOGTAB:
                nt = ra['derive_table'](gtxt, cb, tab_pre)
                if nt:
                    row['tableFromClangListing'] = nt
                    m, ids, info = ra['build'](kind, st, faults, nt)
                    tab_pre = m.table(); allocdrv.TAB[:] = tab_pre
                    m2 = m
                    # re-run the arm with the clang limb table
                    if kind == 'TSTORE': raise Stop('tstore table rerun not modelled')
                    m.c.call(CR[kind], [E, gas, 1, RT[kind]], maxsteps=5000000); tab_post = m.table()
                    gtxt = rs['seqtext'](m.emitted).splitlines()
        except Stop as e:
            row['stop'] = str(e); row['flagged'] = True; out['stops'] += 1; out['flaggedSites'] += 1
            out['sites'].append(row); print(row['block'], row['pc'], kind, 'STOP', e, flush=True); continue
        seq = m.emitted
        row['gccStream'] = gtxt; row['clangStream'] = cb
        row['stream'] = streamcmp(m, gtxt, cb)
        ms, hs = rs['model_state'](m), rs['hook_state'](nxt)
        row['postState'] = ('equal' if ms == hs else 'different') if not SYNDC else 'not-compared-synthetic'
        if ms != hs: row['postStateDiff'] = {k: [repr(ms[k]), repr(hs[k])] for k in ms if ms[k] != hs[k]}
        row['callsites'] = ra['callsite'](seq)
        live = [b for b in set(ids.values()) if m.loc(b)['onstack']]
        rb = None
        if kind in RESULT:
            tix = rs['s32'](m.c.read(S + 8, 4))
            rb = m.c.read(m.c.read(S + 0x158, 8) + 8 * tix, 8) if tix >= 0 else m.c.read(m.c.read(S + 0x140, 8) + 8 * (-tix - 1), 8)
        post = {b: m.loc(b) for b in set(live) | ({rb} if rb else set())}
        row['resultLoc'] = {k: v for k, v in post[rb].items() if k in ('gen', 'avx', 'stack')} if rb else None
        bad = m.invariants(live)
        # a deferred comparison lives in the flags; the runtime call clobbers them, so none may survive the call,
        # and every live element must have a location
        if m.c.read(S + 0x128, 8) or m.c.read(S + 0x130, 8): bad = (bad or []) + ['deferred comparison survives the runtime call']
        for b in live:
            if not any(k in post[b] for k in ('gen', 'avx', 'stack', 'lit')): bad = (bad or []) + ['live element without a location after the call']
        if bad: row['invariant'] = bad
        nmis = ncl = 0; ex = []
        for i in range(NW):
            w = {}
            for k, b in ids.items():
                e = info[k]; w[b] = int(e['lit'], 16) if 'lit' in e else words(rnd)
            init = []
            for k in ids:
                d = {}
                for kk, vv in (('gen', info[k].get('gen')), ('avx', info[k].get('avx')), ('stack', info[k]['so'][0] if 'so' in info[k] else None)):
                    if vv is not None: d[kk] = vv
                init.append((w[ids[k]], d))
            flags0 = tuple(rnd.getrandbits(1) for _ in range(4))
            cf, zf, sf, of = flags0
            truth = [cf, 1 - cf, int(not cf and not zf), int(cf or zf), int(sf != of), int(sf == of), int(not zf and sf == of), int(zf or sf != of), zf, 1 - zf]
            if st['dc'][0] != '(nil)': w[ids[st['dc'][0]]] = truth[st['dc'][2]]
            ref = Ref(rnd)
            allocdrv.TAB[:] = tab_pre
            try: c = run_seq(m, seq, init, rnd, ref, flags0)
            except Stop as e:
                nmis += 1; ex.append('seq stop ' + str(e)); break
            out['runs'] += 1
            allocdrv.TAB[:] = tab_post
            argv = [w[ids[e['id']]] for e in args_e]
            bad1 = None
            if len(ref.calls) != 1: bad1 = 'calls %d' % len(ref.calls)
            else:
                rc = ref.calls[0]
                if rc['kind'] != kind: bad1 = 'runtime function %s' % rc['kind']
                elif rc['args'] != argv: bad1 = 'args'
                elif rc['ctx'] != 0x7ffe00000000: bad1 = 'context'
                elif kind == 'SSTORE' and rc['gas'] != gas: bad1 = 'gas'
            # reference result: pyevm for SLOAD/TLOAD is the stored word; for KECCAK256 the hash the reference returned
            # over the reference memory, recomputed here independently
            ww = dict(w)
            if rb and not bad1:
                rc = ref.calls[0]
                if kind == 'KECCAK256':
                    o, s = argv[0] % 256, argv[1] % 256
                    exp = int.from_bytes(pyevm.keccak((ref.mem * 2)[o:o + s]), 'big')
                else: exp = (ref.st if kind == 'SLOAD' else ref.tst)[argv[0]]
                ww[rb] = exp
            if bad1:
                nmis += 1
                if len(ex) < 20: ex.append({'call': bad1, 'args': [hex(x) for x in argv], 'got': [{k: (hex(v) if isinstance(v, int) else [hex(x) for x in v]) for k, v in r.items() if k in ('args', 'ctx', 'gas', 'rsp_mod16')} for r in ref.calls]})
            for b in post:
                if b not in ww: continue          # the result of a call already counted as wrong
                d = {k2: v2 for k2, v2 in post[b].items() if k2 in ('gen', 'avx', 'stack')}
                for where, got in rs['word_at'](c, d).items():
                    if got != ww[b]:
                        if b == rb: nmis += 1
                        else: ncl += 1
                        if len(ex) < 20: ex.append({'elem': 'result' if b == rb else 'other', 'where': where, 'args': [hex(x) for x in argv], 'got': hex(got), 'want': hex(ww[b])})
        row.update({'runs': NW, 'mismatchRuns': nmis, 'clobberRuns': ncl, 'examples': ex})
        out['mismatchRuns'] += nmis; out['clobberRuns'] += ncl
        if SYNDC: row['stream'] = 'not-compared-synthetic'
        caught = row['stream'] == 'different' or row['postState'] == 'different' or nmis > 0 or ncl > 0 or bool(row.get('invariant'))
        row['flagged'] = bool(caught); out['flaggedSites'] += int(caught)
        out['sites'].append(row)
        print(row['block'], row['pc'], kind, row['src'], row['stream'], row['postState'], row.get('postStateDiff'), nmis, ncl, row['resultLoc'], (ex or [''])[:1], flush=True)
    out['seconds'] = round(time.time() - t0, 1)
    if LOGTAB: out['tableAfterNotLogged'] = [r['pc'] for r in out['sites'] if r.get('tableAfterEqualsLoggedNext') is False]; out['flaggedSites'] += len(out['tableAfterNotLogged'])
    name = 'inl%s%s%s%s.json' % ('-logtab' if LOGTAB else '', '-syndc' if SYNDC else '', '-' + FAULT if FAULT else '', '-' + os.environ['ONLY'].replace(',', '_') if os.environ.get('ONLY') else '')
    json.dump(out, open(os.path.join(OUTD, name), 'w'), indent=1)
    print(name, {k: v for k, v in out.items() if k != 'sites'})
main()
