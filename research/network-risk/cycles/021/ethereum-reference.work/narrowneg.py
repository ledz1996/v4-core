"""Vectors for lead L-940: operands that are negative narrow integers (i8 to i128) in both their
correct 256 bit two's complement image and the zero-extended image that the released ruint
wrapping_from fault would produce, fed to the signed opcodes and the ones the tick math uses.
Reuses the battery dispatcher and reference semantics. Read-only eth_call with state override.
Usage: python3 narrowneg.py <out.json> <pseudo ids comma list>"""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/021/ethereum-reference.work')
import battery
from evm import MASK

M = 1 << 256
vals = set()
rnd = random.Random(940)
for w in (8, 16, 24, 32, 64, 128):
    for x in [-1, -2, -(1 << (w - 1)), -(1 << (w - 1)) + 1, -3, -887272, -887273, -60, -200, -16384] + [-rnd.randrange(1, 1 << (w - 1)) for _ in range(6)]:
        if -(1 << (w - 1)) <= x < 0:
            vals.add(x % M)                 # correct image
            vals.add(x % (1 << w))          # zero-extended image of the faulty conversion
for x in [1, 2, 3, 60, 200, 887272, 16384, 255, 1 << 63, (1 << 64) - 1]:
    vals.add(x)
vals = sorted(vals)
V = []
for a in vals:
    for b in vals[::3]:
        for op in ('SDIV', 'SMOD', 'SLT', 'SGT', 'SAR', 'SIGNEXTEND', 'ADD', 'SUB', 'MUL'):
            if op == 'SAR':
                V.append((op, rnd.choice([0, 1, 7, 8, 63, 64, 127, 128, 255, 256]), a, 0))
            elif op == 'SIGNEXTEND':
                V.append((op, rnd.choice([0, 1, 2, 3, 7, 15, 30, 31, 32]), a, 0))
            else:
                V.append((op, a, b, 0))
for a in vals:
    V.append(('SIGNEXT_CHAIN', a, rnd.randrange(0, 256), 0))
print(len(vals), 'values', len(V), 'vectors')
code = battery.dispatcher()
import evm
out = sys.argv[1]; ids = set(map(int, sys.argv[2].split(',')))
import altrun_eps
res = []
for cid, name, url in altrun_eps.ALT:
    if cid not in ids: continue
    done, bad, errors = battery.run(url, code, V, size=400)
    print(cid, name, 'ran', done, '/', len(V), 'mismatches', len(bad), 'errors', len(errors), errors[:1])
    res.append({'id': cid, 'name': name, 'rpc': url, 'vectors': len(V), 'ran': done, 'mismatches': bad[:50], 'mismatchCount': len(bad), 'errors': errors[:5]})
json.dump({'vectors': len(V), 'values': len(vals), 'results': res}, open(out, 'w'), indent=1)
