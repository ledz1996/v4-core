"""Per-function comparison inside the emitter closures: which functions pass different asmjit ids, and the
asmjit method names (mnemonics) carried as template arguments in the mangled names of each closure.
usage: python3 -I emitper.py <package.s> <harness.s> <out.json>"""
import sys, re, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emitcmp as E
P, H = E.parse(sys.argv[1]), E.parse(sys.argv[2])
allp, allh = set(), set()
for r in E.ROOTS:
    k = 'monad::vm::compiler::native::Emitter::' + r
    allp |= E.closure(P, k); allh |= E.closure(H, k)
both = sorted(allp & allh)
diff = []
for f in both:
    if P[f]['ids'] != H[f]['ids']:
        diff.append({'function': f, 'onlyPackage': sorted(map(hex, P[f]['ids'] - H[f]['ids'])), 'onlyHarness': sorted(map(hex, H[f]['ids'] - P[f]['ids'])), 'esiUnknownHarness': H[f]['esi_unknown'], 'esiUnknownPackage': P[f]['esi_unknown']})
def mnems(funcs, cl):
    seq = set()
    for f in cl:
        for r in funcs[f]['refs'] | {f}:
            for m in re.finditer(r'adL_ZN(?:S[0-9A-Z]*_|N[^E]*E|[0-9A-Za-z_]*?E)(\d+)', r):
                n = int(m.group(1)); s = r[m.end():m.end() + n]
                seq.add(s)
    return seq
mn = {}
for r in E.ROOTS:
    k = 'monad::vm::compiler::native::Emitter::' + r
    a, b = mnems(P, E.closure(P, k)), mnems(H, E.closure(H, k))
    mn[r] = {'equal': a == b, 'package': sorted(a), 'harness': sorted(b)}
json.dump({'onlyInPackageClosures': sorted(allp - allh), 'onlyInHarnessClosures': sorted(allh - allp), 'inBoth': len(both), 'idDiffs': diff, 'templateMnemonics': mn}, open(sys.argv[3], 'w'), indent=1)
print('both', len(both), 'onlyP', len(allp - allh), 'onlyH', len(allh - allp))
for d in diff: print(d)
for r, v in mn.items(): print(r, v['equal'], v['package'] if not v['equal'] else len(v['package']), v['harness'] if not v['equal'] else '')
