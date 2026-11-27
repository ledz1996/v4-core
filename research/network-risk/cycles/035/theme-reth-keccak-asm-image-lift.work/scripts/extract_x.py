"""Disassemble functions (by .eh_frame FDE range) and every function they reach by a direct call or jmp,
with objdump -M intel, nothing executed. usage: python3 -I extract_x.py <bin> <fdes> <out.s> <out.json> <hex start>... [stop=hex]"""
import bisect, json, re, subprocess, sys
binf, fdes, out_s, out_j = sys.argv[1:5]
starts = [int(x, 16) for x in sys.argv[5:] if not x.startswith('stop=')]
STOP = set(int(x[5:], 16) for x in sys.argv[5:] if x.startswith('stop='))
f = sorted(tuple(int(x, 16) for x in l.strip().split('..')) for l in open(fdes) if '..' in l)
s = [a for a, b in f]
CALL = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp|j[a-z]+)\s+([0-9a-f]+)\b')
todo = list(starts); done = {}; external = {}
while todo:
    a = todo.pop()
    k = bisect.bisect_right(s, a) - 1
    lo, hi = f[k]
    if lo in done: continue
    if not (lo <= a < hi):
        external[hex(a)] = 'no fde'; continue
    txt = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout
    body = [l for l in txt.splitlines() if re.match(r'^ *[0-9a-f]+:', l)]
    for l in body:
        c = CALL.match(l)
        if c:
            t = int(c.group(3), 16)
            if not (lo <= t < hi):
                if t in STOP or '@plt' in l: external[hex(t)] = re.sub(r'.*<', '<', l)
                else: todo.append(t)
    done[lo] = (hi, body)
json.dump({'functions': {hex(a): [hex(h), h - a] for a, (h, b) in sorted(done.items())}, 'external': external}, open(out_j, 'w'), indent=1)
open(out_s, 'w').write('\n'.join(l for a in sorted(done) for l in done[a][1]) + '\n')
print(len(done), 'functions', sum(len(b) for h, b in done.values()), 'lines; external', external)
