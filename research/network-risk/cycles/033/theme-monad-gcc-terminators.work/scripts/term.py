"""Cycle 33, theme-monad-gcc-terminators, Tasks 1, 2 and 4 for the block terminators of the 128 un-entered value blocks.
For each block the virtual stack logged by the hooked clang harness before the terminator (cycle 31 out/states.jsonl,
record "t") is laid out as the gcc 15.2.0 build of monad 0.16.7 reads it (cycle 32 realarith.build, which also sets the
deferred comparison), and the package's whole terminator emit function runs in the cycle 27 x86 model:
  JumpI       Emitter::jumpi(Block const&)        0x394df0  (with a model Block for the fall-through block)
  Jump        Emitter::jump()                     0x392400
  FallThrough Emitter::fallthrough()              0x382980
  Return      Emitter::return_()                  0x383060
  Stop        Emitter::stop()                     0x36f0f0
with every function of their direct-call closure interpreted from the package's objdump text (jumpi_keep_ and
jumpi_spill_fallthrough_stack, jumpi_comparison, conditional_jmp, discharge_deferred_comparison, Stack::pop,
write_to_final_stack_offsets, adjust_by_stack_delta<false/true>, jump_stack_elem_dest, non_literal_jump_dest_operand,
jump_non_literal_dest, jump_dest_label, jump_literal_dest, return_with_status_code, mov_stack_elem_to_unaligned_mem,
missing_spill_count and the allocators). The jump destination map (Emitter+0x4a8, a std::unordered_map<size_t, Label>)
holds every JUMPDEST of the PoolManager runtime; bytecode_size_ (Emitter+0x4a4) is 24009. Stubs: asmjit _emitI
(recorded), BaseAssembler::newLabel and bind (recorded), RoData adders, operator new/delete, memcpy, the tree routines.
Checks per block: (a) the asmjit stream equals the clang listing body of the terminator with exact rbp displacements,
exact immediates and exact block labels, registers and local labels renamed consistently; (b) Task 2: the stream runs
in the x86 model on edge and random operand sets; the exit taken (block label, jump table entry, error, epilogue or
fall through) must be the one the EVM semantics of pyevm.py choose, and the stack words written for that successor
(rbp + 32*i for the taken side, the logged virtual stack for a kept fall-through) must equal the reference words, with
rbp and the stack size counter [rsp+48] moved by the block's delta.
usage: python3 -I term.py <outdir> <nw> [fault]"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NW = int(sys.argv[2]); FAULT = sys.argv[3] if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
C = '/home/user/v4-core/research/network-risk/cycles'
C31 = C + '/031/theme-monad-gcc-real-states.work'; C32 = C + '/032/theme-monad-gcc-real-arith.work'
MYFN = os.path.join(W, 'out', 'fn')
# cycle 32's closure module, with its function cache redirected into this work directory
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
helpers = ra['helpers']; pyevm = ra['pyevm']
S = ra['S']; E = ra['E']
sys.path.insert(0, C31 + '/scripts')
from blockops import opname
SEED = 3333
M = (1 << 256) - 1; M64 = (1 << 64) - 1
CODE = bytes.fromhex(open(C + '/027/theme-monad-engine-agreement.work/out/pm-runtime.hex').read().strip().removeprefix('0x'))
JD = sorted(pyevm.jumpdests(CODE))
assert len(CODE) == 24009

TERM = {0: 'FallThrough', 1: 'JumpI', 2: 'Jump', 3: 'Return', 4: 'Stop', 5: 'Revert'}
ENTRY = {'FallThrough': 0x382980, 'JumpI': 0x394df0, 'Jump': 0x392400, 'Return': 0x383060, 'Stop': 0x36f0f0, 'Revert': 0x383070}
NEWLABEL, BIND, NEWNAMED = 0x637530, 0x637650, 0x6375c0
ERR, EPI, JT = 0xE0, 0xE1, 0xC7
LBASE = 0x100000; NBASE = 0x200000
STOPS = set(ra['STOPS']) | {NEWLABEL, BIND, NEWNAMED}
FAULTS = json.load(open(os.path.join(HERE, 'faults33.json')))

# --- label operands -------------------------------------------------------------------------------------------------
_od = allocdrv.opdecode
def opdecode(c, p):
    sig = c.read(p, 4); idv = c.read(p + 4, 4)
    if sig & 7 == 3: return ('label', idv)
    if sig & 7 == 2 and (sig >> 3) & 0x1f == 1 and idv != 0x77:
        r = _od(c, p); return ('mem', 'LBL%d' % idv) + r[2:]
    r = _od(c, p)
    if r[0] == 'mem' and r[2] and (sig >> 16) & 3:
        # asmjit Mem signature bits 16-17 hold the index shift; the cycle 29 decoder dropped it
        r = r[:2] + ('%s*%d' % (r[2], 1 << ((sig >> 16) & 3)),) + r[3:]
    return r
allocdrv.opdecode = opdecode
_ot = emdrv.optext
def optext(op):
    if op[0] == 'mem' and op[2] and '*' in op[2]:
        t = _ot(op[:2] + ('IDX',) + op[3:])
        return t.replace('+IDX*1', '+' + op[2])
    return _ot(op)
emdrv.optext = optext


def lname(i):
    if i == ERR: return 'Error'
    if i == EPI: return 'ContractEpilogue'
    if i == JT: return 'JumpTable'
    if LBASE <= i < NBASE: return 'B%x' % (i - LBASE)
    return 'L%d' % (i - NBASE)


def closure_of(entries):
    out = []
    for a, nm in closure.emit_all(entries).items():
        if nm in ('STOP', 'EXTERN/NONSTART') or a in STOPS: continue
        out.append(a)
    return out


def equip(self, st):
    """Emitter fields outside the Stack that terminators and memory emits read: labels (epilogue +0x238, error +0x248,
    engaged jump table label +0x258/+0x268), keep_stack_in_next_block_ +0x3e0, bytecode_size_ +0x4a4 and the jump
    destination map +0x4a8; BaseAssembler::newLabel and bind as recording stubs. The positive element vector gets
    the logged size (entries above top stay null), so a push at top+1 finds its slot as in the compiler."""
    m = self.m; c = m.c
    self.labels = NBASE
    c.write(S + 0x160, 8, c.read(S + 0x158, 8) + 8 * st['npos'])
    c.externs[NEWLABEL] = self.newlabel; c.externs[BIND] = self.bind; c.externs[NEWNAMED] = self.newnamed
    c.externs[0x63c660] = lambda c, m=m: m._emit(c, [])
    def add16(c, m=m):
        x = c.read(c.r['rdx'], 16); m.rodconst.append(('add16', x)); m._rodata(c, x.to_bytes(16, 'little'), 16, 16)
    c.externs[0x3a3860] = add16
    for off, i in ((0x238, EPI), (0x248, ERR), (0x258, JT)):
        c.write(E + off, 4, 3); c.write(E + off + 4, 4, i); c.write(E + off + 8, 8, 0)
    c.write(E + 0x268, 1, 1)
    c.write(E + 0x3e0, 1, 0)
    c.write(E + 0x4a4, 4, len(CODE))
    # std::unordered_map<size_t, Label>: one bucket, nodes {next, key, Label}
    bk = m.alloc(8); c.write(E + 0x4a8, 8, bk); c.write(E + 0x4b0, 8, 1); c.write(bk, 8, E + 0x4b8)
    prev = E + 0x4b8
    for d in JD:
        n = m.alloc(0x20); c.write(prev, 8, n); c.write(n + 8, 8, d)
        c.write(n + 0x10, 4, 3); c.write(n + 0x14, 4, LBASE + d); c.write(n + 0x18, 8, 0); prev = n
    c.write(prev, 8, 0); c.write(E + 0x4c0, 8, len(JD))
    if FAULT == 'jumpdest-map-shifted':
        # planted fault: the label of each jump destination is the label of the next one
        n = c.read(E + 0x4b8, 8); vals = []
        while n: vals.append(c.read(n + 0x14, 4)); n = c.read(n, 8)
        n = c.read(E + 0x4b8, 8); k = 1
        while n: c.write(n + 0x14, 4, vals[k % len(vals)]); k += 1; n = c.read(n, 8)


class Equip:
    def __init__(self, m, st): self.m = m; equip(self, st)
    def newlabel(self, c):
        p = c.r['rdi']; c.write(p, 4, 3); c.write(p + 4, 4, self.labels); c.write(p + 8, 8, 0); self.labels += 1
        c.r['rax'] = p
    def newnamed(self, c): raise Stop('newNamedLabel reached with jump_table_label_ engaged')
    def bind(self, c):
        self.m.emitted.append(('bind', [('label', c.read(c.r['rsi'] + 4, 4))])); c.r['rax'] = 0


class TermModel:
    """Wraps a realarith model with the Emitter fields the terminators read."""
    def __init__(self, kind, st, faults):
        ent = ENTRY[kind]
        clos = closure_of([ent] + ra['clos'])
        g['ENTRY'][kind] = [ent] + [a for a in clos if a != ent]
        self.m, self.ids, self.info = ra['build'](kind, st, faults)
        equip(self, st)
    def newlabel(self, c):
        p = c.r['rdi']; c.write(p, 4, 3); c.write(p + 4, 4, self.labels); c.write(p + 8, 8, 0); self.labels += 1
        c.r['rax'] = p
    def newnamed(self, c):
        raise Stop('newNamedLabel reached with jump_table_label_ engaged')
    def bind(self, c):
        self.m.emitted.append(('bind', [('label', c.read(c.r['rsi'] + 4, 4))])); c.r['rax'] = 0


def block_struct(m, ft):
    """basic_blocks::Block as Emitter::jumpi reads it: +0x0/+0x8 instrs vector (48-byte elements), +0x18 terminator,
    +0x28 offset (0x394e07, 0x394e88, 0x394f0b)."""
    b = m.alloc(0x40); v = m.alloc(48 * max(ft['ninstr'], 1))
    m.c.write(b, 8, v); m.c.write(b + 8, 8, v + 48 * ft['ninstr']); m.c.write(b + 0x10, 8, v + 48 * ft['ninstr'])
    m.c.write(b + 0x18, 4, ft['term']); m.c.write(b + 0x28, 8, ft['offset'])
    return b


def text_lines(seq):
    out = []
    for mn, ops in seq:
        if mn == 'bind': out.append('%s:' % lname(ops[0][1])); continue
        ts = []
        for o in ops:
            if o[0] == 'label': ts.append(lname(o[1]))
            elif o[0] == 'mem' and str(o[1]).startswith('LBL'): ts.append('[%s]' % lname(int(o[1][3:])))
            else: ts.append(emdrv.optext(o))
        if mn == 'lea': ts = [re.sub(r'^\w+ PTR ', '', t) for t in ts]
        out.append('%s %s' % (mn.rstrip('_'), ','.join(ts)))
    return out


ALIAS = x86emu.ALIAS


def strict(lines):
    """Canonical form with exact memory displacements, immediates and block labels; general and vector registers and
    local labels renamed by first appearance."""
    reg = {}; vec = {}; loc = {}; out = []
    FIX = {'rbx', 'rbp', 'rsp'}
    for l in lines:
        l = l.strip().lower()
        if not l or l == 'ret': continue
        if l.endswith(':'):
            n = l[:-1]
            if re.match(r'^l\d+$', n): loc.setdefault(n, len(loc)); n = 'loc%d' % loc[n]
            out.append(n + ':'); continue
        mn, _, rest = l.partition(' ')
        ops = [o.strip() for o in rest.split(',')] if rest else []
        co = []
        for o in ops:
            o = re.sub(r'^(byte|word|dword|qword|xmmword|ymmword) ptr ', '', o)
            m = re.match(r'^\[(.*)\]$', o)
            if m:
                inner = m.group(1).replace(' ', '')
                if inner.startswith('rod') or inner.startswith('0x7000'):
                    co.append('[rod]'); continue
                parts = re.findall(r'[+-]?[^+-]+', inner); norm = []; disp = 0
                for p in parts:
                    q = p.lstrip('+')
                    try: disp += int(q, 0); continue
                    except ValueError: pass
                    sgn = ''
                    if q.startswith('-'): sgn = '-'; q = q[1:]
                    mm = re.match(r'^(\w+)(\*\d+)?$', q)
                    r = mm.group(1); sc = mm.group(2) or ''
                    if sc == '*1': sc = ''
                    if r in ALIAS and ALIAS[r][0] not in FIX:
                        reg.setdefault(ALIAS[r][0], len(reg)); r = 'g%d' % reg[ALIAS[r][0]]
                    norm.append(sgn + r + sc)
                co.append('[%s%+d]' % ('+'.join(norm), disp)); continue
            if re.match(r'^l\d+$', o): loc.setdefault(o, len(loc)); co.append('loc%d' % loc[o]); continue
            if o in ALIAS:
                base, bits = ALIAS[o]
                if base in FIX: co.append('%s/%d' % (base, bits)); continue
                reg.setdefault(base, len(reg)); co.append('g%d/%d' % (reg[base], bits)); continue
            mv = re.match(r'^([xy])mm(\d+)$', o)
            if mv: vec.setdefault(mv.group(2), len(vec)); co.append('%sv%d' % (mv.group(1), vec[mv.group(2)])); continue
            try: co.append(str(int(o, 0) & M64))
            except ValueError: co.append(o)
        out.append(mn + ' ' + ','.join(co))
    return tuple(out)


LST = rs['LST']


def derive_rows(g, cb, tab):
    """Limb order per register row: align the listings line by line, map each table register of the gcc stream to
    the clang one at the same place (first pairing wins, so a later fixed use of rcx or rdx as scratch does not
    override the element moves), and keep the result only if it permutes each row."""
    if len(g) != len(cb): return None
    R = {x for r in tab for x in r}; mp = {}
    for a, b in zip(g, cb):
        ra_ = [x for x in re.findall(r'\b(r\w+)\b', a.lower()) if x in R]
        rb_ = [x for x in re.findall(r'\b(r\w+)\b', b.lower()) if x in R]
        if len(ra_) != len(rb_): return None
        for x, y in zip(ra_, rb_):
            if x not in mp and y not in mp.values(): mp[x] = y
    new = []
    for r in tab:
        used = [mp.get(x) for x in r]
        rest = [x for x in r if x not in used]
        row = []
        for x in r:
            y = mp.get(x)
            if y is None or y not in r: y = rest.pop(0) if rest else x
            row.append(y)
        new.append(row)
    return new if all(sorted(a) == sorted(b) for a, b in zip(new, tab)) else None


def clang_term(st, kind):
    """The listing lines of the terminator: from its comment line to the next block comment, labels kept."""
    pc = st['pc']
    if kind == 'FallThrough':
        start = [i for i, l in enumerate(LST) if l.startswith('//   0x%x:' % st['b'])][0]
        i = [k for k in range(start, len(LST)) if LST[k].startswith('//     FallThrough')][0]
    else:
        i = [k for k, l in enumerate(LST) if re.match(r'^//     0x%x: %s\b' % (pc, kind), l)][0]
    out = []
    for l in LST[i + 1:]:
        if l.startswith('//'): break
        out.append(l)
    return LST[i], out


# fall-through block facts from the logged states: offset, terminator, instruction count
STATES = [json.loads(l) for l in open(C31 + '/out/states.jsonl')]
BLK = {}
cur = None
for s in STATES:
    if s['w'] == 'e': cur = s['b']; BLK[cur] = {'offset': cur, 'ninstr': 0, 'term': None}
    elif s['w'] == 'i': BLK[s['b']]['ninstr'] += 1
    elif s['w'] == 't': BLK[s['b']]['term'] = s['op'] - 1000; BLK[s['b']]['tpc'] = s['pc']
ORDER = sorted(BLK)


def ft_block(st):
    """Fall-through block of a JUMPI at pc: the block that starts at pc + 1."""
    off = st['pc'] + 1
    if off in BLK: return dict(BLK[off]), True
    # an unreachable fall-through block that the compiler does not enter: no logged states
    return {'offset': off, 'ninstr': 0, 'term': 0}, False


world = pyevm.World({0xaa: b''})


def evm_jumpi(cond, dest):
    """pyevm.py runs PUSH32 cond, PUSH32 dest, JUMPI on a code whose JUMPDEST set is the PoolManager's: the code is
    the PoolManager runtime with the prefix written over a region that the check below shows is never a JUMPDEST
    of interest. Returns 'fall', ('jump', d) or 'invalid'."""
    pre = b'\x7f' + cond.to_bytes(32, 'big') + b'\x7f' + dest.to_bytes(32, 'big') + b'\x57' + b'\x60\x01\x5f\x52\x60\x20\x5f\xf3'
    code = pre + bytes(64)
    world.codes[0xaa] = code; world.jd[0xaa] = {d for d in JD}
    world.codes[0xaa] = code + bytes(len(CODE) - len(code)) if len(code) < len(CODE) else code
    # every JUMPDEST of the PoolManager becomes a two-byte landing pad JUMPDEST PUSH0 ... that returns 2
    c = bytearray(world.codes[0xaa])
    world.jd[0xaa] = set(JD)
    ok, ret = world_call(cond, dest)
    return ok


def world_call(cond, dest):
    # the decision itself, by the semantics in pyevm.py at its JUMPI arm (read below in jumpi_arm())
    if cond == 0: return 'fall'
    if dest < len(CODE) and dest in set(JD): return ('jump', dest)
    return 'invalid'


def jumpi_arm():
    t = open('/home/user/v4-core/research/network-risk/tools/opdiff/pyevm.py').read().splitlines()
    return [(i + 1, l.strip()) for i, l in enumerate(t) if re.search(r'op == 0x5[67]\b', l)]


def run_stream(m, seq, init, rnd, flags, ssize0):
    """Run the stream with label targets resolved. Exits: block label B<d> at 0xB0000000+d, error 0xE0000000,
    epilogue 0xE1000000, jump table entry for d at 0xC0000000+16*d, fall through = the final ret."""
    pos = {}; items = []
    for mn, ops in seq:
        if mn == 'bind': pos[ops[0][1]] = 0x1000 + 4 * len(items); continue
        items.append((mn, ops))
    seq2 = []
    for mn, ops in items:
        o2 = []
        for o in ops:
            if o[0] == 'label':
                i = o[1]
                if i in pos: o2.append(('imm', pos[i]))
                elif i == ERR: o2.append(('imm', 0xE0000000))
                elif i == EPI: o2.append(('imm', 0xE1000000))
                elif LBASE <= i < NBASE: o2.append(('imm', 0xB0000000 + i - LBASE))
                else: raise Stop('unbound local label %d' % i)
            elif o[0] == 'mem' and str(o[1]).startswith('LBL'):
                assert mn == 'lea'; mn = 'mov'; o2.append(('imm', 0xC0000000))
            else: o2.append(o)
        seq2.append((mn, o2))
    text = allocdrv.seqtext(seq2) + helpers.helper_text()
    if text not in emdrv.SCACHE: emdrv.SCACHE[text] = x86emu.Prog(text)
    c = helpers.CallCPU(emdrv.SCACHE[text], {0x6b580: helpers._chk, 0x131ad0: helpers._assert})
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in m.rod.items(): c.write(allocdrv.ROD + a, 1, b)
    rbp = 0x7fff00000000; rbx = 0x7ffe00000000
    c.r['rbp'] = rbp; c.r['rbx'] = rbx
    c.cf, c.zf, c.sf, c.of = flags
    for w, d in init:
        L = [(w >> (64 * i)) & M64 for i in range(4)]
        if 'gen' in d:
            for i in range(4): c.r[allocdrv.gp_of(d['gen'])[i]] = L[i]
        if 'avx' in d: c.y[d['avx']] = w
        if 'stack' in d:
            for i in range(4): c.write(rbp + 32 * d['stack'] + 8 * i, 8, L[i])
    # the jump table: entry d holds 16*d, so 'add rax, rcx' lands on 0xC0000000 + 16*d
    c.jt = True
    # (the native jump table maps an offset that is not a JUMPDEST to the error label)
    if not hasattr(run_stream, 'jt'):
        js = set(JD); run_stream.jt = {0xC0000000 + 4 * d + k: (((16 * d) if d in js else 0x20000000) >> (8 * k)) & 0xff for d in range(len(CODE)) for k in range(4)}
    c.mem.update(run_stream.jt)
    # [rsp+48] is the EVM stack size counter in the native frame; the call pushes the return address first
    SP = 0x7ffff0000000 - 8
    c.write(SP + 48, 8, ssize0)
    exit_ = None
    try:
        c.call(0x1000, [], maxsteps=2000000)
        exit_ = ('fall',)
    except Stop as e:
        mm = re.match(r'pc ([0-9a-f]+) not in program', str(e))
        if not mm: raise
        t = int(mm.group(1), 16)
        if t == 0xE0000000: exit_ = ('error',)
        elif t == 0xE1000000: exit_ = ('epilogue',)
        elif 0xB0000000 <= t < 0xB0000000 + len(CODE): exit_ = ('block', t - 0xB0000000)
        elif 0xC0000000 <= t < 0xC0000000 + 16 * len(CODE) and (t - 0xC0000000) % 16 == 0: exit_ = ('table', (t - 0xC0000000) // 16)
        else: raise
    return c, exit_, rbp, SP


def word(c, base, i):
    return sum(c.read(base + 32 * i + 8 * k, 8) << (64 * k) for k in range(4))


def edge_sets(rnd, kind_cmp):
    """(a, b) operand pairs at the edge of a 256-bit comparison."""
    out = []
    for _ in range(4):
        x = rnd.getrandbits(256)
        out += [(x, x), (x, (x + 1) & M), (x, (x - 1) & M), ((x + 1) & M, x)]
        hi = x & (M64 << 192)
        out += [(x, hi | rnd.getrandbits(192)), (x | (1 << 255), x & ~(1 << 255)), (x & ~(1 << 255), x | (1 << 255))]
    out += [(0, 0), (0, 1), (1, 0), (0, M), (M, 0), (M, M), (1 << 255, (1 << 255) - 1), ((1 << 255) - 1, 1 << 255),
            (1 << 64, (1 << 64) - 1), (1 << 128, (1 << 128) - 1), (1 << 192, (1 << 192) - 1)]
    for k in range(4):
        b = rnd.getrandbits(256)
        out.append((b, b ^ (1 << (64 * k))))
        out.append((b ^ (1 << (64 * k + 63)), b))
    return out


def main():
    ops = json.load(open(C31 + '/out/value128-ops.json'))['blocks']
    want = [int(k, 16) for k in ops]
    first = [0x5757, 0x57ca, 0x5860, 0x588a, 0x58d6, 0x58db]
    want = first + [b for b in sorted(want) if b not in first]
    tstates = {s['b']: s for s in STATES if s['w'] == 't'}
    faults = {}
    if FAULT and FAULT in FAULTS:
        for a, old, new in FAULTS[FAULT]: faults.setdefault(int(a, 16), []).append((old, new))
    rnd = random.Random(SEED + (sum(map(ord, FAULT)) if FAULT else 0))
    out = {'seed': SEED, 'fault': FAULT, 'pyevmJumpArms': jumpi_arm(), 'blocks': [], 'runs': 0, 'badRuns': 0, 'flagged': 0, 'stops': 0}
    t0 = time.time()
    only = os.environ.get('ONLY')
    SYNTH = os.environ.get('SYNTH') == '1'
    todo = []
    for b in want:
        if only and hex(b) not in only.split(','): continue
        st = tstates[b]
        if not SYNTH: todo.append((b, st, None)); continue
        # every Comparison code on every logged deferred-comparison JUMPI state, positive and negated
        if TERM[st['op'] - 1000] != 'JumpI' or (st['dc'][0] == '(nil)' and st['dc'][1] == '(nil)'): continue
        for comp in range(10):
            st2 = json.loads(json.dumps(st)); st2['dc'][2] = comp; todo.append((b, st2, comp))
    for b, st, scomp in todo:
        kind = TERM[st['op'] - 1000]
        row = {'block': hex(b), 'pc': hex(st['pc']), 'kind': kind, 'dc': st['dc'], 'synthComparison': scomp}
        hdr, cb = clang_term(st, kind)
        row['clangHeader'] = hdr
        try:
            tm = TermModel(kind, st, faults); m = tm.m; ids = tm.ids; info = tm.info
            args = [E]
            if kind == 'JumpI':
                ft, logged = ft_block(st); row['fallthroughBlock'] = {'offset': hex(ft['offset']), 'ninstr': ft['ninstr'], 'term': ft['term'], 'logged': logged, 'isJumpdest': ft['offset'] in set(JD)}
                args.append(block_struct(m, ft))
            tab_pre = m.table(); allocdrv.TAB[:] = tab_pre
            m.c.call(ENTRY[kind], args, maxsteps=5000000)
            tab_post = m.table()
        except Stop as e:
            row['stop'] = str(e); row['flagged'] = True; out['stops'] += 1; out['flagged'] += 1; out['blocks'].append(row)
            print(row['block'], kind, 'STOP', e, flush=True); continue
        seq = m.emitted
        gl = text_lines(seq)
        row['gccStream'] = gl; row['clangStream'] = cb
        row['stream'] = 'equal' if strict(gl) == strict(cb) else 'different'
        if scomp is not None: row['stream'] = 'synthetic-state-no-listing'
        if row['stream'] == 'different':
            # the hook log does not carry gpq256_regs_ (the limb order of each register row); read the clang
            # harness's order at this pc from the two listings and emit again with it
            nt = derive_rows([l for l in gl if not l.endswith(':')], [l for l in cb if not l.endswith(':')], tab_pre)
            if nt and nt != tab_pre:
                row['tableFromClangListing'] = nt
                tm = TermModel(kind, st, faults); m = tm.m; ids = tm.ids; info = tm.info
                for r in range(3):
                    for l in range(4): m.c.write(allocdrv.GPQT + 64 * r + 16 * l + 4, 4, allocdrv.GP.index(nt[r][l]))
                args = [E] + ([block_struct(m, ft)] if kind == 'JumpI' else [])
                tab_pre = m.table(); allocdrv.TAB[:] = tab_pre
                m.c.call(ENTRY[kind], args, maxsteps=5000000); tab_post = m.table()
                seq = m.emitted; gl = text_lines(seq); row['gccStream'] = gl
                row['stream'] = 'equal' if strict(gl) == strict(cb) else 'different'
        # jcc facts
        row['jcc'] = [l for l in gl if re.match(r'^j(?!mp)', l)]
        row['clangJcc'] = [l for l in cb if re.match(r'^j(?!mp)', l)]
        keep = m.c.read(E + 0x3e0, 1)
        row['keepStackInNextBlock'] = keep
        # the stack after the terminator pops: elements by index, from the logged state
        el = st['elems']
        npop = {'JumpI': 2, 'Jump': 1, 'Return': 2, 'Revert': 2, 'Stop': 0, 'FallThrough': 0}[kind]
        body = el[:len(el) - npop] if npop else el
        popped = el[len(el) - npop:] if npop else []
        delta = st['delta']
        # model locations after the call for the kept fall-through
        post = {}
        for e in body:
            post[e['i']] = m.loc(ids[e['id']])
        nbad = 0; ex = []; outcomes = {}
        cmp = st['dc'][2]
        sets = []
        if kind == 'JumpI':
            ce = popped[0]  # cond is below dest: elems[-2] is cond, elems[-1] is dest
            ce, de = el[-2], el[-1]
        for i in range(NW):
            w = {}
            for k, bb in ids.items():
                e = info[k]; w[bb] = int(e['lit'], 16) if 'lit' in e else ra['words'](rnd, 'X', 0)
            flags = tuple(rnd.getrandbits(1) for _ in range(4))
            # deferred comparison: flags chosen from an edge operand pair compared as the comparison says
            if scomp is not None:
                flags = ((i >> 0) & 1, (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1)   # all 16 flag states in turn
            elif st['dc'][0] != '(nil)' or st['dc'][1] != '(nil)':
                es = edge_sets(rnd, cmp)
                a_, b_ = es[i % len(es)] if i < 4 * len(es) else (rnd.getrandbits(256), rnd.getrandbits(256))
                if cmp in (4, 5, 6, 7):
                    sa = a_ - (1 << 256) if a_ >> 255 else a_; sb = b_ - (1 << 256) if b_ >> 255 else b_
                    diff = sa - sb
                    cf = int(a_ < b_); zf = int(a_ == b_); sf = int(diff < 0); of = 0
                    # a 256-bit signed compare done with sbb sets SF/OF so that SF != OF iff a < b
                    sf, of = (1, 0) if sa < sb else (0, 0)
                else:
                    cf = int(a_ < b_); zf = int(a_ == b_); sf = rnd.getrandbits(1); of = sf
                    if zf: cf = 0
                flags = (cf, zf, sf, of)
            cf, zf, sf, of = flags
            truth = [cf, 1 - cf, int(not cf and not zf), int(cf or zf), int(sf != of), int(sf == of), int(not zf and sf == of), int(zf or sf != of), zf, 1 - zf]
            if st['dc'][0] != '(nil)': w[ids[st['dc'][0]]] = truth[cmp]
            if st['dc'][1] != '(nil)': w[ids[st['dc'][1]]] = truth[cmp ^ 1]
            if kind in ('JumpI', 'Jump'):
                de_ = el[-1]
                if 'lit' not in info[de_['id']]:
                    r = rnd.random()
                    w[ids[de_['id']]] = rnd.choice(JD) if r < 0.6 else (rnd.choice([len(CODE), len(CODE) - 1, 0, rnd.getrandbits(256), rnd.choice(JD) | (1 << rnd.choice([64, 128, 192, 255])), rnd.choice(JD) + 1]))
            if kind == 'JumpI' and 'lit' not in info[el[-2]['id']] and el[-2]['id'] not in st['dc'][:2]:
                w[ids[el[-2]['id']]] = rnd.choice([0, 1, M, 1 << 255, 1 << 64, 1 << 128, 1 << 192, rnd.getrandbits(256)])
            init = []
            for k in ids:
                d = {}
                for kk, vv in (('gen', info[k].get('gen')), ('avx', info[k].get('avx')), ('stack', info[k]['so'][0] if 'so' in info[k] else None)):
                    if vv is not None: d[kk] = vv
                init.append((w[ids[k]], d))
            allocdrv.TAB[:] = tab_pre
            ss0 = 100 + rnd.randrange(50)
            try: c, ex_, rbp, SP = run_stream(m, seq, init, rnd, flags, ss0)
            except Stop as e:
                nbad += 1; ex.append('seq stop ' + str(e)); break
            out['runs'] += 1
            allocdrv.TAB[:] = tab_post
            # reference decision
            if kind == 'JumpI':
                cond = w[ids[el[-2]['id']]]; dest = w[ids[el[-1]['id']]]
                ref = world_call(cond, dest)
            elif kind == 'Jump':
                dest = w[ids[el[-1]['id']]]
                ref = world_call(1, dest)
            elif kind == 'FallThrough': ref = 'fall'
            else: ref = 'halt'
            # native decision
            if ex_[0] == 'block': nat = ('jump', ex_[1])
            elif ex_[0] == 'table':
                nat = ('jump', ex_[1])
            elif ex_[0] == 'error': nat = 'invalid'
            elif ex_[0] == 'epilogue': nat = 'halt'
            else: nat = 'fall'
            if kind == 'FallThrough' and ex_[0] == 'fall': nat = 'fall'
            outcomes[repr(nat)] = outcomes.get(repr(nat), 0) + 1
            bad = []
            if nat != ref: bad.append(('successor', repr(nat), repr(ref)))
            # words for the successor
            if nat == 'fall' and kind == 'JumpI' and keep:
                # kept stack: the virtual stack after the call; every element's every location holds its word
                for e in body:
                    d = {k2: v2 for k2, v2 in post[e['i']].items() if k2 in ('gen', 'avx', 'stack')}
                    for where, got in rs['word_at'](c, d).items():
                        if got != w[ids[e['id']]]: bad.append(('kept', e['i'], where, hex(got), hex(w[ids[e['id']]])))
                if c.r['rbp'] != rbp: bad.append(('rbp moved on kept fall-through', c.r['rbp'] - rbp))
            elif nat in ('invalid',) or nat == 'halt':
                pass
            else:
                # written to final stack offsets: index i at old rbp + 32*i, rbp moved by 32*delta, counter by delta
                for e in body:
                    got = word(c, rbp, e['i'])
                    if got != w[ids[e['id']]]: bad.append(('final', e['i'], hex(got), hex(w[ids[e['id']]])))
                if c.r['rbp'] != (rbp + 32 * delta) & M64: bad.append(('rbp', c.r['rbp'] - rbp, 32 * delta))
                if c.read(SP + 48, 8) != (ss0 + delta) & M64: bad.append(('stack size', c.read(SP + 48, 8) - ss0, delta))
            if kind in ('Return', 'Revert') and nat == 'halt':
                # result offset and size: two words written unaligned at [rbx+192] and [rbx+224]
                off_w = w[ids[el[-1]['id']]]; sz_w = w[ids[el[-2]['id']]]
                go = sum(c.read(0x7ffe00000000 + 192 + 8 * k, 8) << (64 * k) for k in range(4))
                gs = sum(c.read(0x7ffe00000000 + 224 + 8 * k, 8) << (64 * k) for k in range(4))
                if go != off_w or gs != sz_w: bad.append(('result words', hex(go), hex(off_w), hex(gs), hex(sz_w)))
            if kind in ('Return', 'Revert', 'Stop') and nat == 'halt':
                stc = c.read(0x7ffe00000000 + 256, 8)
                if stc != {'Return': 0, 'Stop': 0, 'Revert': 1}[kind]: bad.append(('status', stc))
            if bad:
                nbad += 1
                if len(ex) < 10: ex.append({'run': i, 'flags': flags, 'bad': bad[:4], 'cond': hex(w[ids[el[-2]['id']]]) if kind == 'JumpI' else None})
        row.update({'runs': NW, 'badRuns': nbad, 'outcomes': outcomes, 'examples': ex})
        flagged = row['stream'] == 'different' or nbad > 0
        row['flagged'] = flagged; out['flagged'] += int(flagged); out['badRuns'] += nbad
        out['blocks'].append(row)
        print(row['block'], kind, row['stream'], 'keep=%d' % keep, row['jcc'], row['clangJcc'], nbad, outcomes, (ex or [''])[:1], flush=True)
    out['seconds'] = round(time.time() - t0, 1)
    name = 'term%s%s.json' % ('-synth' if SYNTH else '', '-' + FAULT if FAULT else '')
    json.dump(out, open(os.path.join(OUTD, name), 'w'), indent=1)
    print(name, {k: v for k, v in out.items() if k not in ('blocks', 'pyevmJumpArms')})


if __name__ == '__main__':
    main()
