"""Intra-function reachability over an aarch64 listing: from a start address, which addresses are reachable
following fall-through, b, b.cond, cbz/cbnz, tbz/tbnz (bl falls through; ret, br and brk end a path).
usage: python3 -I reach_a64.py <listing> <start hex> <target hex>"""
import re, sys
L = open(sys.argv[1]).read().splitlines()
ins = []
for l in L:
    m = re.match(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$', l)
    if m: ins.append((int(m.group(1), 16), m.group(2), re.sub(r'\s*<[^>]*>', '', m.group(3))))
idx = {a: i for i, (a, _, _) in enumerate(ins)}
start, target = int(sys.argv[2], 16), int(sys.argv[3], 16)
seen = set(); todo = [start]; calls = set()
while todo:
    a = todo.pop()
    if a in seen or a not in idx: continue
    seen.add(a); i = idx[a]; _, mn, ops = ins[i]
    nxt = ins[i + 1][0] if i + 1 < len(ins) else None
    tg = re.findall(r'0x([0-9a-f]+)', ops)
    if mn == 'bl': calls.add(tg[-1] if tg else ops); todo.append(nxt); continue
    if mn in ('ret', 'br', 'brk'): continue
    if mn == 'b': todo.append(int(tg[-1], 16)); continue
    if mn.startswith('b.') or mn in ('cbz', 'cbnz', 'tbz', 'tbnz'):
        todo.append(int(tg[-1], 16)); todo.append(nxt); continue
    todo.append(nxt)
print('reachable', target in seen, 'blocks', len(seen), 'calls on paths', sorted(calls)[:40])
