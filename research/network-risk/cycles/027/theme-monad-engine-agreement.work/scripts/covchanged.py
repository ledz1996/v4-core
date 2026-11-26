"""Cycle 27: which of the PoolManager blocks whose emitted code differs between v0.16.5 and v0.16.7
(out/asm-blockdiff.json) were entered by the native code in the fixed-harness coverage runs (cov files written by
build/<ver>/hxfcov through cov.hpp of cycle 23). Usage: python3 covchanged.py <out.json> <cov dir> [...]"""
import sys, glob, json, collections
diff = json.load(open('out/asm-blockdiff.json'))
changed = {int(d['block'], 16): d.get('tags', []) for d in diff['differ']}
res = {}
for ver in ('0.16.5', '0.16.7'):
    entered = set(); nfiles = 0; nblocks = None
    for d in sys.argv[2:]:
        for p in glob.glob(f'{d}/{ver}-case*.cov'):
            B = []; nfiles += 1
            for line in open(p):
                t = line.split()
                if t[0] == 'B': B.append(int(t[2]))
                elif t[0] == 'L' and t[3] == '1' and t[4] == '1': entered.add(B[int(t[2])])
            nblocks = len(B)
    hit = sorted(o for o in changed if o in entered)
    tagc = collections.Counter(t for o in hit for t in changed[o])
    res[ver] = {'covFiles': nfiles, 'irBlocks': nblocks, 'blocksEntered': len(entered), 'changedBlocks': len(changed),
                'changedEntered': len(hit), 'changedEnteredByTag': dict(tagc),
                'changedNotEntered': [hex(o) for o in sorted(changed) if o not in entered]}
    print(ver, {k: v for k, v in res[ver].items() if k != 'changedNotEntered'}, 'not entered:', len(res[ver]['changedNotEntered']))
json.dump(res, open(sys.argv[1], 'w'), indent=1)
# The cov directories were packed into out/c26-all-cov/cov.tgz and out/c25-all-cov/cov.tgz after out/cov-changed.json
# was written; unpack them before rerunning.
