"""Find direct call/jmp rel32 sites and RELATIVE relocation slots that target given addresses. Reads only.
usage: python3 -I xrefs.py <bin> <hexaddr>..."""
import sys, struct, subprocess
fb = open(sys.argv[1], 'rb').read()
T = [int(x, 16) for x in sys.argv[2:]]
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x20c7b00, 0x20c6b00, 0x4ea2a18
d = TEXT_VA - TEXT_OFF
for t in T:
    hits = []
    for op in (b'\xe8', b'\xe9'):
        i = TEXT_OFF
        while True:
            i = fb.find(op, i, TEXT_OFF + TEXT_SZ)
            if i < 0: break
            rel = struct.unpack_from('<i', fb, i + 1)[0]
            if i + d + 5 + rel == t: hits.append((op.hex(), hex(i + d)))
            i += 1
    print(hex(t), 'rel32 sites', hits)
