# Scan the kona-client cannon64 prestate memory image for the instruction shape behind LLVM issue 235261:
# `andi rX, rY, 0x40` (the i128 shift-parts select condition) and every later use of rX before it is redefined.
# A use other than the condition operand of MOVN/MOVZ or a zero test in a branch would mark a place where
# the 0/64 value is treated as a 0/1 boolean. Pages are scanned in file order, aligned to 4 bytes.
import sys, struct, collections
data = open(sys.argv[1], 'rb').read()
def dec(w):
    op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; fn = w & 63
    if op == 0:
        if fn in (0x0a, 0x0b): return ('movz' if fn == 0x0a else 'movn'), [rs], rt, rd
        if fn in (0x08,): return 'jr', [rs], None, None
        if fn in (0x09,): return 'jalr', [rs], None, rd
        if fn in (0x10, 0x12): return 'mf', [], None, rd
        if fn in (0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x11, 0x13): return 'hilo%x' % fn, [rs, rt], None, None
        if fn in (0x00, 0x02, 0x03, 0x38, 0x3a, 0x3b, 0x3c, 0x3e, 0x3f): return 'shift%x' % fn, [rt], None, rd
        return 'r%x' % fn, [rs, rt], None, rd
    if op == 0x1c: return 's2_%x' % fn, [rs, rt], None, rd
    if op in (4, 5): return ('beq', 'bne')[op - 4], [rs, rt], None, None
    if op in (6, 7, 1): return 'bz%x' % op, [rs], None, None
    if op in (2, 3): return 'j', [], None, (31 if op == 3 else None)
    if op >= 0x28 and op != 0x37 and op not in (0x30, 0x34): return 'st%x' % op, [rs, rt], None, None
    if op >= 0x20: return 'ld%x' % op, [rs], None, rt
    return 'i%x' % op, [rs], None, rt
n = 0; uses = collections.Counter(); odd = []
for off in range(0, len(data) - 4, 4):
    w = struct.unpack('>I', data[off:off + 4])[0]
    if w >> 26 == 0x0C and (w & 0xFFFF) == 0x40:
        r = (w >> 16) & 31
        if r == 0: continue
        n += 1
        for k in range(1, 48):
            w2 = struct.unpack('>I', data[off + 4 * k:off + 4 * k + 4])[0]
            name, srcs, cond, dst = dec(w2)
            if cond == r: uses[name + ' cond'] += 1
            elif r in srcs:
                if name in ('beq', 'bne') and 0 in srcs: uses[name + ' vs zero'] += 1
                elif name.startswith('bz'): uses[name] += 1
                else:
                    uses[name] += 1
                    if len(odd) < 40: odd.append((hex(off), k, name, hex(w2)))
            if dst == r: break
print({'andi64Sites': n, 'uses': dict(uses), 'otherUsesFirst': odd})
