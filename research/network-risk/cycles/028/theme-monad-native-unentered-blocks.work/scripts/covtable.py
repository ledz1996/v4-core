"""Cycle 28 Task 1: one coverage table of the PoolManager's compiled IR blocks per Monad tag, entered or not in
native code by each case set. Sets: c25 (1,533 cases, cycle 27 out/c25-all-cov/cov.tgz unpacked to out/c25cov),
c26 (575 cases, out/c26cov), seq (d40 and d300, run here, out/seqcov), c27 (530 cases of cycles/027/
theme-never-run-math-sides.work/out/cases27.json, run here, out/c27cov), plus any extra dirs named on the command line
(cycle 28 cases). Output out/covtable-<ver>.json. Usage: python3 covtable.py [name=dir ...]"""
import sys, os, glob, json
import blocks as B
W = B.WORK
SETS = {'c25': 'out/c25cov/cov', 'c26': 'out/c26cov/cov', 'seq': 'out/seqcov/cov', 'c27': 'out/c27cov/cov'}
for a in sys.argv[1:]: k, v = a.split('='); SETS[k] = v
diff = json.load(open(os.path.join(W, '..', '..', '027', 'theme-monad-engine-agreement.work', 'out', 'asm-blockdiff.json')))
changed = {int(d['block'], 16) for d in diff['differ']}
for ver in ('0.16.5', '0.16.7'):
    ref = None; per = {}; nfiles = {}; en = None
    for k, d in SETS.items():
        hit = set(); n = 0
        for p in sorted(glob.glob(os.path.join(W, d, f'{ver}-*.cov'))):
            offs = B.block_offsets(p)
            if ref is None: ref = offs; en = B.enterable(p)
            assert offs == ref, p
            hit |= B.entered(p); n += 1
        per[k] = hit; nfiles[k] = n
    sp = B.block_spans(ref); rows = []
    for o in ref:
        src = B.block_src(sp[o])
        rows.append({'block': hex(o), 'enterable': en[o], 'changed167': o in changed,
                     'entered': {k: (o in per[k]) for k in SETS}, 'any': any(o in per[k] for k in SETS),
                     'src': [f'{r[0]}:{r[1]}' + (f'-{r[2]}' if r[2] != r[1] else '') for r in src][:6]})
    out = {'ver': ver, 'blocks': len(ref), 'files': nfiles, 'sets': SETS,
           'enteredBySet': {k: len(per[k]) for k in SETS}, 'enteredAny': sum(r['any'] for r in rows),
           'notEntered': [r['block'] for r in rows if not r['any']],
           'changedNotEntered': [r['block'] for r in rows if r['changed167'] and not r['any']], 'rows': rows}
    json.dump(out, open(os.path.join(W, 'out', f'covtable-{ver}.json'), 'w'), indent=0)
    print(ver, out['blocks'], out['files'], out['enteredBySet'], 'any', out['enteredAny'], 'not', len(out['notEntered']),
          'changedNot', len(out['changedNotEntered']))
