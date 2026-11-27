"""Lists the SLOAD, SSTORE, TLOAD, TSTORE, CALL family and LOG handlers in the three dispatch tables of each
tempo v1.19.1 binary, from the RELATIVE relocation lists that cycle 28 extracted with readelf.
usage: python3 -I handlers.py <cycle28 build dir> <out.json>"""
import json, sys, os
B, OUT = sys.argv[1:3]
T = {'aarch64': ('a64_relative.txt', {'A': 0x5dc6098, 'B': 0x5da9a50, 'C': 0x5dc6898}),
     'x86_64': ('x64_relative.txt', {'A': 0x6c09a28, 'B': 0x6becbf8, 'C': 0x6c09228})}
OPS = {'SLOAD': 0x54, 'SSTORE': 0x55, 'TLOAD': 0x5c, 'TSTORE': 0x5d, 'CALL': 0xf1, 'STATICCALL': 0xfa,
       'DELEGATECALL': 0xf4, 'LOG0': 0xa0, 'LOG3': 0xa3, 'REVERT': 0xfd, 'RETURN': 0xf3, 'INVALID': 0xfe, 'ADD': 0x01}
out = {}
for arch, (f, tabs) in T.items():
    rel = {}
    for l in open(os.path.join(B, f)):
        a, b = l.split(); rel[int(a, 16)] = int(b, 16)
    out[arch] = {fam: {op: hex(rel.get(base + 8 * c, 0)) for op, c in OPS.items()} for fam, base in tabs.items()}
json.dump(out, open(OUT, 'w'), indent=1); print(json.dumps(out, indent=1))
