"""Selectors of every custom error declared in src/ (error X(...);) computed with the reference keccak."""
import re, os, sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
out = {}
for root, _, fs in os.walk('/home/user/v4-core/src'):
    for f in fs:
        t = open(os.path.join(root, f)).read()
        for m in re.finditer(r'error\s+(\w+)\(([^)]*)\)', t):
            args = [a.strip().split()[0] for a in m.group(2).split(',') if a.strip()]
            sig = '%s(%s)' % (m.group(1), ','.join(args))
            out['0x' + keccak(sig.encode())[:4].hex()] = [sig, os.path.join(root, f)[len('/home/user/v4-core/'):]]
for s in ['Error(string)', 'Panic(uint256)']: out['0x' + keccak(s.encode())[:4].hex()] = [s, 'builtin']
json.dump(out, open('/home/user/v4-core/research/network-risk/cycles/024/theme-failed-tx-replay.work/results/selectors.json', 'w'), indent=1)
for k in sys.argv[1:]: print(k, out.get(k))
