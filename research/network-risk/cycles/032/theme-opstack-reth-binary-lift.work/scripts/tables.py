"""List every 256-entry handler table in a binary's RELATIVE relocations whose most common entry is the unknown-opcode
handler, and say whether its 25 arithmetic, comparison and shift entries equal those of the table the models ran.
usage: python3 -I tables.py <rel> <table hex>"""
import collections, sys
OPS = [1,2,3,4,5,6,7,8,9,10,11,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x1d]
rel = {}
for l in open(sys.argv[1]):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
t = int(sys.argv[2], 16); ref = [rel[t + 8 * o] for o in OPS]; unk = rel[t + 8 * 0x0c]
a = min(rel); out = []
keys = sorted(rel); i = 0
while i < len(keys):
    a = keys[i]
    if all((a + 8 * j) in rel for j in range(256)):
        f = [rel[a + 8 * j] for j in range(256)]
        if collections.Counter(f).most_common(1)[0][0] == unk and f[0x0c] == unk:
            arith = [f[o] for o in OPS]
            out.append((hex(a), 'same' if arith == ref else ('all-unknown' if set(arith) == {unk} else 'DIFFERENT')))
            i = keys.index(a + 8 * 255) + 1; continue
    i += 1
print(collections.Counter(x[1] for x in out), out)
