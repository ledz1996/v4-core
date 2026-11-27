"""Find 256-entry instruction tables in a reth-family binary, read as data: arrays of 256 relocated pointers where
the undefined opcodes share one handler and the 25 arithmetic slots hold distinct handlers. Nothing is executed.
usage: python3 -I findtab.py <rel.txt> <out.json>"""
import json, sys
rel = {}
for l in open(sys.argv[1]):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
UNDEF = [0x0c, 0x0d, 0x0e, 0x0f, 0x21, 0x22, 0x2f, 0xa5, 0xa6, 0xb0, 0xc0]
ARITH = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d]
out = []
for a in sorted(rel):
    fns = [rel.get(a + 8 * i) for i in range(256)]
    if None in fns: continue
    if len({fns[i] for i in UNDEF}) != 1: continue
    if len({fns[i] for i in ARITH}) != 25: continue
    if fns[ARITH[0]] == fns[UNDEF[0]]: continue
    out.append({'table': hex(a), 'distinct': len(set(fns)), 'arith': {hex(i): hex(fns[i]) for i in ARITH},
                'undef': hex(fns[0x0c]), 'stop': hex(fns[0]), 'jump': hex(fns[0x56]), 'jumpi': hex(fns[0x57])})
json.dump(out, open(sys.argv[2], 'w'), indent=1)
groups = {}
for t in out: groups.setdefault(tuple(t['arith'].values()), []).append(t['table'])
print(len(out), 'tables;', len(groups), 'distinct arithmetic handler sets')
for g, ts in groups.items(): print(ts[0], len(ts), 'ADD', g[0], 'MULMOD', g[8])
