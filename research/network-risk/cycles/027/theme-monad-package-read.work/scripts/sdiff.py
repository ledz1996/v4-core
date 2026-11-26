"""Compare the .text and .rodata sections of assembler objects of the harness with the bytes at the same symbols
in a package ELF file (data reads only). Relocated positions of the object are masked on both sides.
usage: python3 -I sdiff.py <elf> <obj> [obj ...]"""
import sys, re, subprocess, hashlib, json
sys.path.insert(0, __import__('os').path.dirname(__file__))
from symbytes import sections, symbols, relocs
elf = sys.argv[1]
edata = open(elf, 'rb').read(); esecs = sections(elf); esyms = {s[0]: s for s in symbols(elf)}
def e_bytes(addr, n):
    for idx, (nm, a, off, sz) in esecs.items():
        if a and a <= addr < a + sz: return edata[off + addr - a: off + addr - a + n]
out = []
for o in sys.argv[2:]:
    od = open(o, 'rb').read(); secs = sections(o); syms = symbols(o); rel = relocs(o)
    for idx, (sname, a, off, sz) in secs.items():
        if sname not in ('.text', '.rodata') or sz == 0: continue
        anchors = [s for s in syms if s[3] == idx and s[0] in esyms]
        if not anchors: out.append({'obj': o, 'section': sname, 'result': 'no anchor symbol in package'}); continue
        nm, val = anchors[0][0], anchors[0][1]
        base = esyms[nm][1] - val
        ob = bytearray(od[off:off + sz]); pb = bytearray(e_bytes(base, sz))
        masked = 0
        for (ro, rsz, tgt) in rel.get(sname, []):
            for i in range(rsz):
                if ro + i < sz: ob[ro + i] = 0; pb[ro + i] = 0
            masked += 1
        consistent = all(esyms[s[0]][1] - s[1] == base for s in anchors)
        r = {'obj': o.split('/')[-1], 'section': sname, 'size': sz, 'anchor': nm, 'packageAddress': hex(base),
             'allSymbolsAtSameOffsets': consistent, 'symbols': len(anchors), 'relocsMasked': masked,
             'equal': ob == pb, 'sha256Masked': hashlib.sha256(bytes(pb)).hexdigest()}
        if ob != pb: r['diffs'] = [i for i in range(sz) if ob[i] != pb[i]][:30]
        out.append(r)
print(json.dumps(out, indent=1))
