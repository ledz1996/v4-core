"""Build a virtual memory image of an ELF file (PT_LOAD segments at their vaddr, RELATIVE relocations applied with base 0).
Data only: nothing from the file is executed."""
import struct, subprocess
def image(path):
    fb = open(path, 'rb').read()
    phoff = struct.unpack_from('<Q', fb, 0x20)[0]; n = struct.unpack_from('<H', fb, 0x38)[0]
    segs = []
    for i in range(n):
        t, fl, off, va, pa, fs, ms, al = struct.unpack_from('<IIQQQQQQ', fb, phoff + 56 * i)
        if t == 1: segs.append((va, off, fs, ms))
    hi = max(va + ms for va, off, fs, ms in segs)
    img = bytearray(hi)
    for va, off, fs, ms in segs:
        img[va:va + fs] = fb[off:off + fs]
    out = subprocess.run(['readelf', '-rW', path], capture_output=True, text=True).stdout
    for l in out.splitlines():
        if 'RELATIV' in l:
            p = l.split()
            img[int(p[0], 16):int(p[0], 16) + 8] = int(p[-1], 16).to_bytes(8, 'little')
    return bytes(img), segs
