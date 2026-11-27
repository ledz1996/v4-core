"""List candidate direct call/jmp sites (E8/E9 rel32) in .text whose target is one of the given addresses.
Reads the file only. usage: python3 -I callers.py <bin> <hex target>..."""
import sys, struct, re
b = open(sys.argv[1], 'rb').read()
T = set(int(x, 16) for x in sys.argv[2:])
import subprocess
for l in subprocess.run(['readelf', '-SW', sys.argv[1]], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: TEXT_VA, TEXT_OFF, TEXT_SZ = (int(x, 16) for x in m.groups())
seg = b[TEXT_OFF:TEXT_OFF + TEXT_SZ]
out = {}
for op in (b'\xe8', b'\xe9'):
    i = seg.find(op)
    while i != -1:
        if i + 5 <= len(seg):
            rel = struct.unpack_from('<i', seg, i + 1)[0]
            va = TEXT_VA + i; t = va + 5 + rel
            if t in T: out.setdefault(hex(t), []).append((hex(va), op.hex()))
        i = seg.find(op, i + 1)
for k, v in out.items(): print(k, len(v), v)
