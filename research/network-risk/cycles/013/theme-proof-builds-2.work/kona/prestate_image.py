# Rebuild the memory image of the cannon64 prestate (version byte, page count, then index + 4096 bytes per page)
# and write the pages of the program's executable segment, read from the ELF program headers in the first page.
import sys, struct
d = open(sys.argv[1], 'rb').read()
ver = d[0]; npages = struct.unpack('>Q', d[1:9])[0]
mem = {}
o = 9
for k in range(npages):
    idx = struct.unpack('>Q', d[o:o + 8])[0]; mem[idx] = d[o + 8:o + 8 + 4096]; o += 4104
print('version', ver, 'pages', npages, 'trailing bytes', len(d) - o)
def rd(a, n):
    out = b''
    while n:
        p, off = a >> 12, a & 4095; k = min(n, 4096 - off)
        out += mem.get(p, b'\0' * 4096)[off:off + k]; a += k; n -= k
    return out
base = min(mem) << 12
eh = rd(base, 64); assert eh[:4] == b'\x7fELF'
phoff, = struct.unpack('>Q', eh[32:40]); phentsize, phnum = struct.unpack('>HH', eh[54:58])
segs = []
for i in range(phnum):
    ph = rd(base + phoff + i * phentsize, 56)
    p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack('>IIQQQQQQ', ph)
    segs.append((p_type, p_flags, hex(p_vaddr), p_filesz, p_memsz))
    if p_type == 1 and p_flags & 1:
        open(sys.argv[2], 'wb').write(rd(p_vaddr, p_filesz)); print('text segment', hex(p_vaddr), p_filesz)
print(segs)
