"""Print the direct callees of the functions holding the given addresses, to a given depth (reads only).
usage: python3 -I callees.py <bin> <fde> <depth> <hex>..."""
import bisect, re, subprocess, sys
binf, fdes, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
f = sorted(tuple(int(x, 16) for x in l.strip().split('...')) for l in open(fdes)); s = [a for a, b in f]
def fn(a):
    k = bisect.bisect_right(s, a) - 1; return f[k]
def callees(lo, hi):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        m = re.search(r'\s(call|jmp)\s+([0-9a-f]+)\s', l + ' ')
        if m:
            t = int(m.group(2), 16)
            if not (lo <= t < hi): r.append(t)
        elif re.search(r'\scall\s+(QWORD|r[a-z0-9]+)', l): r.append(re.sub(r'.*call\s+', '', l).strip())
    return r
def walk(a, d, ind):
    lo, hi = fn(a)
    print(' ' * ind + '%x (%d)' % (lo, hi - lo))
    if d == 0: return
    seen = []
    for t in callees(lo, hi):
        if t in seen: continue
        seen.append(t)
        if isinstance(t, str): print(' ' * (ind + 2) + 'indirect ' + t); continue
        walk(t, d - 1, ind + 2)
for x in sys.argv[4:]: walk(int(x, 16), depth, 0)
