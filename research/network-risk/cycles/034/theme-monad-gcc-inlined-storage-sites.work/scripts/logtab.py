"""Cycle 34 Task 4 (L-1253): rerun cycle 33 term.py, block.py and task3.py with the limb table gpq256_regs_ and every
element's touched_memory_size_ taken from the extended hook log (out/states34.jsonl) at each state, and with every
place that read them from the clang listing disabled (term.derive_rows and realarith derive_table return None, the
task3 touched-memory retry is never reached because the first emission already uses the logged value, and block.py's
table search is not entered unless the stream differs, which is then reported). After each emission inside a block
the model's table must equal the logged table before the next instruction. Outputs go to <outdir>; cycle 33's
directory is only read. usage: python3 -I logtab.py term|block|task3|realarith <outdir> <n>  (TASK4=1 for realarith's realother set)"""
import sys, os, json, types
MODE, OUTD, N = sys.argv[1], sys.argv[2], sys.argv[3]
C = '/home/user/v4-core/research/network-risk/cycles'
C33 = C + '/033/theme-monad-gcc-terminators.work/scripts'
W = C + '/034/theme-monad-gcc-inlined-storage-sites.work'
os.makedirs(OUTD, exist_ok=True)
sys.argv = [sys.argv[0], OUTD, N]
sys.path.insert(0, C33)
src = open(C33 + '/term.py').read()
src = src.replace("MYFN = os.path.join(W, 'out', 'fn')", "MYFN = %r" % (W + '/out/fn'))
src = src.replace("os.path.join(HERE, 'faults33.json')", repr(C33 + '/faults33.json'))
assert src.rstrip().endswith("if __name__ == '__main__':\n    main()")
term = types.ModuleType('term'); term.__file__ = C33 + '/term.py'
body = src      # the module's own guard keeps main() from running here
exec(compile(body, 'term.py', 'exec'), term.__dict__)
sys.modules['term'] = term
ra = term.ra; allocdrv = term.allocdrv
GP = allocdrv.GP
L34 = [json.loads(l) for l in open(W + '/out/states34.jsonl')]
L31 = term.STATES
assert len(L31) == len(L34)
KEY = {}
for a, b in zip(L31, L34): KEY.setdefault((a['b'], a['pc'], a['w'], a['op']), []).append(b)
STATS = {'builds': 0, 'tmWritten': 0, 'tableAfterEmitChecked': 0, 'tableAfterEmitDiffer': []}
_build = ra['build']
def build(kind, st, faults, table=None):
    m, ids, info = _build(kind, st, faults)
    lg = KEY[(st['b'], st['pc'], st['w'], st['op'])]
    assert len(lg) == 1 or all(x['gpq'] == lg[0]['gpq'] for x in lg)
    lg = lg[0]
    for r in range(3):
        for l in range(4): m.c.write(allocdrv.GPQT + 64 * r + 16 * l + 4, 4, lg['gpq'][r][l])
    assert len(lg['elems']) == len(st['elems'])
    for e_old, e_new in zip(st['elems'], lg['elems']):
        assert e_old['i'] == e_new['i'] and e_old.get('ix') == e_new.get('ix')
        if 'id' in e_old and e_new.get('tm'):
            m.c.write(ids[e_old['id']] + 0x80, 4, e_new['tm']); STATS['tmWritten'] += 1
    STATS['builds'] += 1
    m._logstate = lg
    return m, ids, info
ra['build'] = build
term.derive_rows = lambda *a, **k: None
ra['derive_table'] = lambda *a, **k: None
IDX = {id(s): i for i, s in enumerate(L31)}
if MODE == 'term':
    term.main()
elif MODE == 'realarith':
    # cycle 32 realarith.py main (with TASK4=1 in the environment, its realother set), on the logged tables
    ra['NW'] = int(N); ra['OUTD'] = OUTD
    ra['main']()
elif MODE in ('block', 'task3'):
    bsrc = open(C33 + '/block.py').read().replace("os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults33b.json')", repr(C33 + '/faults33b.json'))
    bsrc = bsrc.rstrip()[:-len('main()')]
    bm = {'__file__': C33 + '/block.py', '__name__': 'bm'}
    exec(compile(bsrc, 'block.py', 'exec'), bm)
    _es = bm['emit_site']
    def emit_site(kind, st, faults, table):
        m = _es(kind, st, faults, table)
        i = IDX.get(id(st))
        if i is not None and i + 1 < len(L34):
            nxt = L34[i + 1]; got = m.table(); want = [[GP[x] for x in r] for r in nxt['gpq']]
            STATS['tableAfterEmitChecked'] += 1
            if got != want: STATS['tableAfterEmitDiffer'].append({'block': hex(st['b']), 'pc': hex(st['pc']), 'model': got, 'logged': want})
        return m
    bm['emit_site'] = emit_site
    if MODE == 'block':
        bm['main']()
    else:
        tsrc = open(C33 + '/task3.py').read()
        tsrc = tsrc.replace("src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'block.py')).read().replace('\\nmain()\\n', '\\n')", "src = ''")
        tsrc = tsrc.replace("exec(compile(src, 'block.py', 'exec'), bk)", "bk = bm")
        assert "bk = bm" in tsrc and "src = ''" in tsrc, 'task3 header changed'
        tm_ = {'__file__': C33 + '/task3.py', '__name__': '__main__', 'bm': bm}
        exec(compile(tsrc, 'task3.py', 'exec'), tm_)
json.dump(STATS, open(os.path.join(OUTD, 'logtab-%s-stats.json' % MODE), 'w'), indent=1)
print('logtab', MODE, {k: (v if not isinstance(v, list) else len(v)) for k, v in STATS.items()})
