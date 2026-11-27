"""Disassemble the functions (by .eh_frame FDE range) holding the given start addresses and every function
they call directly, with objdump per range. Reads only; nothing from the binary is run.
usage: python3 -I extract2.py <bin> <fde list> <arch x86|a64> <out.s> <out.json> <hex start>... [stop=hex]"""
import bisect, json, re, subprocess, sys
binf, fdes, arch, out_s, out_j = sys.argv[1:6]
starts = [int(x, 16) for x in sys.argv[6:] if not x.startswith('stop=')]
STOP = set(int(x[5:], 16) for x in sys.argv[6:] if x.startswith('stop='))
f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes) if '..' in l)
s = [a for a, b in f]
if arch == 'x86':
    CALL = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp|j[a-z]+)\s+(?:0x)?([0-9a-f]+)\b')
    opts = ['-M', 'intel']
else:
    CALL = re.compile(r'^ *([0-9a-f]+):\s+(bl|b|b\.[a-z]+|cbz|cbnz|tbz|tbnz)\s+(?:[wx][0-9]+, )?(?:#0x?[0-9a-f]+, )?(?:0x)?([0-9a-f]+)\b')
    opts = []
OBJ = 'objdump' if arch == 'x86' else 'llvm-objdump'
PLT = []
for l in subprocess.run(['readelf', '-SW', binf], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+(\.plt\S*)\s+\S+\s+([0-9a-f]+)\s+[0-9a-f]+\s+([0-9a-f]+)', l)
    if m: PLT.append((int(m.group(2), 16), int(m.group(2), 16) + int(m.group(3), 16)))
def inplt(t): return any(a <= t < b for a, b in PLT)
todo = list(starts); done = {}; external = {}
while todo:
    a = todo.pop()
    k = bisect.bisect_right(s, a) - 1
    lo, hi = f[k]
    if lo in done: continue
    if not (lo <= a < hi):
        external[hex(a)] = 'no fde'; continue
    out = subprocess.run([OBJ, '-d', '--no-show-raw-insn', *opts, '--start-address=%#x' % lo, '--stop-address=%#x' % hi, binf],
                         capture_output=True, text=True).stdout.splitlines()
    body = [l for l in out if re.match(r'^ *[0-9a-f]+:', l)]
    for l in body:
        c = CALL.match(l)
        if c:
            t = int(c.group(3), 16)
            if not (lo <= t < hi):
                if t in STOP or inplt(t): external[hex(t)] = re.sub(r'.*<', '<', l)
                else: todo.append(t)
    done[lo] = (hi, body)
json.dump({'functions': {hex(a): [hex(h), h - a] for a, (h, b) in sorted(done.items())}, 'external': external}, open(out_j, 'w'), indent=1)
open(out_s, 'w').write('\n'.join(l for a in sorted(done) for l in done[a][1]) + '\n')
print(len(done), 'functions', sum(len(b) for h, b in done.values()), 'lines; external', external)
