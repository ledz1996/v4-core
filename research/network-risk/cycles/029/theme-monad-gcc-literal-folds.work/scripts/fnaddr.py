"""Extract objdump text of functions by start address from a large disassembly file (nothing is run).
usage: python3 -I fnaddr.py <dis.s> <outdir> <hexaddr>..."""
import sys, re, os
dis, out = sys.argv[1], sys.argv[2]; want = {int(a, 16) for a in sys.argv[3:]}
os.makedirs(out, exist_ok=True)
cur = None; buf = []
def flush():
    if cur is not None:
        open(os.path.join(out, '%016x.s' % cur), 'w').write(''.join(buf)); print(hex(cur), len(buf))
with open(dis, errors='replace') as f:
    for line in f:
        m = re.match(r'^([0-9a-f]+) <(.*)>:$', line)
        if m:
            flush(); cur = None; buf = []
            a = int(m.group(1), 16)
            if a in want: cur = a; buf = [line]
            continue
        if cur is not None: buf.append(line)
flush()
