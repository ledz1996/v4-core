"""Extract the objdump text of named functions from a large disassembly file (no code is run).
usage: python3 -I fnext.py <dis.s> <outdir> <substring>...   writes one file per match, named by start address."""
import sys, re, os
dis, out = sys.argv[1], sys.argv[2]; keys = sys.argv[3:]
os.makedirs(out, exist_ok=True)
cur = None; buf = []
def flush():
    if cur is not None:
        open(os.path.join(out, cur[0] + '.s'), 'w').write(''.join(buf))
        print(cur[0], cur[1][:160])
with open(dis, errors='replace') as f:
    for line in f:
        m = re.match(r'^([0-9a-f]+) <(.*)>:$', line)
        if m:
            flush(); cur = None; buf = []
            if any(k in m.group(2) for k in keys) and '[clone .cold]' not in m.group(2):
                cur = (m.group(1), m.group(2)); buf = [line]
            continue
        if cur is not None: buf.append(line)
flush()
