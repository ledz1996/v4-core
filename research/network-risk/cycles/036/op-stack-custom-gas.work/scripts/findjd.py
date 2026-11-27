"""Locate candidate legacy jump destination analysis loops in an x86-64 ELF by byte pattern: a lea with
displacement -0x5e (push size step) within 48 bytes of a compare with 0x5b (JUMPDEST). Reads only.
usage: python3 -I findjd.py <bin> <fdes>"""
import re, sys, bisect, struct
b = open(sys.argv[1], 'rb').read()
f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(sys.argv[2]) if '..' in l)
st = [x[0] for x in f]
# text segment file offset == vaddr - 0x1000 for these builds; derive from section header via readelf would be better
import subprocess
sec = subprocess.run(['readelf', '-SW', sys.argv[1]], capture_output=True, text=True).stdout
m = re.search(r'\.text\s+PROGBITS\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', sec)
va, off, sz = (int(x, 16) for x in m.groups())
t = b[off:off + sz]
LEA = re.compile(rb'[\x48-\x4f]\x8d[\x44\x4c\x54\x5c\x64\x6c\x74\x7c].\xa2', re.S)
CMP = re.compile(rb'(?:[\x40-\x4f]?\x83[\xf8-\xff]\x5b|[\x40-\x4f]?\x80[\xf8-\xff]\x5b|\x3c\x5b)', re.S)
hits = {}
for mm in LEA.finditer(t):
    lo = max(0, mm.start() - 48); hi = mm.start() + 48
    if CMP.search(t, lo, hi):
        a = va + mm.start()
        i = bisect.bisect_right(st, a) - 1
        fn = f[i] if i >= 0 and f[i][0] <= a < f[i][1] else None
        hits.setdefault(fn, []).append(hex(a))
for fn, v in hits.items():
    print(hex(fn[0]) if fn else None, (fn[1] - fn[0]) if fn else None, v[:4])
