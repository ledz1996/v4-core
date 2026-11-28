"""Reads R_X86_64_RELATIVE relocations of an ELF file as data and writes 'addr target' lines; then lists runs of
at least 256 consecutive relocated 8-byte slots (candidate instruction tables) with their distinct target counts.
usage: python3 -I rrel.py <bin> <out rel.txt> <out tables.json>"""
import struct, sys, json
f = open(sys.argv[1], 'rb').read()
shoff, = struct.unpack_from('<Q', f, 0x28); se, sn, six = struct.unpack_from('<HHH', f, 0x3a)
secs = [struct.unpack_from('<IIQQQQ', f, shoff + i * se) for i in range(sn)]
rel = {}
for name, typ, flags, addr, off, size in secs:
    if typ == 4:  # SHT_RELA
        for i in range(0, size, 24):
            o, info, add = struct.unpack_from('<QQq', f, off + i)
            if info & 0xffffffff == 8:
                rel[o] = add
open(sys.argv[2], 'w').write(''.join('%x %x\n' % (a, rel[a]) for a in sorted(rel)))
keys = sorted(rel); runs = []; start = keys[0]; prev = keys[0]
for a in keys[1:] + [None]:
    if a is not None and a == prev + 8:
        prev = a; continue
    n = (prev - start) // 8 + 1
    if n >= 256:
        runs.append((start, n))
    if a is not None:
        start = prev = a
out = []
for s, n in runs:
    for k in range(0, n - 255):
        pass
    t = [rel[s + 8 * i] for i in range(n)]
    out.append({'start': hex(s), 'slots': n, 'distinct': len(set(t))})
json.dump(out, open(sys.argv[3], 'w'), indent=0)
print(len(rel), 'relative relocations;', len(out), 'runs of 256 or more slots')
for r in out[:60]: print(r)
