"""Normalise disassembly text: drop rip displacements and sort the two sources of commutative VEX ops."""
import sys, re
COMM = {'vpxor', 'vpor', 'vpand', 'vpaddq', 'vxorps', 'vpaddd'}
for line in open(sys.argv[1]):
    line = re.sub(r'\[rip\+0x[0-9a-f]+\]\s*#?\s*', '[rip+X]', line.strip())
    p = line.split(None, 1)
    if p and p[0] in COMM and len(p) > 1:
        ops = [x.strip() for x in p[1].split(',')]
        if len(ops) == 3: line = p[0] + ' ' + ops[0] + ',' + ','.join(sorted(ops[1:]))
    print(line)
