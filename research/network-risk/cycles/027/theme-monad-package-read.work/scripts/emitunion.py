"""Union over every function of monad::vm::compiler (both builds) of the asmjit instruction ids passed as an
immediate, of large immediates (masks and constants), and of functions whose id is not an immediate.
Ids are named from the InstId enum of asmjit e8c8e2e4 (out/asmjit-instid-e8c8e2e4.json).
usage: python3 -I emitunion.py <package.s> <harness.s> <names.json> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emitcmp as E
nm = {int(k, 16): v for k, v in json.load(open(sys.argv[3])).items()}
res = {}
U = {}
for tag, path in (('package', sys.argv[1]), ('harness', sys.argv[2])):
    F = E.parse(path)
    ids, consts, unk = set(), set(), []
    for k, f in F.items():
        if not k.startswith('monad::vm::compiler::'): continue
        ids |= f['ids']; consts |= f['consts']
        if f['esi_unknown']: unk.append((k, f['esi_unknown']))
    U[tag] = (ids, consts, unk)
pi, pc, pu = U['package']; hi, hc, hu = U['harness']
res = {'idsPackage': len(pi), 'idsHarness': len(hi),
       'idsOnlyPackage': [(hex(i), nm.get(i)) for i in sorted(pi - hi)], 'idsOnlyHarness': [(hex(i), nm.get(i)) for i in sorted(hi - pi)],
       'idsBoth': [(hex(i), nm.get(i)) for i in sorted(pi & hi)],
       'constsOnlyPackage': [hex(c) for c in sorted(pc - hc)], 'constsOnlyHarness': [hex(c) for c in sorted(hc - pc)], 'constsBoth': [hex(c) for c in sorted(pc & hc)],
       'idNotImmediatePackage': pu, 'idNotImmediateHarness': hu}
json.dump(res, open(sys.argv[4], 'w'), indent=1)
for k, v in res.items():
    print(k, v if not isinstance(v, list) or len(v) < 60 else '%d items' % len(v))
