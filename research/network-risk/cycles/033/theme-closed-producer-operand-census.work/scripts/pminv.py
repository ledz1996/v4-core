"""Inventory of the PoolManager runtime instructions with opcodes of the census, each mapped to src/ via the solc source map
of the build (cycles/012/theme-bytecode-coverage.work/srcmap.py, which reads build-srcmap.json; its runtime equals build/PoolManager.json)."""
import sys, json, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap
from classes import OPS
inv = []
for pc in srcmap.starts:
    if srcmap.PC2I[pc] >= srcmap.NCODE: break
    op = srcmap.code[pc]
    if op in OPS:
        inv.append({'pc': pc, 'op': OPS[op], 'opn': op, 'src': srcmap.loc(pc)})
json.dump(inv, open(sys.argv[1], 'w'), indent=0)
import collections
print(len(inv), collections.Counter(x['op'] for x in inv))
