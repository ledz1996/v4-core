"""Like cycle 35 extract2.py (x86 only), and also follows call/jmp through a rip-relative slot whose RELATIVE
relocation points at a function with an FDE. Slots resolved by the dynamic linker (GLOB_DAT/JUMP_SLOT) are listed
with their symbol name. Reads only; nothing from the binary is run.
usage: python3 -I extract3.py <bin> <fde> <rel> <out.s> <out.json> <hex start>... [stop=hex]"""
import bisect, json, re, subprocess, sys
binf, fdes, relf, out_s, out_j = sys.argv[1:6]
starts = [int(x, 16) for x in sys.argv[6:] if not x.startswith('stop=')]
STOP = set(int(x[5:], 16) for x in sys.argv[6:] if x.startswith('stop='))
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdes))
s = [a for a, b in f]
rel = {}
for l in open(relf):
    a, b = l.split(); rel[int(a, 16)] = int(b, 16)
dyn = {}
for l in subprocess.run(['readelf', '-rW', binf], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 5 and ('GLOB_DAT' in l or 'JUMP_SLO' in l):
        dyn[int(p[0], 16)] = p[4]
CALL = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp|j[a-z]+)\s+(?:0x)?([0-9a-f]+)\b')
IND = re.compile(r'^ *([0-9a-f]+):\s+(call|jmp)\s+QWORD PTR \[rip[+-]0x[0-9a-f]+\]\s+#\s*([0-9a-f]+)')
PLT = []
for l in subprocess.run(['readelf', '-SW', binf], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+(\.plt\S*)\s+\S+\s+([0-9a-f]+)\s+[0-9a-f]+\s+([0-9a-f]+)', l)
    if m: PLT.append((int(m.group(2), 16), int(m.group(2), 16) + int(m.group(3), 16)))
def inplt(t): return any(a <= t < b for a, b in PLT)
todo = list(starts); done = {}; external = {}; slots = {}
while todo:
    a = todo.pop()
    k = bisect.bisect_right(s, a) - 1
    lo, hi = f[k]
    if lo in done: continue
    if not (lo <= a < hi):
        external[hex(a)] = 'no fde'; continue
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout.splitlines()
    body = [l for l in out if re.match(r'^ *[0-9a-f]+:', l)]
    for l in body:
        c = CALL.match(l)
        if c:
            t = int(c.group(3), 16)
            if not (lo <= t < hi):
                if t in STOP or inplt(t): external[hex(t)] = re.sub(r'.*<', '<', l)
                else: todo.append(t)
        c = IND.match(l)
        if c:
            slot = int(c.group(3), 16)
            if slot in rel:
                t = rel[slot]; slots[hex(slot)] = hex(t)
                if t in STOP: external[hex(t)] = 'stop via slot %x' % slot
                else: todo.append(t)
            else:
                slots[hex(slot)] = dyn.get(slot, '?')
    done[lo] = (hi, body)
json.dump({'functions': {hex(a): [hex(h), h - a] for a, (h, b) in sorted(done.items())}, 'external': external,
           'slots': slots}, open(out_j, 'w'), indent=1)
open(out_s, 'w').write('\n'.join(l for a in sorted(done) for l in done[a][1]) + '\n')
print(len(done), 'functions', sum(len(b) for h, b in done.values()), 'lines; external', external, 'slots', slots)
