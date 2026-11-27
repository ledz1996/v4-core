"""Cycle 32, theme-monad-gcc-real-arith, Tasks 1, 2 and 5 for the MUL, DIV, MOD and MULMOD sites of the 128 un-entered
value blocks. For each site the virtual stack logged by the hooked clang harness (cycle 31 out/states.jsonl) is laid
out as the gcc 15.2.0 build of monad 0.16.7 reads it (cycle 31 realshift.build, cycle 30 layout) and the package's
whole Emitter::mul(long) 0x3838e0, Emitter::udiv(long) 0x383a20, Emitter::umod(long) 0x387840 or
Emitter::mulmod(long) 0x387590 runs in the cycle 27 x86 model. All functions in their direct-call closure
(out/closure.txt: mul_optimized, div_optimized<false>, mod_optimized<false>, modop_optimized<mulmod>, mul_mod2,
call_runtime_impl, spill_all_caller_save_general_regs, spill_avx_reg_range, RuntimeImpl::pass, mov_arg,
RuntimeImpl::call_impl, Stack::pop/push/alloc_stack_offset and the allocators) are interpreted from the package's
objdump text. Stubs: asmjit _emitI (recorded, 0 to 4 operands), RoData::add4/add8/add32 (recorded), operator
new/delete, memcpy, memset, the libstdc++ tree routines (cycle 30 allocdrv.py).
Checks per site: (a) the asmjit stream equals the clang listing body of the same pc up to consistent renaming;
(b) the gcc Stack after the call equals the clang hook state before the next instruction; (c) Task 2: at the call the
stream makes, which registers carry the argument and result pointers, which live virtual stack elements sit in
caller-saved general or AVX registers across the call, whether vzeroupper precedes it; (d) the stream is run on
NW operand sets, the runtime call being served by the package's own helper text (monad_vm_runtime_mul,
runtime::udiv, umod, mulmod with every callee) in the same x86 model, and every live word is compared with pyevm.py.
Live caller-saved registers are filled with random words before the run and the helper's clobbers reach them.
usage: python3 -I realarith.py <outdir> <nw> [fault]"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NW = int(sys.argv[2]); FAULT = sys.argv[3] if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
C31 = '/home/user/v4-core/research/network-risk/cycles/031/theme-monad-gcc-real-states.work'
# load cycle 31 realshift (which loads cycle 30 shiftfull/allocdrv/cmpclang) without running its main()
src = open(os.path.join(C31, 'scripts/realshift.py')).read().replace('\nmain()', '\n')
rs = {'__file__': os.path.join(C31, 'scripts/realshift.py'), '__name__': 'rs'}
sys.argv = [sys.argv[0], OUTD, '0']
exec(compile(src, 'realshift.py', 'exec'), rs)
g = rs['g']; allocdrv = rs['allocdrv']; x86emu = g['x86emu']; Stop = rs['Stop']
allocdrv.FN = os.path.join(W, 'out', 'fn')           # function text cut by closure.py from the same objdump file
canon = rs['canon']; cg = rs['cg']
S = rs['S']; E = rs['E']; ROD = allocdrv.ROD
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
from blockops import opname
sys.path.insert(0, HERE)
import helpers
SEED = 3232
M = (1 << 256) - 1
clos = [int(l.split()[0], 16) for l in open(os.path.join(W, 'out/closure.txt')) if 'EXTERN' not in l and 'STOP' not in l]
if os.environ.get('KINDS') and 0x3ad360 not in clos: clos.append(0x3ad360)
ARITH = {'MUL': 0x3838e0, 'DIV': 0x383a20, 'MOD': 0x387840, 'MULMOD': 0x387590}
OTHER = {'ADD': 0x378260, 'SUB': 0x378da0, 'LT': 0x37ad10, 'GT': 0x37ae80, 'EQ': 0x385860, 'ISZERO': 0x36eaa0,
         'AND': 0x387980, 'OR': 0x3867c0, 'XOR': 0x386010, 'NOT': 0x37b5e0, 'SGT': 0x37a5a0, 'SLT': 0x37a430}
TASK4 = os.environ.get('TASK4') == '1'          # Task 4: the other emit kinds, same driver
ENTRY = OTHER if TASK4 else ARITH
if os.environ.get('KINDS'): ENTRY = {k: v for k, v in ENTRY.items() if k in os.environ['KINDS'].split(',')}
NARG = {'MUL': 2, 'DIV': 2, 'MOD': 2, 'MULMOD': 3, 'ADD': 2, 'SUB': 2, 'LT': 2, 'GT': 2, 'EQ': 2, 'ISZERO': 1, 'AND': 2, 'OR': 2, 'XOR': 2, 'NOT': 1, 'SGT': 2, 'SLT': 2}
OPC = {'MUL': 0x02, 'DIV': 0x04, 'MOD': 0x06, 'MULMOD': 0x09, 'ADD': 0x01, 'SUB': 0x03, 'LT': 0x10, 'GT': 0x11, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'SGT': 0x13, 'SLT': 0x12}
for k, a in ENTRY.items(): g['ENTRY'][k] = [a] + [x for x in clos if x != a]
import closure
STOPS = {0x3a3ea0, 0x375c50, 0x3810b0, 0x373800, 0x131ad0, 0x3a3860} | (set() if os.environ.get('KINDS') else {0x3ad360})
ADDED = []
world = pyevm.World({0xaa: b''})
# indirect jumps and calls (switch tables, std::variant visits) in the emitter text: the target is read from the
# register or memory operand; the jump table words come from the ELF image through C.read
import emdrv
_oj = emdrv.C.i_jmp; _oc = x86emu.CPU.i_call
def _ij(self, o, pc, n):
    if re.match(r'^[0-9a-f]+$', o[0]): return _oj(self, o, pc, n)
    t = self.get(self.opnd(o[0]))
    if t in self.externs: self.externs[t](self); return self.i_ret(o, pc, n)
    INDIRECT.add((pc, t)); return t
def _ic(self, o, pc, n):
    if re.match(r'^[0-9a-f]+$', o[0]): return _oc(self, o, pc, n)
    t = self.get(self.opnd(o[0])); INDIRECT.add((pc, t))
    if t in self.externs: self.externs[t](self); return n
    self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
INDIRECT = set()
def _vshufps(self, o, pc, n):
    """VEX.128 vshufps (the model lacked it; mul_sequence<false> uses it at 0x3a1a92 to pack two dwords)."""
    d = self.opnd(o[0]); a = self.get(self.opnd(o[1])); b = self.get(self.opnd(o[2])); imm = int(o[3], 16)
    assert self._vw(d) == 128
    la = [(a >> (32 * i)) & 0xffffffff for i in range(4)]; lb = [(b >> (32 * i)) & 0xffffffff for i in range(4)]
    r = la[imm & 3] | (la[(imm >> 2) & 3] << 32) | (lb[(imm >> 4) & 3] << 64) | (lb[(imm >> 6) & 3] << 96)
    self.put(d, r)
emdrv.C.i_vshufps = _vshufps
def _btc(self, o, pc, n):
    """btc r64, imm8 (the model lacked it; Emitter::slt flips the sign bit of a literal limb with it)."""
    d = self.opnd(o[0]); b = int(o[1], 16) & (d[2] - 1); v = self.get(d)
    self.cf = (v >> b) & 1; self.put(d, v ^ (1 << b))
emdrv.C.i_btc = _btc
LIFT_ALLOC_LITERAL = os.environ.get('KINDS') is not None
emdrv.C.i_jmp = _ij; emdrv.C.i_call = _ic


def evm(op, args):
    """args from the top of the stack down."""
    code = b''.join(b'\x7f' + x.to_bytes(32, 'big') for x in reversed(args)) + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0); assert ok
    return int.from_bytes(ret, 'big')


FAULTS = json.load(open(os.path.join(HERE, 'faults32.json')))


def build(kind, st, faults, table=None):
    """realshift.build, plus the deferred comparison (Stack+0x128 stack_elem, +0x130 negated_stack_elem, both raw
    StackElem pointers, +0x138 Comparison; Stack::discharge_deferred_comparison 0x3ac3b0) and an optional limb table."""
    dc = st['dc']; st2 = dict(st); st2['dc'] = ['(nil)', '(nil)', dc[2]]
    m, ids, info = rs['build'](kind, st2, faults)
    m.c.externs[0x63c660] = lambda c, m=m: m._emit(c, [])
    if LIFT_ALLOC_LITERAL and 0x3ad360 in clos: m.c.externs.pop(0x3ad360, None)   # Stack::alloc_literal run from the package
    for off, x in ((0x128, dc[0]), (0x130, dc[1])):
        if x != '(nil)': m.c.write(S + off, 8, ids[x] + 8)
    m.c.write(S + 0x138, 4, dc[2])
    if table:
        for r in range(3):
            for l in range(4): m.c.write(allocdrv.GPQT + 64 * r + 16 * l + 4, 4, allocdrv.GP.index(table[r][l]))
    return m, ids, info


def derive_table(gtxt, cb, tab):
    return derive_table_stores(gtxt, cb, tab) or derive_table_lines(gtxt, cb, tab)


def derive_table_stores(gtxt, cb, tab):
    """Limb table from the stores of general register limbs to equal displacements in the two listings."""
    gl = {}; cl = {}
    for l in gtxt:
        mm = re.search(r'mov QWORD PTR \[rbp([+-]0x[0-9a-f]+)\],(r\w+)$', l)
        if mm: gl[int(mm.group(1), 16)] = mm.group(2)
    for l in cb:
        mm = re.search(r'mov qword ptr \[rbp([+-]\d+)?\], (r\w+)$', l)
        if mm: cl[int(mm.group(1) or 0)] = mm.group(2)
    new = [list(r) for r in tab]
    for d, rg in gl.items():
        if d in cl:
            for r in range(3):
                if rg in tab[r]: new[r][tab[r].index(rg)] = cl[d]
    return new if new != tab and all(sorted(a) == sorted(b) for a, b in zip(new, tab)) else None


def derive_table_lines(gtxt, cb, tab):
    """Limb table of the clang harness at this pc (the hook log does not carry gpq256_regs_), read by aligning the
    two listings line by line: every 64-bit register the gcc stream names maps to the one clang names at the same
    place, and the result must be a permutation inside each row of the table."""
    g = [l.split('\t', 1)[1] for l in gtxt if '\t' in l and not l.split('\t', 1)[1].startswith('ret')]
    if len(g) != len(cb): return None
    R = sorted({x for r in tab for x in r}, key=len, reverse=True)
    mp = {}
    for a, b in zip(g, cb):
        ra = re.findall(r'\b(r\w+)\b', a.lower()); rb_ = re.findall(r'\b(r\w+)\b', b.lower())
        ra = [x for x in ra if x in R]; rb_ = [x for x in rb_ if x in R]
        if len(ra) != len(rb_): return None
        for x, y in zip(ra, rb_):
            if mp.setdefault(x, y) != y: return None
    new = [[mp.get(x, x) for x in r] for r in tab]
    ok = new != tab and all(sorted(a) == sorted(b) for a, b in zip(new, tab))
    return new if ok else None


def normimm(lines):
    """asmjit prints a sign-extended immediate as -N in the clang listing and the model prints 0x...; same encoding."""
    out = []
    for l in lines:
        out.append(re.sub(r'(?<![\w\[+-])-(\d+)\b', lambda m: hex((1 << 64) - int(m.group(1))), l))
    return out

def words(rnd, kind, pos):
    """Operand word generator: FullMath / SqrtPriceMath / SwapMath shapes and edge words."""
    r = rnd.random()
    if r < 0.12: return rnd.choice([0, 1, 2, M, M - 1, 1 << 255, (1 << 255) - 1, 1 << 128, (1 << 128) - 1, 1 << 96, 1 << 160, (1 << 160) - 1, 1 << 64, (1 << 64) - 1, 10 ** 6, 999_999])
    if r < 0.3: return rnd.getrandbits(rnd.choice([1, 8, 24, 32, 63, 64, 65, 96, 127, 128, 129, 160, 192, 255]))
    if r < 0.45: return (rnd.getrandbits(64) << (64 * rnd.randrange(4))) & M
    if r < 0.55: return (1 << rnd.randrange(256)) + rnd.choice([-1, 0, 1]) & M
    return rnd.getrandbits(256)


def callsite(seq):
    """Task 2 facts from the gcc stream: the instructions before each call."""
    out = []
    for i, (mn, ops) in enumerate(seq):
        if mn == 'call':
            pre = seq[max(0, i - 6):i]
            out.append({'index': i, 'before': rs['seqtext'](pre).splitlines(), 'call': rs['seqtext']([seq[i]]).strip()})
    return out


def main():
    states = [json.loads(l) for l in open(os.path.join(C31, 'out/states.jsonl'))]
    ops = json.load(open(os.path.join(C31, 'out/value128-ops.json')))['blocks']
    want = {int(k, 16) for k in ops}
    sites = [(s, states[i + 1]) for i, s in enumerate(states) if s['w'] == 'i' and s['b'] in want and opname(s['pc']) in ENTRY]
    faults = {}
    if FAULT and FAULT in FAULTS:
        for a, old, new in FAULTS[FAULT]: faults.setdefault(int(a, 16), []).append((old, new))
    helpers.FAULT = FAULT
    rnd = random.Random(SEED)
    out = {'seed': SEED, 'fault': FAULT, 'sites': [], 'runs': 0, 'mismatchRuns': 0, 'clobberRuns': 0, 'stops': 0, 'flaggedSites': 0}
    t0 = time.time()
    for st, nxt in sites:
        kind = opname(st['pc']); row = {'block': hex(st['b']), 'pc': hex(st['pc']), 'op': kind}
        n = NARG[kind]; args_e = st['elems'][-n:][::-1]
        row['operands'] = [{k: e[k] for k in ('gen', 'avx', 'so', 'lit') if k in e} for e in args_e]
        def emit_once(table=None):
            for _ in range(40):
                m, ids, info = build(kind, st, faults, table)
                tab_pre = m.table(); allocdrv.TAB[:] = tab_pre
                try:
                    m.c.call(ENTRY[kind], [E, 0], maxsteps=5000000)
                    return m, ids, info, tab_pre, m.table()
                except Stop as e:
                    mm = re.match(r'pc ([0-9a-f]+) not in program', str(e))
                    if not mm or int(mm.group(1), 16) not in closure.IDX: raise
                    # a function reached through a pointer (std::function handler, member function pointer):
                    # add it and its direct-call closure, from the same objdump text, and emit again
                    new = [a for a, nm in closure.emit_all([int(mm.group(1), 16)]).items() if nm not in ('STOP', 'EXTERN/NONSTART') and a not in STOPS]
                    for a in new:
                        if a not in clos: clos.append(a); ADDED.append(a)
                    for k, a in ENTRY.items(): g['ENTRY'][k] = [a] + [x for x in clos if x != a]
            raise Stop('closure did not settle')
        try:
            m, ids, info, tab_pre, tab_post = emit_once()
            row['tableChanged'] = tab_pre != tab_post
            cb = rs['clang_body'](st['pc'], kind); gtxt = rs['seqtext'](m.emitted).splitlines()
            if canon(gtxt) != canon(normimm(cb)):
                nt = derive_table(gtxt, cb, tab_pre)
                if nt:
                    row['tableFromClangListing'] = nt
                    m, ids, info, tab_pre, tab_post = emit_once(nt)
        except Stop as e:
            row['stop'] = str(e); row['flagged'] = True; out['stops'] += 1; out['flaggedSites'] += 1
            out['sites'].append(row); print(row['block'], row['pc'], kind, 'STOP', e); continue
        if FAULT == 'helper-args-swapped' or FAULT == 'result-slot-wrong':
            pass
        seq = m.emitted
        gtxt = rs['seqtext'](seq).splitlines()
        cb = rs['clang_body'](st['pc'], kind)
        row['gccStream'] = gtxt; row['clangStream'] = cb
        row['rodconst'] = [(k, hex(v)) for k, v in m.rodconst]
        cbn = normimm(cb)
        if canon(gtxt) == canon(cbn): row['stream'] = 'equal-up-to-renaming'
        else:
            cg['FIXED'] = {'rax', 'rbx', 'rbp', 'rsp'}
            row['stream'] = 'equal-up-to-renaming-incl-rcx-row' if canon(gtxt) == canon(cbn) else 'different'
            cg['FIXED'] = {'rax', 'rcx', 'rbx', 'rbp', 'rsp'}
        ms, hs = rs['model_state'](m), rs['hook_state'](nxt)
        # deferred comparison after the call: which of the two slots is set, whether it is the top element, the code
        tix0 = rs['s32'](m.c.read(S + 8, 4))
        topb = m.c.read(m.c.read(S + 0x158, 8) + 8 * tix0, 8) if tix0 >= 0 else m.c.read(m.c.read(S + 0x140, 8) + 8 * (-tix0 - 1), 8)
        d0, d1 = m.c.read(S + 0x128, 8), m.c.read(S + 0x130, 8)
        ms['dc'] = (bool(d0), bool(d1), d0 == topb + 8 and bool(d0), d1 == topb + 8 and bool(d1), m.c.read(S + 0x138, 4) if (d0 or d1) else None)
        htop = nxt['elems'][-1]['id'] if nxt['elems'] else None
        hs['dc'] = (nxt['dc'][0] != '(nil)', nxt['dc'][1] != '(nil)', nxt['dc'][0] == htop, nxt['dc'][1] == htop, nxt['dc'][2] if nxt['dc'][0] != '(nil)' or nxt['dc'][1] != '(nil)' else None)
        row['postState'] = 'equal' if ms == hs else 'different'
        if ms != hs: row['postStateDiff'] = {k: [repr(ms[k]), repr(hs[k])] for k in ms if ms[k] != hs[k]}
        row['callsites'] = callsite(seq)
        # live elements and where they sit after the call
        tix = rs['s32'](m.c.read(S + 8, 4))
        rb = m.c.read(m.c.read(S + 0x158, 8) + 8 * tix, 8) if tix >= 0 else m.c.read(m.c.read(S + 0x140, 8) + 8 * (-tix - 1), 8)
        live = [b for b in set(ids.values()) if m.loc(b)['onstack']]
        post = {b: m.loc(b) for b in set(live) | {rb}}
        lac = []
        for b in live:
            if b == rb: continue
            if 'gen' in post[b]: lac.append('gen%d' % post[b]['gen'])
            if 'avx' in post[b]: lac.append('avx%d' % post[b]['avx'])
        row['liveRegsAfterEmit'] = sorted(lac)
        bad = m.invariants(live)
        if bad: row['invariant'] = bad
        nmis = ncl = 0; ex = []
        for i in range(NW):
            w = {}
            for k, b in ids.items():
                e = info[k]; w[b] = int(e['lit'], 16) if 'lit' in e else words(rnd, kind, 0)
            # FullMath shapes: denominators and moduli with a top limb of 0, 1, all ones
            if 'lit' not in args_e[-1] and rnd.random() < 0.3:
                top = rnd.choice([0, 1, (1 << 64) - 1])
                w[ids[args_e[-1]['id']]] = (top << 192) | rnd.getrandbits(rnd.choice([1, 64, 128, 192]))
            if n == 2 and rnd.random() < 0.15 and 'lit' not in args_e[1]:
                w[ids[args_e[1]['id']]] = w[ids[args_e[0]['id']]] if ids[args_e[1]['id']] != ids[args_e[0]['id']] else w[ids[args_e[1]['id']]]
            init = []
            for k in ids:
                d = {}
                for kk, vv in (('gen', info[k].get('gen')), ('avx', info[k].get('avx')), ('stack', info[k]['so'][0] if 'so' in info[k] else None)):
                    if vv is not None: d[kk] = vv
                init.append((w[ids[k]], d))
            # a deferred comparison element in the input holds the flag outcome of the comparison before this
            # instruction: choose the flags, and give those elements the 0 or 1 the flags mean
            cf, zf, sf, of = flags0 = tuple(rnd.getrandbits(1) for _ in range(4))
            truth = [cf, 1 - cf, int(not cf and not zf), int(cf or zf), int(sf != of), int(sf == of), int(not zf and sf == of), int(zf or sf != of), zf, 1 - zf]
            dcs = st['dc']
            if dcs[0] != '(nil)': w[ids[dcs[0]]] = truth[dcs[2]]
            if dcs[1] != '(nil)': w[ids[dcs[1]]] = truth[dcs[2] ^ 1]
            allocdrv.TAB[:] = tab_pre
            try: c = helpers.run_seq_calls(m, seq, init, rnd, flags=flags0)
            except Stop as e:
                nmis += 1; ex.append('seq stop ' + str(e)); break
            out['runs'] += 1
            allocdrv.TAB[:] = tab_post
            argv = [w[ids[e['id']]] for e in args_e]
            exp = evm(OPC[kind], argv)
            ww = dict(w); ww[rb] = exp
            # the result itself may be a deferred comparison: its value is the comparison of the final flags
            ftruth = [c.cf, 1 - c.cf, int(not c.cf and not c.zf), int(c.cf or c.zf), int(c.sf != c.of), int(c.sf == c.of),
                      int(not c.zf and c.sf == c.of), int(c.zf or c.sf != c.of), c.zf, 1 - c.zf]
            rdc = None
            if ms['dc'][2]: rdc = ftruth[ms['dc'][4]]
            if ms['dc'][3]: rdc = ftruth[ms['dc'][4] ^ 1]
            if rdc is not None:
                if rdc != exp:
                    nmis += 1
                    if len(ex) < 20: ex.append({'elem': 'result', 'where': 'flags', 'args': [hex(x) for x in argv], 'got': rdc, 'want': hex(exp)})
            for b in post:
                d = {k2: v2 for k2, v2 in post[b].items() if k2 in ('gen', 'avx', 'stack')}
                for where, got in rs['word_at'](c, d).items():
                    if got != ww[b]:
                        if b == rb: nmis += 1
                        else: ncl += 1
                        if len(ex) < 20: ex.append({'elem': 'result' if b == rb else 'other', 'where': where, 'args': [hex(x) for x in argv], 'got': hex(got), 'want': hex(ww[b])})
        row.update({'runs': NW, 'mismatchRuns': nmis, 'clobberRuns': ncl, 'examples': ex})
        out['mismatchRuns'] += nmis; out['clobberRuns'] += ncl
        caught = row['stream'] == 'different' or row['postState'] != 'equal' or nmis > 0 or ncl > 0 or bool(row.get('invariant'))
        row['flagged'] = bool(caught); out['flaggedSites'] += int(caught)
        out['sites'].append(row)
        print(row['block'], row['pc'], kind, row['stream'], row['postState'], row.get('postStateDiff'), row.get('invariant'), nmis, ncl, row['liveRegsAfterEmit'], row.get('tableFromClangListing'), (ex or [''])[:1], flush=True)
    cov = {}
    for f in sorted(set(clos) | set(helpers.HELPERS_ALL)):
        try: txt = allocdrv.load_fn(f)
        except FileNotFoundError: continue
        addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        hit = sum(1 for a in addrs if a in x86emu.VISITED)
        if hit: cov['%x' % f] = [hit, len(addrs), txt.splitlines()[0][:120]]
    out['instructionCoverage'] = cov; out['functionsAddedThroughPointers'] = ['%x' % a for a in ADDED]
    out['seconds'] = round(time.time() - t0, 1)
    name = ('realother%s.json' if TASK4 else 'realarith%s.json') % (('-' + FAULT if FAULT else '') + ('-' + os.environ['KINDS'].replace(',', '_') if os.environ.get('KINDS') else ''))
    json.dump(out, open(os.path.join(OUTD, name), 'w'), indent=1)
    print(name, {k: v for k, v in out.items() if k not in ('sites', 'instructionCoverage')})
main()
