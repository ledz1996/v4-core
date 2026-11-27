"""Cycle 33, Task 2, whole blocks: the FullMath.mulDiv blocks 0x5757, 0x57ca, 0x5860, 0x588a, 0x58d6, 0x58db and the
mulDivRoundingUp remainder test block 0x51cf. Every code-emitting instruction of the block is emitted by the package's
own emit function from its logged state (cycle 31 states.jsonl), the terminator by term.py's TermModel, all with the one
register limb table that the clang listing of the block shows (read once from the whole block); PUSH, DUP, SWAP and POP
emit no code (checked against the listing). The concatenated stream must equal the clang listing of the block body
(prologue excluded) under term.strict. It then runs in the x86 model from the block's entry state, with the package's
runtime helpers serving any helper call, and the successor and every word at block exit are compared with pyevm.py run
on the block's own bytecode from the same entry stack.
Operand sets: random words from realarith.words, plus, for every comparison feeding a JUMPI and for the compare in the
middle of mulDiv (GT of remainder and prod0, LT of mm and prod0), sets where the compared words are equal, one apart, or
equal in the top limb only, made by tracing pyevm.py and rewriting the entry word that the compared word is a copy of.
usage: python3 -I block.py <outdir> <nsets> [fault]"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NS = int(sys.argv[2]); FAULT = sys.argv[3] if len(sys.argv) > 3 else None
sys.argv = [sys.argv[0], OUTD, '0'] + ([FAULT] if FAULT else [])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import term
from term import ra, rs, g, allocdrv, x86emu, Stop, emdrv, helpers, pyevm, S, E, CODE, JD, M, M64, opname, STATES
SEED = 3334 + int(os.environ.get('SEEDX', '0'))
BLOCKS = [0x5757, 0x57ca, 0x5860, 0x588a, 0x58d6, 0x58db, 0x51cf]
SHIFTS = {'SHL': 0x391590, 'SHR': 0x38d1a0, 'SAR': 0x38a5d0}
EMIT = dict(ra['ARITH']); EMIT.update(ra['OTHER']); EMIT.update(SHIFTS)
NOCODE = re.compile(r'^(PUSH\d*|DUP\d+|SWAP\d+|POP)$')
FAULTS = dict(term.FAULTS)
FAULTS.update(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults33b.json'))))
LST = term.LST


def block_listing(b):
    i = LST.index('//   0x%x:' % b)
    out = []; started = False
    for l in LST[i + 1:]:
        if l.startswith('//   0x'): break
        if l.startswith('//       0x'): started = True; out.append(l); continue
        if l.startswith('//     '): started = True; out.append(l); continue
        if started: out.append(l)
    return out


def site_lines(lst):
    """Split the block listing into (comment, code lines) groups."""
    grp = []
    for l in lst:
        if l.startswith('//'): grp.append([l, []])
        else: grp[-1][1].append(l)
    return grp


def emit_site(kind, st, faults, table):
    ent = EMIT[kind]
    for _ in range(20):
        clos = term.closure_of([ent] + ra['clos'])
        g['ENTRY'][kind] = [ent] + [a for a in clos if a != ent]
        m, ids, info = ra['build'](kind, st, faults, table)
        term.Equip(m, st)
        allocdrv.TAB[:] = m.table(); m._ids, m._info, m._tabpre = ids, info, m.table()
        try:
            m.c.call(ent, [E, 0], maxsteps=5000000)
            return m
        except Exception as e:
            mm = re.match(r'pc ([0-9a-f]+) not in program', str(e))
            if type(e).__name__ != 'Stop' or not mm: raise
            a = int(mm.group(1), 16)
            if a in ra['clos']: raise
            ra['clos'].append(a)
    raise Stop('closure did not settle')


def emit_term(kind, st, faults, table):
    tm = term.TermModel(kind, st, faults); m = tm.m
    for r in range(3):
        for l in range(4): m.c.write(allocdrv.GPQT + 64 * r + 16 * l + 4, 4, allocdrv.GP.index(table[r][l]))
    args = [E]
    if kind == 'JumpI':
        ft, _ = term.ft_block(st); args.append(term.block_struct(m, ft))
    allocdrv.TAB[:] = m.table()
    m.c.call(term.ENTRY[kind], args, maxsteps=5000000)
    return tm


class Rod:
    def __init__(self): self.rod = {}; self.top = 0


def relocate(seq, m, rod):
    """Move one site's read-only constants to their own range of the combined area."""
    base = (rod.top + 63) // 64 * 64
    for a, v in m.rod.items(): rod.rod[base + a] = v
    rod.top = base + (max(m.rod) + 1 if m.rod else 0)
    out = []
    for mn, ops in seq:
        out.append((mn, [o[:3] + (o[3] + base,) + o[4:] if o[0] == 'mem' and o[1] == 'ROD' else o for o in ops]))
    return out


def build_block(b, faults, table):
    sts = [s for s in STATES if s['b'] == b]
    seq = []; rod = Rod(); per = []; tables = []
    for s in sts:
        if s['w'] == 'i':
            k = opname(s['pc'])
            if NOCODE.match(k): per.append((hex(s['pc']), k, 0)); continue
            if k not in EMIT: raise Stop('no emit function wired for %s' % k)
            m = emit_site(k, s, faults, table)
            part = relocate(m.emitted, m, rod); seq += part; per.append((hex(s['pc']), k, len(part)))
            # an emit can reorder a row's limbs (a literal shift by a multiple of 64 renames limbs); the next
            # instruction starts from the table this one leaves, as in the compiler's own Emitter
            table = m.table(); tables.append(table)
        elif s['w'] == 't':
            kind = term.TERM[s['op'] - 1000]
            tm = emit_term(kind, s, faults, table)
            part = relocate(tm.m.emitted, tm.m, rod); seq += part; per.append((hex(s['pc']), kind, len(part)))
            build_block.tables = tables + [tm.m.table()]
            return sts, seq, rod, per, tm, kind
    raise Stop('no terminator state')


def evm_block(b, tpc, entry):
    """pyevm.py on PUSH32 entry words (deepest first), the block's bytes up to the terminator, then every stack word
    stored to memory (top first) and returned."""
    body = CODE[b:tpc]
    if CODE[b] == 0x5b: body = body[1:]
    pre = b''.join(b'\x7f' + w.to_bytes(32, 'big') for w in entry)
    return pre, body


def run_ref(pre, body, depth):
    post = b''
    for k in range(depth):
        post += b'\x61' + (32 * k).to_bytes(2, 'big') + b'\x52'
    post += b'\x61' + (32 * depth).to_bytes(2, 'big') + b'\x5f\xf3'
    code = pre + body + post
    w = pyevm.World({0xaa: code})
    ok, ret = w.call(1, 0xaa, 0, b'', False, 0)
    assert ok, 'reference run failed'
    return [int.from_bytes(ret[32 * k:32 * k + 32], 'big') for k in range(depth)]   # top first


def trace_ops(pre, body, kinds):
    """Operands of the comparison ops of the body: list of (pc in body, op, a, b) with a the top word."""
    code = pre + body + b'\x00'
    w = pyevm.World({0xaa: code}); w.trace = []; w.trace_stack = 2
    w.call(1, 0xaa, 0, b'', False, 0)
    out = []
    for d, pc, op, stk in w.trace:
        if pc >= len(pre) and op in kinds: out.append((pc - len(pre), op, stk[-1], stk[-2]))
    return out


def main():
    rnd = random.Random(SEED + (sum(map(ord, FAULT)) if FAULT else 0))
    faults = {}
    if FAULT and FAULT in FAULTS:
        for a, old, new in FAULTS[FAULT]: faults.setdefault(int(a, 16), []).append((old, new))
    out = {'seed': SEED, 'fault': FAULT, 'blocks': [], 'runs': 0, 'badRuns': 0, 'flagged': 0}
    t0 = time.time()
    only = os.environ.get('ONLY')
    for b in BLOCKS:
        if only and hex(b) not in only.split(','): continue
        row = {'block': hex(b)}
        lst = block_listing(b)
        grp = site_lines(lst)
        nocode_with_code = [c for c, ls in grp if re.match(r'^//       0x[0-9a-f]+: (PUSH\d*|DUP\d+|SWAP\d+|POP)\b', c) and ls]
        # code under a stack-op comment belongs to the discharge of the next emitting instruction only if the
        # listing prints it there; count such groups
        row['stackOpGroupsWithCode'] = nocode_with_code
        cb = [l for c, ls in grp for l in ls]
        st0 = [s for s in STATES if s['b'] == b]
        tab0 = term.TermModel('Jump', [s for s in st0 if s['w'] == 't'][0], {}).m.table()
        if FAULT:
            # a planted fault runs with the entry table the clean run found, and no search
            import glob
            for f_ in glob.glob(os.path.join(OUTD, 'block-0x*.json')):
                for r_ in json.load(open(f_))['blocks']:
                    if r_['block'] == hex(b): tab0 = r_['table']
        sts, seq, rod, per, tm, kind = build_block(b, faults, tab0)
        gl = term.text_lines(seq)
        table = tab0
        def score(gl_):
            a_, b_ = term.strict(gl_), term.strict(cb)
            return sum(1 for x, y in zip(a_, b_) if x == y) - abs(len(a_) - len(b_))
        if term.strict(gl) != term.strict(cb) and not FAULT:
            # the hook log does not carry the limb table at block entry: coordinate search over the 24 orders of
            # each row, scored by the number of equal lines of the whole block
            import itertools
            best = (score(gl), [list(r) for r in tab0], (sts, seq, rod, per, tm, kind))
            for _pass in range(2):
                for r in range(3):
                    for perm in itertools.permutations(tab0[r]):
                        tb = [list(x) for x in best[1]]; tb[r] = list(perm)
                        if tb == best[1]: continue
                        res = build_block(b, faults, tb); sc = score(term.text_lines(res[1]))
                        if sc > best[0]: best = (sc, tb, res)
                if term.strict(term.text_lines(best[2][1])) == term.strict(cb): break
            table = best[1]; sts, seq, rod, per, tm, kind = best[2]; gl = term.text_lines(seq)
        row['tablesThroughBlock'] = build_block.tables
        row['table'] = table; row['perSite'] = per; row['terminator'] = kind
        row['stream'] = 'equal' if term.strict(gl) == term.strict(cb) else 'different'
        row['gccLines'] = len(gl); row['clangLines'] = len(cb)
        if row['stream'] != 'equal':
            a_, b_ = term.strict(gl), term.strict(cb)
            k = next((i for i, (x, y) in enumerate(zip(a_, b_)) if x != y), min(len(a_), len(b_)))
            row['firstDiff'] = [k, a_[k:k + 3], b_[k:k + 3]]
        e = [s for s in sts if s['w'] == 'e'][0]; t = [s for s in sts if s['w'] == 't'][0]
        # entry words: indices e.min .. e.top (relative to the rbp the block starts with; a block entered through a
        # kept fall-through starts with the previous block's rbp and delta), deepest first
        lo = e['min']; n_in = e['top'] - lo + 1
        depth_out = t['top'] - lo + 1               # stack items at the terminator, indices lo .. top
        allocdrv.TAB[:] = table
        nbad = 0; ex = []; outcomes = {}; cases = {}
        body = CODE[b:t['pc']]
        cmp_ops = {0x10: 'LT', 0x11: 'GT', 0x14: 'EQ', 0x09: 'MULMOD', 0x15: 'ISZERO'}
        for i in range(NS):
            entry = [ra['words'](rnd, 'X', 0) for _ in range(n_in)]
            tag = 'random'
            if i % 3 == 1 and n_in:
                # edge case for a comparison of the block: rewrite the entry word one compared word copies
                pre, bd = evm_block(b, t['pc'], entry)
                ops = [x for x in trace_ops(pre, bd, (0x10, 0x11, 0x14)) ]
                if ops:
                    pc_, op, a, bb = rnd.choice(ops)
                    which = rnd.randrange(2); src = (a, bb)[which]; other = (a, bb)[1 - which]
                    if src in entry:
                        k = entry.index(src)
                        mode = rnd.choice(['eq', 'plus1', 'minus1', 'tophigh', 'zero'])
                        new = {'eq': other, 'plus1': (other + 1) & M, 'minus1': (other - 1) & M,
                               'tophigh': (other & (M64 << 192)) | rnd.getrandbits(192), 'zero': 0}[mode]
                        entry[k] = new; tag = '%s@%x/%s' % (cmp_ops.get(op, op), b + pc_, mode)
            if i % 3 == 2 and n_in:
                # MULMOD remainder zero: set the multiplicand to a multiple of the modulus where the modulus is a copy
                pre, bd = evm_block(b, t['pc'], entry)
                code = pre + bd + b'\x00'; w = pyevm.World({0xaa: code}); w.trace = []; w.trace_stack = 3; w.call(1, 0xaa, 0, b'', False, 0)
                mm = [(pc - len(pre), stk) for d, pc, op, stk in w.trace if pc >= len(pre) and op == 0x09]
                if mm:
                    pc_, stk = mm[0]; x, y, mod = stk[-1], stk[-2], stk[-3]
                    if mod and x in entry:
                        entry[entry.index(x)] = (mod * rnd.choice([0, 1, 2, rnd.getrandbits(64)])) & M; tag = 'MULMOD@%x/remainder-zero-try' % (b + pc_)
                    elif mod and y in entry:
                        entry[entry.index(y)] = (mod * rnd.choice([0, 1, 2, rnd.getrandbits(64)])) & M; tag = 'MULMOD@%x/remainder-zero-try' % (b + pc_)
            pre, bd = evm_block(b, t['pc'], entry)
            ref = run_ref(pre, bd, depth_out)            # top first
            if kind in ('Jump', 'JumpI') and ref[0] in entry and rnd.random() < 0.8:
                # the jump destination is a copy of an entry word: make it a JUMPDEST most of the time
                entry[entry.index(ref[0])] = rnd.choice(JD)
                pre, bd = evm_block(b, t['pc'], entry); ref = run_ref(pre, bd, depth_out)
            refw = {t['top'] - k: v for k, v in enumerate(ref)}
            # terminator decision by EVM semantics
            if kind == 'JumpI': rdec = term.world_call(refw[t['top'] - 1], refw[t['top']]); npop = 2
            elif kind == 'Jump': rdec = term.world_call(1, refw[t['top']]); npop = 1
            else: rdec = 'fall'; npop = 0
            init = []
            have = {el['i'] for el in e['elems']}
            for ix in range(lo, e['top'] + 1):
                if ix not in have: init.append((entry[ix - lo], {'stack': ix}))
            for el in e['elems']:
                d = {}
                if 'so' in el: d['stack'] = el['so'][0]
                if 'gen' in el: d['gen'] = el['gen']
                if 'avx' in el: d['avx'] = el['avx']
                if 'lit' in el: raise Stop('literal in entry state')
                init.append((entry[el['i'] - lo], d))
            flags = tuple(rnd.getrandbits(1) for _ in range(4))
            ss0 = 300 + rnd.randrange(50)
            try:
                c, ex_, rbp, SP = term.run_stream(rod, seq, init, rnd, flags, ss0)
            except Stop as er:
                nbad += 1; ex.append({'run': i, 'stop': str(er)}); break
            out['runs'] += 1
            nat = {'block': lambda: ('jump', ex_[1]), 'table': lambda: ('jump', ex_[1]), 'error': lambda: 'invalid', 'epilogue': lambda: 'halt', 'fall': lambda: 'fall'}[ex_[0]]()
            outcomes[repr(nat)] = outcomes.get(repr(nat), 0) + 1
            cases[tag.split('@')[0] + ('/' + tag.split('/')[-1] if '/' in tag else '')] = cases.get(tag.split('@')[0] + ('/' + tag.split('/')[-1] if '/' in tag else ''), 0) + 1
            bad = []
            if nat != rdec: bad.append(('successor', repr(nat), repr(rdec)))
            keep = tm.m.c.read(E + 0x3e0, 1)
            live = range(lo, t['top'] - npop + 1)
            if nat == 'fall' and kind == 'JumpI' and keep:
                for el in t['elems'][:len(t['elems']) - npop]:
                    d = {k2: v2 for k2, v2 in tm.m.loc(tm.ids[el['id']]).items() if k2 in ('gen', 'avx', 'stack')}
                    for where, got in rs['word_at'](c, d).items():
                        if got != refw[el['i']]: bad.append(('kept', el['i'], where, hex(got), hex(refw[el['i']])))
            elif nat in ('invalid', 'halt'):
                pass
            else:
                for ix in live:
                    got = term.word(c, rbp, ix)
                    if got != refw[ix]: bad.append(('final', ix, hex(got), hex(refw[ix])))
                if c.r['rbp'] != (rbp + 32 * t['delta']) & M64: bad.append(('rbp', c.r['rbp'] - rbp, 32 * t['delta']))
            if bad:
                nbad += 1
                if len(ex) < 12: ex.append({'run': i, 'tag': tag, 'entry': [hex(x) for x in entry], 'bad': bad[:4]})
        row.update({'sets': NS, 'badRuns': nbad, 'outcomes': outcomes, 'cases': cases, 'examples': ex})
        fl = row['stream'] != 'equal' or nbad > 0
        row['flagged'] = fl; out['flagged'] += int(fl); out['badRuns'] += nbad
        out['blocks'].append(row)
        print(row['block'], kind, row['stream'], row.get('firstDiff'), 'stackOpCode', len(nocode_with_code), nbad, outcomes, cases, (ex or [''])[:1], flush=True)
    out['seconds'] = round(time.time() - t0, 1)
    name = 'block%s%s%s.json' % ('-' + FAULT if FAULT else '', ('-' + only.replace(',', '_')) if only else '', ('-s%d' % SEED) if os.environ.get('SEEDX') else '')
    json.dump(out, open(os.path.join(OUTD, name), 'w'), indent=1)
    print(name, {k: v for k, v in out.items() if k != 'blocks'})


main()
