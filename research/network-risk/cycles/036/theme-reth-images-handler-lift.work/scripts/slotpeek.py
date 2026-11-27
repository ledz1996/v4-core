"""List the rip-relative call/jmp slots used directly by one function, the RELATIVE target of each, its FDE size and
its first instructions (objdump). Read only. usage: python3 -I slotpeek.py <bin> <fde> <rel> <hex fn>"""
import bisect, re, subprocess, sys
binf, fdef, relf, fa = sys.argv[1:5]
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdef)); s = [a for a, b in f]
rel = {int(a, 16): int(b, 16) for a, b in (l.split() for l in open(relf))}
def rng(a):
    k = bisect.bisect_right(s, a) - 1
    return f[k] if f[k][0] <= a < f[k][1] else None
lo, hi = rng(int(fa, 16))
dis = lambda a, b: subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % a, '--stop-address=%#x' % b, binf], capture_output=True, text=True).stdout
for l in dis(lo, hi).splitlines():
    m = re.search(r'^ *([0-9a-f]+):\s+(call|jmp)\s+(QWORD PTR \[rip.*#\s*([0-9a-f]+)|([0-9a-f]+) <)', l)
    if not m: continue
    if m.group(4):
        slot = int(m.group(4), 16); t = rel.get(slot)
    else:
        slot = None; t = int(m.group(5), 16)
        if lo <= t < hi: continue
    r = rng(t) if t else None
    head = ''
    if t and r:
        head = ' | '.join(x.split('\t')[-1].strip()[:60] for x in dis(t, min(r[1], t + 40)).splitlines() if re.match(r'^ *[0-9a-f]+:', x))[:300]
    print(m.group(1), m.group(2), hex(slot) if slot else '-', hex(t) if t else 'dyn', (r[1] - r[0]) if r else None, head)
