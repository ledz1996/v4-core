"""Task 5: planted faults in in-memory copies of the model text (never in the files). Each fault is located by
pattern inside one function of the shipped binary's disassembly and replaced there; the run must then report
mismatches or model errors.

Transient faults (tsgo.py targets):
  skip_journal    the call that appends the transientStorageChange (journal.append / appendJournal) in
                  SetTransientState becomes a nop
  snap_off_by_one the exit test of the journal revert loop admits one entry fewer (jg->jge, jl->jle, b.gt->b.ge,
                  b.lt->b.le): the entry at the snapshot index is not undone
  key_limb        the first byte swap of the TLOAD key in opTload becomes a nop: one 64-bit limb of the key keeps
                  the stack word's little-endian order
  revert_zero     after the zero-value test (memequal against zero) in the revert path, the branch to the store
                  becomes a nop, so every revert deletes the slot (restores zero); not on avax, whose Set has no
                  zero test
Storage faults (stgo.py, bsc): skip_journal (journal.storageChange call in stateObject.SetState), key_limb (first
bswap/rev in opSload), revert_zero (the branch after memequal in (*storageChange).revert, so a revert always takes
the 'value equals origin' delete), dirty_kept (the mapdelete of stateObject.SetState's inlined setState becomes a
nop, so a slot written back to its original value stays dirty).
usage: python3 -I plant.py ts <target> <nseq> <outdir> | st <arch> <nseq> <outdir>
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fn

BR = r'\s(je|jne|cbz|cbnz|tbz|tbnz)\s'


def _patch_in(text, fname, pick, repl):
    b = fn.body(text, fname)
    assert b, fname
    lines = b.splitlines()
    i = pick(lines)
    assert i is not None, (fname, 'no site')
    old = lines[i]
    m = re.match(r'^(\s*[0-9a-f]+:\s+)', old)
    lines[i] = m.group(1) + repl(old[m.end():])
    nb = '\n'.join(lines) + ('\n' if b.endswith('\n') else '')
    return text.replace(b, nb, 1), old.strip()


def first(pat):
    def p(lines):
        for i, l in enumerate(lines):
            if re.search(pat, l):
                return i
    return p


def after(pat1, pat2):
    def p(lines):
        for i, l in enumerate(lines):
            if re.search(pat1, l):
                for j in range(i + 1, min(i + 6, len(lines))):
                    if re.search(pat2, lines[j]):
                        return j
    return p


def nop(_): return 'nop'


def flip(ins):
    for a, b in (('jg ', 'jge '), ('jl ', 'jle '), ('b.gt', 'b.ge'), ('b.lt', 'b.le')):
        if ins.startswith(a):
            return b + ins[len(a):]
    raise ValueError(ins)


SITES = {}


def ts_faults(target):
    par = 'par' in target
    out = {
        'skip_journal': ('(*ParallelStateDB).SetTransientState' if par else '(*StateDB).SetTransientState',
                         first(r'(journal\)\.append|appendJournal)>'), nop),
        'snap_off_by_one': ('(*ParallelStateDB).RevertToSnapshot' if par else '(*journal).revert',
                            (lambda L: [i for i, l in enumerate(L) if re.search(r'\s(jl|b\.lt)\s', l)][0]) if par else
                            first(r'\s(jg|b\.gt)\s'), flip),
        'key_limb': ('core/vm.opTload', first(r'\s(bswap|rev)\s'), nop),
    }
    if not target.startswith('avax'):
        out['revert_zero'] = ('(*parallelJournalEntry).revert' if par else '(*transientStorageChange).revert',
                              after(r'memequal', BR), nop)
    return out


ST_FAULTS = {
    'skip_journal': ('(*stateObject).SetState', first(r'journal\)\.storageChange>'), nop),
    'key_limb': ('core/vm.opSload', first(r'\s(bswap|rev)\s'), nop),
    'revert_zero': ('(*storageChange).revert', after(r'memequal', BR), nop),
    'dirty_kept': ('(*stateObject).SetState', first(r'mapdelete>'), nop),
}


def patcher(spec, log):
    fname, pick, repl = spec
    def p(text):
        t, old = _patch_in(text, fname, pick, repl)
        log.append({'function': fname, 'replaced': old})
        return t
    return p


def main():
    kind, tgt, n, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    os.makedirs(outdir, exist_ok=True)
    import json
    summary = []
    if kind == 'ts':
        import tsgo
        for f, spec in ts_faults(tgt).items():
            log = []
            r = tsgo.run(tgt, n, os.path.join(outdir, '%s-%s.json' % (tgt, f)), text_patch=patcher(spec, log), fault=f)
            summary.append({'target': tgt, 'fault': f, 'site': log, 'sequences': r['sequences'],
                            'mismatchSeqs': len(r['mismatches']), 'errorSeqs': len(r['errors'])})
    else:
        import stgo
        for f, spec in ST_FAULTS.items():
            log = []
            r = stgo.run(tgt, n, os.path.join(outdir, 'bsc-%s-%s.json' % (tgt, f)), text_patch=patcher(spec, log), fault=f)
            summary.append({'target': 'bsc-' + tgt, 'fault': f, 'site': log, 'sequences': r['sequences'],
                            'mismatchSeqs': len(r['mismatches']), 'errorSeqs': len(r['errors'])})
    json.dump(summary, open(os.path.join(outdir, 'summary-%s-%s.json' % (kind, tgt)), 'w'), indent=1)
    for s in summary:
        print(s)


if __name__ == '__main__':
    main()
