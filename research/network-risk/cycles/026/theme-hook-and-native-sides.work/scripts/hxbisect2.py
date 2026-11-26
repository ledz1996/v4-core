"""Same scenario (afterInitialize-only hook flag, afterInitialize returns L bytes, one initialize action) with different
token addresses, to see whether the Monad harness engine difference depends on the addresses or on the returned length.
Usage: python3 hxbisect2.py <outdir>"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common26 as C
argv = sys.argv; sys.argv = [argv[0], '/dev/null']
import cases26 as K
sys.argv = argv
od = sys.argv[1]; os.makedirs(od, exist_ok=True)
aI = K.HSEL['afterInitialize']; var = []
for L in (0, 1, 4, 32):
    for t in range(8):
        c = K.pool(30000 + 37 * t, K.F['afterInitialize']); c['id'] = len(var); c['tag'] = f'len{L} tok{t}'
        acts = K.std_acts(c)[:1]; c['nact'] = 1; c['p'] = C.build_p([(0, aI, 1, K.ret(aI, 0, length=L))], acts); var.append(c)
json.dump({'cases': var}, open(os.path.join(od, 'cases.json'), 'w'))
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'hxrun26.py'), os.path.join(od, 'cases.json'), od], check=True, capture_output=True)
r = json.load(open(os.path.join(od, 'hx-results.json')))['0.16.7']
for L in (0, 1, 4, 32):
    print(L, ''.join(str(r[str(c['id'])]['native']['ok']) for c in var if c['tag'].startswith(f'len{L} ')),
          ''.join(str(r[str(c['id'])]['interp']['ok']) for c in var if c['tag'].startswith(f'len{L} ')))
