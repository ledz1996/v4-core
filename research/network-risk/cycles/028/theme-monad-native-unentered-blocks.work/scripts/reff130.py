"""Cycle 28 Task 2: pyevm.py (tools/opdiff, unmodified) reference for the cases that entered the native blocks of
SqrtPriceMath.sol:52, :97, :105 and Position.sol:94-96 (out/f130-entering.json), one case per fresh world as in
cycles/025/theme-unexecuted-sides.work/scripts/refrun.py. Usage: python3 -I reff130.py <cases.json> <ids> <out.json>"""
import sys, os, json
S25 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '025', 'theme-unexecuted-sides.work', 'scripts'))
sys.path.insert(0, S25)
from common import enc_run, dec_run, codes_for, D, EOA
import pyevm as P
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
cases = {c['id']: c for c in json.load(open(sys.argv[1]))['cases']}
out = {}
for i in [int(x) for x in sys.argv[2].split(',')]:
    c = cases[i]; w = P.World(codes_for(PM, [c]))
    for k, v in c.get('storage', {}).items(): w.storage[(PM, int(k, 16))] = int(v, 16)
    ok, ret = w.call(EOA, D, 0, enc_run([c]), False, 0)
    if not ok: out[str(i)] = {'topFail': ret.hex()}; continue
    uok, words, rv = dec_run(ret)[0]
    out[str(i)] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
json.dump({'pm': hex(PM), 'results': out}, open(sys.argv[3], 'w'))
print(len(out))
