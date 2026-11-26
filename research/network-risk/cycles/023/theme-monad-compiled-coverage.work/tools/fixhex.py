# Pad the value field of N lines and the BAL field to 64 hex digits (sets2tx.py wrote them with %x; replay.cpp reads hex in byte pairs).
import sys
for p in sys.argv[1:]:
    out = []
    for line in open(p):
        t = line.rstrip('\n').split(' ')
        if t[0] == 'N': t[7] = '%064x' % int(t[7], 16)
        elif t[0] == 'BAL': t[1] = '%064x' % int(t[1], 16)
        out.append(' '.join(t))
    open(p, 'w').write('\n'.join(out) + '\n')
    print('fixed', p, len(out))
