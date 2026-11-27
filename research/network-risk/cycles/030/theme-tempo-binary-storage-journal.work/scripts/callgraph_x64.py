"""Breadth-first walk of direct calls (bl and tail b to another function) from given roots in a disassembly
listing, using .eh_frame ranges as function bounds. Reports, for each function reached, its depth and whether
its body has given text patterns. usage: python3 -I callgraph.py <dis> <fde list> <maxdepth> <out.json> <root>..."""
import bisect, json, re, sys
dis, fdes, maxd, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
roots = [int(x, 16) for x in sys.argv[5:]]
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdes)); s = [a for a, b in f]
lines = open(dis).read().splitlines()
idx = {}
for i, l in enumerate(lines):
    m = re.match(r'^ *([0-9a-f]+):', l)
    if m: idx[int(m.group(1), 16)] = i
CALL = re.compile(r'^ *([0-9a-f]+):\s+(bl|b|call|callq|jmp|jmpq)\s+(?:0x)?([0-9a-f]+)\b')
def fn(a):
    k = bisect.bisect_right(s, a) - 1
    return f[k] if k >= 0 and f[k][0] <= a < f[k][1] else None
seen = {}; front = [(fn(r), 0, None) for r in roots]
while front:
    nxt = []
    for r, d, parent in front:
        if r is None or r in seen: continue
        lo, hi = r; i = idx.get(lo)
        if i is None: continue
        body = []
        while i < len(lines):
            m = re.match(r'^ *([0-9a-f]+):', lines[i])
            if m and int(m.group(1), 16) >= hi: break
            body.append(lines[i]); i += 1
        txt = '\n'.join(body)
        seen[r] = {'depth': d, 'size': hi - lo, 'parent': parent and hex(parent[0]),
                   'x78': bool(re.search(r'imul\s+\w+,\w+,0x78|,0x78\]|0x78\b', txt)), 'inv11': '#0x2e8b, lsl #48' in txt or '0x2e8ba2e8ba2e8ba3' in txt,
                   'calls': []}
        if d >= maxd: continue
        for l in body:
            c = CALL.match(l)
            if c:
                t = int(c.group(3), 16)
                if lo <= t < hi or '@plt' in l: continue
                g = fn(t)
                if g: seen[r]['calls'].append(hex(g[0])); nxt.append((g, d + 1, r))
    front = nxt
json.dump({hex(k[0]): v for k, v in seen.items()}, open(out, 'w'), indent=0)
print(len(seen), 'functions')
