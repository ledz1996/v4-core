"""For each named function of a lifted profile in binary A, find the most similar function (normalised
instruction sequence, difflib ratio) among the functions reachable from the storage handlers of all tables of B and
the journal routines of B. Reads only (objdump text).
usage: python3 -I match_fns.py <binA> <relA> <fdeA> <tableA> <binB> <relB> <fdeB> <tableB> <out.json> name=hex..."""
import difflib, json, sys, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/035/theme-reth-journal-binary-lift.work/scripts')
import cmp_journal as cj
A = cj.load(*sys.argv[1:5]); B = cj.load(*sys.argv[5:9]); OUT = sys.argv[9]
names = dict(x.split('=') for x in sys.argv[10:])
tb = cj.tables(B)
roots = [B['rel'][t + 8 * o] for t in tb for o in (0x54, 0x55, 0x5c, 0x5d)]
extra = [int(x, 16) for x in os.environ.get('EXTRA_B', '').split(',') if x]
fs = cj.walk(B, roots + extra, depth=4)
res = {}
for nm, hx in names.items():
    a = cj.fn(A, int(hx, 16)); ba = cj.body(A, a[0])
    best = []
    for lo, bb in fs.items():
        if abs(bb['n'] - ba['n']) > max(40, ba['n'] // 3): continue
        sm = difflib.SequenceMatcher(a=ba['ins'], b=bb['ins'], autojunk=False)
        eq = sum(m.size for m in sm.get_matching_blocks())
        best.append((eq / max(len(ba['ins']), len(bb['ins'])), lo, eq, bb['n']))
    best.sort(reverse=True)
    res[nm] = {'A': hex(a[0]), 'nA': ba['n'], 'best': [(round(r, 4), hex(lo), eq, n) for r, lo, eq, n in best[:3]]}
    print(nm, res[nm])
json.dump(res, open(OUT, 'w'), indent=1)
