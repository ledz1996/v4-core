# Per-function statistics of a WebAssembly module: instruction count, locals, block count, largest br_table.
import sys, json
data = open(sys.argv[1], 'rb').read()
assert data[:4] == b'\0asm', 'not wasm'
pos = 8
def uleb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1; r |= (x & 0x7f) << s; s += 7
        if x < 0x80: return r, p
def sleb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1; r |= (x & 0x7f) << s; s += 7
        if x < 0x80:
            if x & 0x40: r -= 1 << s
            return r, p
sections = {}
nimports_func = 0
while pos < len(data):
    sid = data[pos]; pos += 1
    size, pos = uleb(data, pos)
    sections.setdefault(sid, []).append((pos, size))
    pos += size
# count imported functions
if 2 in sections:
    p, size = sections[2][0]; n, p = uleb(data, p)
    for _ in range(n):
        l, p = uleb(data, p); p += l
        l, p = uleb(data, p); p += l
        kind = data[p]; p += 1
        if kind == 0: _, p = uleb(data, p); nimports_func += 1
        elif kind == 1: p += 1; f = data[p]; p += 1; _, p = uleb(data, p); p = uleb(data, p)[1] if f & 1 else p
        elif kind == 2: f = data[p]; p += 1; _, p = uleb(data, p); p = uleb(data, p)[1] if f & 1 else p
        elif kind == 3: p += 2
        else: raise Exception('import kind %d' % kind)
MEM = set(range(0x28, 0x3f))
NOIMM = set(range(0x45, 0xc5)) | {0x00, 0x01, 0x05, 0x0b, 0x0f, 0x1a, 0x1b, 0xd1}
p, size = sections[10][0]; end = p + size
nf, p = uleb(data, p)
stats = []; simd = 0
for fi in range(nf):
    bsize, p = uleb(data, p); bend = p + bsize
    nl, p = uleb(data, p); locals_ = 0
    for _ in range(nl):
        c, p = uleb(data, p); p += 1; locals_ += c
    ins = blocks = maxbt = brtables = 0
    while p < bend:
        op = data[p]; p += 1; ins += 1
        if op in NOIMM: continue
        if op in (0x02, 0x03, 0x04):
            blocks += 1
            if data[p] == 0x40 or data[p] in (0x7f, 0x7e, 0x7d, 0x7c, 0x7b, 0x70, 0x6f): p += 1
            else: _, p = sleb(data, p)
        elif op in (0x0c, 0x0d, 0x10, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0xd2): _, p = uleb(data, p)
        elif op == 0x0e:
            n, p = uleb(data, p)
            for _ in range(n + 1): _, p = uleb(data, p)
            brtables += 1; maxbt = max(maxbt, n + 1)
        elif op == 0x11: _, p = uleb(data, p); _, p = uleb(data, p)
        elif op == 0x1c:
            n, p = uleb(data, p); p += n
        elif op in MEM: _, p = uleb(data, p); _, p = uleb(data, p)
        elif op in (0x3f, 0x40): p += 1
        elif op == 0x41: _, p = sleb(data, p)
        elif op == 0x42: _, p = sleb(data, p)
        elif op == 0x43: p += 4
        elif op == 0x44: p += 8
        elif op == 0xd0: p += 1
        elif op == 0xfc:
            sub, p = uleb(data, p)
            if sub <= 7: pass
            elif sub == 8: _, p = uleb(data, p); p += 1
            elif sub in (9, 13, 15, 16, 17): _, p = uleb(data, p)
            elif sub == 10: p += 2
            elif sub == 11: p += 1
            elif sub in (12, 14): _, p = uleb(data, p); _, p = uleb(data, p)
            else: raise Exception('fc %d' % sub)
        elif op == 0xfd:
            simd += 1; raise Exception('SIMD op in function %d' % fi)
        else:
            raise Exception('unknown op 0x%02x at %d in function %d' % (op, p, fi))
    assert p == bend, (fi, p, bend)
    stats.append((ins, locals_, blocks, maxbt, brtables, fi + nimports_func))
stats.sort(reverse=True)
tot = sum(s[0] for s in stats)
out = {'functions': nf, 'importedFunctions': nimports_func, 'totalInstructions': tot,
       'largestByInstructions': [dict(index=s[5], instructions=s[0], locals=s[1], blocks=s[2], maxBrTableTargets=s[3]) for s in stats[:10]],
       'largestBrTable': max(s[3] for s in stats),
       'functionsWithBrTableOver4096': sum(1 for s in stats if s[3] > 4096),
       'maxLocalsTimesBlocks': max(s[1] * max(s[2], 1) for s in stats)}
bt = sorted(stats, key=lambda s: -s[3])[:5]
out['largestBrTables'] = [dict(index=s[5], targets=s[3], instructions=s[0]) for s in bt]
print(json.dumps(out, indent=1))
