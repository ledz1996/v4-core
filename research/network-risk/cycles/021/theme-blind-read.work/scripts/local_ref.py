"""Run probe C in the review's reference interpreter (tools/opdiff/pyevm.py) with the build of this checkout."""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
sys.path.insert(0, os.path.join(here, '..', '..', '..', '..', 'tools', 'opdiff'))
import pyevm
from static_rollback import probe, PR
from xtx import driver, TOKEN, D, X, FROM
b = json.load(open(os.path.join(here, '..', '..', '..', '..', 'build', 'PoolManager.json')))
PM = 0x00000000000000000000000000000000b11d0aaa
rt = bytearray(bytes.fromhex(b['runtime'].removeprefix('0x')))
for refs in b['immutableReferences'].values():
    for r in refs: rt[r['start']:r['start'] + r['length']] = PM.to_bytes(32, 'big')
code, labels, exp = probe(PM)
w = pyevm.World({PM: bytes(rt), PR: code, D: driver(PM), X: TOKEN})
ok, ret = w.call(FROM, PR, 0, b'', False, 0)
print(ok, len(ret))
got = [int.from_bytes(ret[32*i:32*i+32], 'big') for i in range(len(labels))]
for l, e, g in zip(labels, exp, got): print('OK ' if e == g else 'BAD', l, hex(g))
