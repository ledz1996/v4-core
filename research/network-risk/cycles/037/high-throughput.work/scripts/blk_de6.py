"""Cycle 37, lead L-1310: block 0xde6 of the compiled PoolManager (the delta read of clear(),
src/PoolManager.sol:311 via src/libraries/CurrencyDelta.sol:11-15 and :20-22) emitted whole from the shipped gcc 15.2.0
build of monad 0.16.7, from the cycle 31 logged real states, with the register limb table threaded from site to site as
the Emitter does. Emit functions: CALLER 0x36fe10, MSTORE 0x3a9dc0, CALLDATALOAD 0x3936a0 (cycle 33 task3.py), AND
(cycle 32/33 EMIT table), KECCAK256 and TLOAD through the call_runtime instances 0x351e00 and 0x351f40 that
compile_basic_blocks<MonadTraits<10>> calls (cycle 34 inl.py / blk.py), terminator Jump through cycle 33 term.py.
The concatenated stream is compared with the clang listing of the whole block under term.strict.
Read-only reuse of the cycle 31 to 34 work directories; outputs go to this cycle's work directory.
usage: python3 -I blk_de6.py <outdir>"""
import sys, os, json, re
OUTD = sys.argv[1]; os.makedirs(OUTD, exist_ok=True)
C = '/home/user/v4-core/research/network-risk/cycles'
C33 = C + '/033/theme-monad-gcc-terminators.work/scripts'
HERE = os.path.dirname(os.path.abspath(__file__))
MYFN = os.path.join(os.path.dirname(HERE), 'out', 'fn'); os.makedirs(MYFN, exist_ok=True)
sys.path.insert(0, C33)
import types
tsrc = open(C33 + '/term.py').read()
tsrc = tsrc.replace("MYFN = os.path.join(W, 'out', 'fn')", "MYFN = %r" % MYFN)
tsrc = tsrc.replace("os.path.join(HERE, 'faults33.json')", repr(C33 + '/faults33.json'))
_argv0 = list(sys.argv); sys.argv = [sys.argv[0], OUTD, '0']
_t = types.ModuleType('term'); _t.__file__ = C33 + '/term.py'
exec(compile(tsrc, 'term.py', 'exec'), _t.__dict__)
sys.modules['term'] = _t
src = open(C33 + '/block.py').read()
src = src.rstrip()[:-len('main()')]
src = src.replace("os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults33b.json')", "os.path.join(%r, 'faults33b.json')" % C33)
bm = {'__file__': C33 + '/block.py', '__name__': 'bm'}
exec(compile(src, 'block.py', 'exec'), bm)
sys.argv = _argv0
term = bm['term']; ra = bm['ra']; g = bm['g']; Stop = bm['Stop']; allocdrv = bm['allocdrv']; E = bm['E']
# MSTORE of a literal word allocates a literal element: run Stack::alloc_literal from the package (as task3.py)
term.STOPS.discard(0x3ad360)
if 0x3ad360 not in ra['clos']: ra['clos'].append(0x3ad360)
_build = ra['build']
def _build2(*a, **k):
    m, ids, info = _build(*a, **k); m.c.externs.pop(0x3ad360, None)
    return m, ids, info
ra['build'] = _build2
bm['EMIT'].update({'CALLER': 0x36fe10, 'MSTORE': 0x3a9dc0, 'CALLDATALOAD': 0x3936a0, 'KECCAK256': 0x351e00, 'TLOAD': 0x351f40})
RT = {'KECCAK256': 0x343f90, 'TLOAD': 0x340570}
CR = {'KECCAK256': 0x351e00, 'TLOAD': 0x351f40}
_orig = bm['emit_site']
def emit_site(kind, st, faults, table):
    if kind not in CR: return _orig(kind, st, faults, table)
    ent = CR[kind]
    for _ in range(20):
        clos = term.closure_of([ent] + ra['clos'])
        g['ENTRY'][kind] = [ent] + [a for a in clos if a != ent]
        m, ids, info = ra['build'](kind, st, faults, table)
        term.Equip(m, st)
        allocdrv.TAB[:] = m.table(); m._ids, m._info, m._tabpre = ids, info, m.table()
        try:
            m.c.call(ent, [E, 0, 1, RT[kind]], maxsteps=5000000)
            return m
        except Exception as e:
            mm = re.match(r'pc ([0-9a-f]+) not in program', str(e))
            if type(e).__name__ != 'Stop' or not mm: raise
            a = int(mm.group(1), 16)
            if a in ra['clos']: raise
            ra['clos'].append(a)
    raise Stop('closure did not settle')
bm['emit_site'] = emit_site

B = 0xde6
sts = [s for s in bm['STATES'] if s['b'] == B]
tab = term.TermModel('Jump', [s for s in sts if s['w'] == 't'][0], {}).m.table()
res = {'block': hex(B), 'sites': None}
sts_, seq, rod, per, tm, kind = bm['build_block'](B, {}, tab)
gl = term.text_lines(seq)
lst = bm['block_listing'](B)
cb = [l for l in lst if not l.startswith('//')]
eq0 = term.strict(gl) == term.strict(cb)
# the model numbers each site's local labels from 0; the compiler numbers them through the function. Make them
# unique per site before the whole-block comparison (strict() then renames by first appearance).
gl2 = []; k = 0
for (pc_, kd, n) in per:
    for l in gl[k:k + n]: gl2.append(re.sub(r'\bL(\d+)\b', lambda mm: 'L%d' % (1000 * (len(gl2) and 0) + 100 * per.index((pc_, kd, n)) + int(mm.group(1))), l))
    k += n
assert k == len(gl)
eq = term.strict(gl2) == term.strict(cb)
res['equalBeforeLabelRenaming'] = eq0
gl = gl2
res.update({'sites': per, 'terminator': kind, 'gccLines': len(gl), 'clangLines': len(cb), 'equal': eq,
            'gccStream': gl, 'clangStream': cb})
if not eq:
    a, b = term.strict(gl), term.strict(cb)
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: res['firstDiff'] = [i, x, y]; break
json.dump(res, open(os.path.join(OUTD, 'blk-de6-stream.json'), 'w'), indent=1)
print('block 0xde6 sites', per, 'terminator', kind, 'gcc', len(gl), 'clang', len(cb), 'equal', eq, res.get('firstDiff'))

# ---------------------------------------------------------------------------------------------------------------
# Execution of the whole gcc stream from the block entry state, against pyevm.py on the block's own bytecode.
import random
pyevm = bm['pyevm']; helpers = bm['helpers']; CODE = bm['CODE']; M = (1 << 256) - 1; M64 = (1 << 64) - 1
NS = int(os.environ.get('NS', '4000')); FAULT = os.environ.get('FAULT')
ERR, EPI, JT, LBASE = term.ERR, term.EPI, term.JT, term.LBASE
# relabel local labels per site so that two sites' L0 do not share an id
seqr = []; k = 0; items = [x for x in seq]
# per[] counts text lines (bind lines included), seq entries map one to one onto text lines
assert len(items) == len(term.text_lines(items))
for si, (pc_, kd, n) in enumerate(per):
    for mn, ops in items[k:k + n]:
        def fix(o):
            if o[0] == 'label' and o[1] >= term.NBASE: return ('label', term.NBASE + 0x100 * (si + 1) + o[1] - term.NBASE) + tuple(o[2:])
            return o
        if mn == 'bind': seqr.append((mn, [fix(ops[0])]))
        else: seqr.append((mn, [fix(o) for o in ops]))
    k += n
_a, _b = term.strict(term.text_lines(seqr)), term.strict(cb)
if _a != _b: print([(x, y) for x, y in zip(_a, _b) if x != y][:4], [x for x in seq if any(o[0] == "label" for o in x[1])][:6]); sys.exit(1)
# bind every local label the block leaves unbound (the out-of-line slow path of CALLDATALOAD for calldata shorter
# than offset + 32) to a marker after the terminator; reaching it ends the run as 'fall', which counts as wrong
bound = {o[0][1] for mn, o in seqr if mn == 'bind'}
unb = sorted({op[1] for mn, ops in seqr if mn != 'bind' for op in ops if op[0] == 'label' and op[1] >= term.NBASE} - bound)
for u in unb: seqr.append(('bind', [('label', u)]))
res['unboundLocalLabels'] = len(unb)
CTX = 0x7ffe00000000; MEMP = 0x7ffd00000000; CDP = 0x7ffc00000000
RUN = {}
KECCAK_FN, TLOAD_FN = RT['KECCAK256'], RT['TLOAD']
class Cpu(helpers.CallCPU):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        R = RUN
        # Context fields the listing reads: caller (20 bytes big-endian at +60), calldata pointer +144 and size +168,
        # memory size +264 and memory pointer +272
        for i, b in enumerate(R['caller'].to_bytes(20, 'big')): self.write(CTX + 60 + i, 1, b)
        self.write(CTX + 144, 8, CDP); self.write(CTX + 168, 4, len(R['cd']))
        for i, b in enumerate(R['cd']): self.write(CDP + i, 1, b)
        self.write(CTX + 264, 4, R['msize']); self.write(CTX + 272, 8, MEMP)
        for i in range(128): self.write(MEMP + i, 1, R['mem0'][i])
    def i_movbe(self, o, pc, n):
        # MOVBE (Intel SDM): move with the byte order reversed; the cycle 27 model has no arm for it, the operand
        # size is the size of the register operand
        d = self.opnd(o[0]); s_ = self.opnd(o[1])
        b = d[2] if d[0] == 'r' else s_[2]
        v = self.get(s_, b)
        self.put(d, int.from_bytes(v.to_bytes(b // 8, 'little'), 'big'))
    def i_call(self, o, pc, n):
        s = o[0]
        if 'PTR' in s:
            t = self.get(self.opnd(s))
            R = RUN; rnd = R['rnd']
            if t == KECCAK_FN:
                off = self.read(self.r['rdx'], 32); size = self.read(self.r['rcx'], 32)
                data = bytes(self.read(MEMP + off + i, 1) for i in range(size))
                v = int.from_bytes(pyevm.keccak(data), 'big'); R['calls'].append(('keccak', off, size, v))
                self.write(self.r['rsi'], 32, v)
            elif t == TLOAD_FN:
                key = self.read(self.r['rdx'], 32); v = R['tstate'].get(key, 0)
                if FAULT == 'tload-result-bit0' : v ^= 1
                if FAULT == 'tload-key-low-limb-dropped': v = R['tstate'].get(key & ~M64, 0)
                R['calls'].append(('tload', key, v)); self.write(self.r['rsi'], 32, v)
            else:
                # memory growth call: rdi holds the new end; the runtime grows memory to a word multiple
                need = self.r['rdi']; R['calls'].append(('grow', hex(t), need))
                self.write(CTX + 264, 4, (need + 31) // 32 * 32)
                # the growth call has no spill before it in either build: the runtime reaches it through a trampoline
                # that saves every register (cycle 29 reading, OPCODES.md cycle 33 row), so the stub keeps them
                return n
            for r in ('rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11'): self.r[r] = rnd.getrandbits(64)
            for i in range(16): self.y[i] = rnd.getrandbits(256)
            for f in ('cf', 'zf', 'sf', 'of'): setattr(self, f, rnd.getrandbits(1))
            return n
        return super().i_call(o, pc, n)
helpers.CallCPU = Cpu

TEXTFAULTS = {'caller-limbs-swapped': [('[rbx+0x40]', '[rbx+0xQQ]'), ('[rbx+0x48]', '[rbx+0x40]'), ('[rbx+0xQQ]', '[rbx+0x48]')],
              'calldata-offset-32': [('add rdi,0x24', 'add rdi,0x20')],
              'mstore-currency-offset-0': [('[rax+0x20]', '[rax+0x0]')]}
if FAULT in TEXTFAULTS:
    _st = allocdrv.seqtext
    def seqtext(sq):
        tx = _st(sq); n0 = 0
        for a, b in TEXTFAULTS[FAULT]:
            n0 += tx.count(a); tx = tx.replace(a, b)
        assert n0, 'fault pattern not found'
        return tx
    allocdrv.seqtext = seqtext
class _R: pass
rodobj = rod
e = [s for s in sts_ if s['w'] == 'e'][0]; t = [s for s in sts_ if s['w'] == 't'][0]
lo = e['min']; depth_out = t['top'] - lo + 1
body = CODE[B:t['pc']]
rnd = random.Random(3737)
INT128 = (1 << 127) - 1
def slot(caller, cur):
    return int.from_bytes(pyevm.keccak((caller & ((1 << 160) - 1)).to_bytes(32, 'big') + (cur & ((1 << 160) - 1)).to_bytes(32, 'big')), 'big')
stats = {'runs': 0, 'bad': 0, 'modes': {}, 'eqAmount': 0, 'grow': 0}; ex = []
for i in range(NS):
    caller = rnd.choice([rnd.getrandbits(160), (1 << 160) - 1, 1, rnd.getrandbits(160) | (1 << 159)])
    cur = rnd.choice([0, rnd.getrandbits(160), (1 << 160) - 1, rnd.getrandbits(256)])   # dirty high bits too
    amount = rnd.choice([0, 1, rnd.getrandbits(64), rnd.getrandbits(127), INT128, INT128 + 1, rnd.getrandbits(256)])
    mode = rnd.choice(['zero', 'equal', 'plus1', 'minus1', 'negative', 'neg-equal', 'random', 'unset'])
    a128 = amount & M
    dv = {'zero': 0, 'equal': a128, 'plus1': (a128 + 1) & M, 'minus1': (a128 - 1) & M, 'negative': (-(rnd.getrandbits(100) + 1)) & M,
          'neg-equal': (-a128) & M, 'random': rnd.getrandbits(256), 'unset': None}[mode]
    ts = {}
    if dv is not None: ts[slot(caller, cur)] = dv
    for _ in range(rnd.randrange(3)): ts[rnd.getrandbits(256)] = rnd.getrandbits(256)
    # neighbouring slots: same caller other currency, swapped order
    ts[slot(cur, caller)] = rnd.getrandbits(256)
    sel = bytes.fromhex('80f0b44c')
    cd = sel + (cur & M).to_bytes(32, 'big') + amount.to_bytes(32, 'big') + bytes(rnd.choice([0, 0, 1, 31, 64]))
    msize = rnd.choice([0, 32, 64, 96, 128])
    mem0 = bytes(rnd.getrandbits(8) for _ in range(128))
    RUN.update({'caller': caller, 'cd': cd, 'msize': msize, 'mem0': mem0, 'tstate': ts, 'calls': [], 'rnd': rnd})
    entry = [cur]
    pre = b'\x7f' + cur.to_bytes(32, 'big')
    post = b''
    for kk in range(depth_out): post += b'\x61' + (32 * kk).to_bytes(2, 'big') + b'\x52'
    post += b'\x61' + (32 * depth_out).to_bytes(2, 'big') + b'\x5f\xf3'
    w = pyevm.World({0xaa: pre + body + post})
    for kk, v in ts.items(): w.transient[(0xaa, kk)] = v
    ok, ret = w.call(caller, 0xaa, 0, cd, False, 0)
    assert ok
    ref = [int.from_bytes(ret[32 * kk:32 * kk + 32], 'big') for kk in range(depth_out)]
    refw = {t['top'] - kk: v for kk, v in enumerate(ref)}
    init = [(cur, {'stack': -1})]
    flags = tuple(rnd.getrandbits(1) for _ in range(4))
    c, ex_, rbp, SP = term.run_stream(rodobj, seqr, init, rnd, flags, 300 + rnd.randrange(50))
    stats['runs'] += 1; stats['modes'][mode] = stats['modes'].get(mode, 0) + 1
    if any(x[0] == 'grow' for x in RUN['calls']): stats['grow'] += 1
    bad = []
    if ex_[0] != 'block' or ex_[1] != refw[t['top']]: bad.append(('successor', repr(ex_), hex(refw[t['top']])))
    for ix in range(lo, t['top']):
        got = term.word(c, rbp, ix)
        if got != refw[ix]: bad.append(('word', ix, hex(got), hex(refw[ix])))
    if c.r['rbp'] != (rbp + 32 * t['delta']) & M64: bad.append(('rbp',))
    # the decision of src/PoolManager.sol:314 on these words, by the source: revert unless int128(amount) == delta
    tl = term.word(c, rbp, 0); amt = term.word(c, rbp, 2)
    if (amt <= INT128) and tl == amt: stats['eqAmount'] += 1
    if bad:
        stats['bad'] += 1
        if len(ex) < 10: ex.append({'run': i, 'mode': mode, 'bad': bad[:4], 'calls': [str(x) for x in RUN['calls']]})
res.update({'execution': {'seed': 3737, 'fault': FAULT, 'stats': stats, 'examples': ex,
            'note': 'words compared at stack indexes %d..%d (currency, delta from TLOAD, literal 0xe14, CALLDATALOAD(0x24)); successor must be the reference jump target' % (lo, t['top'] - 1)}})
json.dump(res, open(os.path.join(OUTD, 'blk-de6%s.json' % ('-' + FAULT if FAULT else '')), 'w'), indent=1)
print('execution', FAULT, stats, ex[:1])
