"""Index function starts in the objdump text (byte offsets), so functions can be cut out without rescanning."""
import re, json, sys
D = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/dl/dis/monad-0.16.7.s'
idx = {}
with open(D, 'rb') as f:
    pos = 0
    for line in f:
        if line[:1] in b'0123456789abcdef' and line.rstrip().endswith(b'>:'):
            m = re.match(rb'^([0-9a-f]+) <', line)
            if m: idx[int(m.group(1), 16)] = pos
        pos += len(line)
json.dump({'%x' % k: v for k, v in idx.items()}, open(sys.argv[1], 'w'))
print(len(idx))
