"""Counts 8-byte little-endian occurrences of each handler entry in the file-backed data sections (Go funcvals
that jump table builders store in operation.execute). usage: python3 -I funcval.py <bin> <fnlist> <names...>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goshim as G
img = G.Image(sys.argv[1]); fns = G.fnlist(sys.argv[2])
for n in sys.argv[3:]:
    e = fns[G.VM + n][0]; pat = e.to_bytes(8, 'little'); hits = []
    for lo, hi, off in img.secs:
        if lo < 0x1000000 and hi < 0x3000000: continue  # skip .text
        b = img.f[off:off + hi - lo]; i = b.find(pat)
        while i >= 0:
            hits.append(hex(lo + i)); i = b.find(pat, i + 1)
    print(n, hex(e), hits)
