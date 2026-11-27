"""Extracts functions (by .eh_frame FDE range) and everything they call from a disassembly listing.

usage: python3 -I extract.py <disasm> <fde list> <out.s> <out.json> <hex start> [...]
Calls into PLT stubs or into the stop list are not followed; they are reported.
"""
import bisect, json, re, sys

dis, fdes, out_s, out_j = sys.argv[1:5]
starts = [int(x, 16) for x in sys.argv[5:] if not x.startswith('stop=')]
STOP = set(int(x[5:], 16) for x in sys.argv[5:] if x.startswith('stop='))
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdes))
s = [a for a, b in f]
lines = open(dis).read().splitlines()
idx = {}
for i, l in enumerate(lines):
    m = re.match(r'^ *([0-9a-f]+):', l)
    if m:
        idx[int(m.group(1), 16)] = i
CALL = re.compile(r'^ *([0-9a-f]+):\s+(bl|b|call|callq|jmp|jmpq)\s+(?:0x)?([0-9a-f]+)\b')
PANIC_HINT = ('panic',)
todo = list(starts)
done = {}
external = {}
while todo:
    a = todo.pop()
    k = bisect.bisect_right(s, a) - 1
    lo, hi = f[k]
    if lo in done:
        continue
    if not (lo <= a < hi):
        external[hex(a)] = 'no fde'
        continue
    i = idx[lo]
    body = []
    while i < len(lines):
        m = re.match(r'^ *([0-9a-f]+):', lines[i])
        if m and int(m.group(1), 16) >= hi:
            break
        body.append(lines[i])
        c = CALL.match(lines[i])
        if c:
            t = int(c.group(3), 16)
            if not (lo <= t < hi):
                if t in STOP:
                    external[hex(t)] = 'stop'
                elif '@plt' in lines[i] or t < 0x1886240 and 'x86' not in dis:
                    external[hex(t)] = re.sub(r'.*<', '<', lines[i])
                else:
                    todo.append(t)
        i += 1
    done[lo] = (hi, body)
json.dump({'functions': {hex(a): [hex(h), h - a] for a, (h, b) in sorted(done.items())}, 'external': external},
          open(out_j, 'w'), indent=1)
open(out_s, 'w').write('\n'.join(l for a in sorted(done) for l in done[a][1]) + '\n')
print(len(done), 'functions', sum(len(b) for h, b in done.values()), 'lines; external', external)
