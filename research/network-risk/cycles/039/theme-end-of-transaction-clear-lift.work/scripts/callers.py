"""Cycle 39: direct callers (call/jmp rel32) of given functions, and 8-byte little-endian copies of their addresses in
non-text sections (vtables, function pointer tables), with the calling function's FDE range and, when the binary has
a symbol table, its demangled name. Binary read as data. usage: python3 -I callers.py <profile> <out.json> <addr>..."""
import bisect, json, re, struct, subprocess, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
from bins import BINS
prof, outp = sys.argv[1:3]; T = [int(x, 16) for x in sys.argv[3:]]
P = BINS[prof]; b = open(P['bin'], 'rb').read()
secs = {}
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: secs[m.group(1)] = tuple(int(x, 16) for x in m.groups()[1:])
VA, OFF, SZ = secs['.text']; seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]
def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None
syms = {}
nm = subprocess.run(['nm', '-C', '--defined-only', P['bin']], capture_output=True, text=True).stdout
for l in nm.splitlines():
    p = l.split(' ', 2)
    if len(p) == 3 and p[1] in 'tTwW':
        try: syms[int(p[0], 16)] = p[2][:220]
        except ValueError: pass
res = {}
for t in T:
    calls = []
    for m in re.finditer(rb'[\xe8\xe9]', seg):
        pass
    res['%#x' % t] = dict(name=syms.get(t), calls=[], data=[])
import numpy as np
arr = np.frombuffer(seg, dtype=np.uint8)
for op in (0xe8, 0xe9):
    idx = np.nonzero(arr[:-5] == op)[0]
    rel = (arr[idx + 1].astype(np.int64) | (arr[idx + 2].astype(np.int64) << 8) | (arr[idx + 3].astype(np.int64) << 16) | (arr[idx + 4].astype(np.int64) << 24))
    rel = np.where(rel >= 1 << 31, rel - (1 << 32), rel)
    tgt = VA + idx + 5 + rel
    for t in T:
        for i in idx[tgt == t]:
            a = VA + int(i); f = fn(a)
            res['%#x' % t]['calls'].append(dict(at='%#x' % a, op='call' if op == 0xe8 else 'jmp', fn=['%#x' % x for x in f] if f else None,
                                               name=syms.get(f[0]) if f else None))
for nmn, (a, o, s) in secs.items():
    if nmn in ('.text', '.bss', '.tbss') or s == 0: continue
    data = b[o:o + s]
    for t in T:
        for m in re.finditer(re.escape(struct.pack('<Q', t)), data):
            res['%#x' % t]['data'].append(dict(section=nmn, at='%#x' % (a + m.start())))
json.dump(res, open(outp, 'w'), indent=1)
for t, r in res.items():
    print(prof, t, r['name'], 'calls', len(r['calls']), 'data refs', len(r['data']), 'calling fns', len({tuple(c['fn'] or ()) for c in r['calls']}))
