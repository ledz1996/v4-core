"""Narrow the engine difference of the Monad harness on case 46 (afterInitialize returns 0 bytes): variants with fewer
actions, other hook flags and other return lengths, each one world per scenario. Usage: python3 hxbisect.py <outdir>"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common26 as C
argv = sys.argv; sys.argv = [argv[0], '/dev/null']
import cases26 as K
sys.argv = argv
od = sys.argv[1]; os.makedirs(od, exist_ok=True)
var = []
def mk(tag, flags, cfg, nacts, fn_len=None):
    c = K.pool(20000 + len(var), flags); c['id'] = len(var); c['tag'] = tag
    acts = K.std_acts(c)[:nacts]; c['nact'] = len(acts); c['p'] = C.build_p(cfg, acts); var.append(c)
aI = K.HSEL['afterInitialize']; bI = K.HSEL['beforeInitialize']
for n in (1, 2, 5):
    mk(f'ALLF afterInitialize len0 acts={n}', K.ALLF, [(0, aI, 1, b'')], n)
    mk(f'afterInitialize-only flag len0 acts={n}', K.F['afterInitialize'], [(0, aI, 1, b'')], n)
    mk(f'ALLF afterInitialize len32 acts={n}', K.ALLF, [(0, aI, 1, K.ret(aI))], n)
    mk(f'ALLF no cfg acts={n}', K.ALLF, [], n)
    mk(f'ALLF beforeInitialize len0 acts={n}', K.ALLF, [(0, bI, 1, b'')], n)
for L in (0, 1, 4, 31, 32, 33, 64):
    mk(f'afterInitialize-only flag len{L} acts=1', K.F['afterInitialize'], [(0, aI, 1, K.ret(aI, 0, 0, length=L))], 1)
json.dump({'cases': var}, open(os.path.join(od, 'bisect-cases.json'), 'w'))
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'hxrun26.py'), os.path.join(od, 'bisect-cases.json'), od], check=True, capture_output=True)
r = json.load(open(os.path.join(od, 'hx-results.json')))
import pyevm26 as P
pm = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
for c in var:
    w = P.World(C.codes_for(pm, [c]), C.balances_for(pm)); ok, ret = w.call(C.EOA, C.D, 0, C.enc_run([c], pm), False, 0)
    refok = C.dec_run(ret)[0][0]
    row = [c['tag'], 'ref', refok] + [(v, r[v][str(c['id'])]['interp']['ok'], r[v][str(c['id'])]['native']['ok']) for v in r]
    print(row)
