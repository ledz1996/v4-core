"""Cycle 33, Task 3: the memory, storage, hashing, log, context and SIGNEXTEND sites of the 128 un-entered value
blocks. Where the gcc 15.2.0 build has a standalone emit function, it runs whole in the x86 model on the logged state
(cycle 31 states.jsonl), with the limb table the clang listing shows for the block (read as in block.py by running
the block's sites in order), and its asmjit stream is compared with the clang listing group of the same pc under
term.strict (exact displacements and immediates):
  SIGNEXTEND Emitter::signextend() 0x388440      CALLDATALOAD Emitter::calldataload() 0x3936a0
  CALLER Emitter::caller() 0x36fe10              RETURNDATASIZE Emitter::returndatasize() 0x370480
  MLOAD Emitter::mload<Version 0/1> 0x3a9fa0 / 0x3a9780    MSTORE Emitter::mstore<Version 0/1> 0x3a9dc0 / 0x3a95a0
KECCAK256, SLOAD, SSTORE, TLOAD and LOG2 to LOG4 are emitted by the traits templates sha3<>, sload<>, sstore<>, tload<>,
log<N><> that the gcc build inlines into compile_basic_blocks<traits>; they have no standalone function and are listed
as not run. For every call in a stream the instructions before it are recorded (spills of live general and vector
registers, argument registers). SIGNEXTEND sites also run on operand sets in the model and are compared with pyevm.py.
usage: python3 -I task3.py <outdir> <nw>"""
import sys, os, json, random, re, time
OUTD = sys.argv[1]; NW = int(sys.argv[2])
sys.argv = [sys.argv[0], OUTD, '0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import term
from term import ra, rs, g, allocdrv, x86emu, Stop, emdrv, helpers, pyevm, S, E, CODE, JD, M, M64, opname, STATES
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'block.py')).read().replace('\nmain()\n', '\n')
bk = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'block.py'), '__name__': 'bk'}
sys.argv = [sys.argv[0], OUTD, '0']
exec(compile(src, 'block.py', 'exec'), bk)
SEED = 3335
# MSTORE of a literal word allocates a literal element: run Stack::alloc_literal (0x3ad360) from the package text
# instead of the cycle 30 stub that stops
term.STOPS.discard(0x3ad360)
if 0x3ad360 not in ra['clos']: ra['clos'].append(0x3ad360)
_build = ra['build']
TOUCH = [None]
def _build2(*a, **k):
    m, ids, info = _build(*a, **k); m.c.externs.pop(0x3ad360, None)
    if TOUCH[0] is not None:
        # StackElem::touched_memory_size_ (RcObject block +0x80, read at touch_memory<V> 0x395694), which the
        # cycle 31 hook does not log
        m.c.write(ids[a[1]['elems'][-1]['id']] + 0x80, 4, TOUCH[0])
    return m, ids, info
ra['build'] = _build2
FNS = {'SIGNEXTEND': [0x388440], 'CALLDATALOAD': [0x3936a0], 'CALLER': [0x36fe10], 'RETURNDATASIZE': [0x370480],
       'MLOAD': [0x3a9fa0, 0x3a9780], 'MSTORE': [0x3a9dc0, 0x3a95a0]}
INLINED = ['KECCAK256', 'SLOAD', 'SSTORE', 'TLOAD', 'LOG2', 'LOG3', 'LOG4']


def main():
    rnd = random.Random(SEED)
    ops = json.load(open(term.C31 + '/out/value128-ops.json'))['blocks']
    want = {int(k, 16) for k in ops}
    out = {'seed': SEED, 'sites': [], 'byKind': {}, 'inlinedNotRun': {}}
    t0 = time.time()
    # the limb table each site starts with: thread the block from the default table (block.py found the default
    # entry table right for the mulDiv blocks; here every block starts from it and the stream comparison shows
    # whether that holds)
    only = os.environ.get('ONLY')
    for b in sorted(want):
        if only and hex(b) not in only.split(','): continue
        sts = [s for s in STATES if s['b'] == b]
        lst = bk['block_listing'](b); grp = bk['site_lines'](lst)
        sites_cb = {}
        for c_, ls in grp:
            mm = re.match(r'^//\s+(0x[0-9a-f]+):', c_)
            if mm: sites_cb[int(mm.group(1), 16)] = ls
        tab = term.TermModel('Jump', [s for s in sts if s['w'] == 't'][0], {}).m.table()
        for s in sts:
            if s['w'] != 'i': continue
            k = opname(s['pc'])
            if k in INLINED:
                out['inlinedNotRun'][k] = out['inlinedNotRun'].get(k, 0) + 1
            emitter = k in bk['EMIT'] or k in FNS
            if not emitter: continue
            if k in FNS:
                row = {'block': hex(b), 'pc': hex(s['pc']), 'op': k}
                if k == 'SIGNEXTEND': row['literalIndex'] = 'lit' in s['elems'][-1]
                cb = sites_cb.get(s['pc'], [])
                res = None
                for fn in FNS[k]:
                    bk['EMIT'][k] = fn
                    try: m = bk['emit_site'](k, s, {}, tab)
                    except Stop as e:
                        row.setdefault('stops', []).append('%x: %s' % (fn, e)); continue
                    gl = term.text_lines(m.emitted)
                    eq = term.strict(gl) == term.strict(cb)
                    if res is None or eq: res = (fn, m, gl, eq)
                    if eq: break
                if res is None:
                    out['sites'].append(row); continue
                fn, m, gl, eq = res
                if not eq:
                    nt = term.derive_rows([l for l in gl if not l.endswith(':')], [l for l in cb if not l.endswith(':')], tab)
                    if nt:
                        m2 = bk['emit_site'](k, s, {}, nt); gl2 = term.text_lines(m2.emitted)
                        if term.strict(gl2) == term.strict(cb): m, gl, eq = m2, gl2, True; row['tableFromListing'] = nt
                if not eq and k in ('MLOAD', 'MSTORE'):
                    TOUCH[0] = 32
                    try:
                        m2 = bk['emit_site'](k, s, {}, tab); gl2 = term.text_lines(m2.emitted)
                        if term.strict(gl2) == term.strict(cb): m, gl, eq = m2, gl2, True; row['touchedMemorySizeFromListing'] = 32
                    finally: TOUCH[0] = None
                row.update({'fn': hex(fn), 'stream': 'equal' if eq else 'different', 'gccStream': gl, 'clangStream': cb})
                calls = []
                for i, l in enumerate(gl):
                    if l.startswith('call'):
                        calls.append({'call': l, 'before': gl[max(0, i - 8):i]})
                row['calls'] = calls
                if k == 'SIGNEXTEND' and eq:
                    # value runs: every live word after the emit against pyevm.py
                    nmis = 0; exs = []
                    args_e = s['elems'][-2:][::-1]
                    ids, info = m._ids, m._info
                    tix = rs['s32'](m.c.read(S + 8, 4))
                    rb = m.c.read(m.c.read(S + 0x158, 8) + 8 * tix, 8) if tix >= 0 else m.c.read(m.c.read(S + 0x140, 8) + 8 * (-tix - 1), 8)
                    post = m.loc(rb)
                    for i in range(NW):
                        w = {}
                        for kk, bb in ids.items():
                            e = info[kk]; w[bb] = int(e['lit'], 16) if 'lit' in e else rnd.choice([rnd.getrandbits(256), rnd.getrandbits(8), (1 << rnd.randrange(256)), M, 0, rnd.randrange(40)])
                        init = []
                        for kk in ids:
                            d = {}
                            for k2, v2 in (('gen', info[kk].get('gen')), ('avx', info[kk].get('avx')), ('stack', info[kk]['so'][0] if 'so' in info[kk] else None)):
                                if v2 is not None: d[k2] = v2
                            init.append((w[ids[kk]], d))
                        allocdrv.TAB[:] = m._tabpre
                        c = helpers.run_seq_calls(m, m.emitted, init, rnd)
                        allocdrv.TAB[:] = m.table()
                        argv = [w[ids[e['id']]] for e in args_e]
                        exp = ra['evm'](0x0b, argv)
                        d = {k2: v2 for k2, v2 in post.items() if k2 in ('gen', 'avx', 'stack')}
                        for where, got in rs['word_at'](c, d).items():
                            if got != exp:
                                nmis += 1
                                if len(exs) < 5: exs.append({'args': [hex(x) for x in argv], 'where': where, 'got': hex(got), 'want': hex(exp)})
                    row.update({'runs': NW, 'mismatchRuns': nmis, 'examples': exs})
                out['sites'].append(row)
                kk = out['byKind'].setdefault(k, {'sites': 0, 'equal': 0, 'different': 0, 'calls': 0, 'runs': 0, 'mismatchRuns': 0})
                kk['sites'] += 1; kk['equal' if eq else 'different'] += 1; kk['calls'] += len(calls)
                kk['runs'] += row.get('runs', 0); kk['mismatchRuns'] += row.get('mismatchRuns', 0)
                print(row['block'], row['pc'], k, row.get('fn'), row.get('stream'), len(calls), row.get('mismatchRuns'), row.get('stops'), flush=True)
                m_next = m
            else:
                m_next = bk['emit_site'](k, s, {}, tab)
            tab = m_next.table()
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(OUTD, 'task3.json'), 'w'), indent=1)
    print(json.dumps(out['byKind']), out['inlinedNotRun'])


main()
