"""Map asmjit instruction ids to mnemonics from the EmitterExplicitT wrapper bodies of both builds."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emitcmp as E
m = {}
for path in sys.argv[1:3]:
    F = E.parse(path)
    for name, f in F.items():
        if 'EmitterExplicitT' in name and len(f['ids']) == 1:
            i = next(iter(f['ids'])); m.setdefault(i, set()).add(name.split('::')[-1])
json.dump({hex(k): sorted(v) for k, v in sorted(m.items())}, open(sys.argv[3], 'w'), indent=0)
want = [0x2ce,0x2cf,0x2d0,0x2d1,0x2d3,0x2d4,0x2d5,0x2d6,0x2d7,0x2dd,0x139,0x13a,0x13b,0x13c,0x13e,0x140,0x141,0x142,0x143,0x14a,0x4fd,0x4ff,0x500,0x50f,0x53c,0x53a,0x5f8,0x60c,0x60d,0x4c0,0x62f,0x61e,0x4e8,0x510,0x5ae,0x5bc,0x607,0x615,0x2f6,0x4a9,0x193]
for w in want: print(hex(w), m.get(w))
