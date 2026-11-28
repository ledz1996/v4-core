"""Cycle 39: layout-free search for inlined end-of-transaction clears. Byte patterns only (binary read as data):
every 'inc qword [R+d]' or 'add qword [R+d],1' (the transaction id) with, within 0x300 bytes before it, a
'mov qword [R+d-8],0' (depth) and a 'mov qword [R+d-0xf8],0' (journal length) on the same base register R.
Reports D = d-0x120 (journal base relative to R) and the function (FDE). usage: python3 -I txscan.py <profile> <out.json>"""
import bisect, json, re, struct, subprocess, sys
from collections import Counter
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
from bins import BINS
prof, outp = sys.argv[1:3]
P = BINS[prof]; b = open(P['bin'], 'rb').read()
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]
def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None
def reg(rex, modrm): return (modrm & 7) | ((rex & 1) << 3)
incs = []
for m in re.finditer(rb'([\x48\x49])\xff([\x80-\x83\x85-\x87])(....)|([\x48\x49])\x83([\x80-\x83\x85-\x87])(....)\x01', seg, re.S):
    if m.group(1): rex, mr, d = m.group(1)[0], m.group(2)[0], m.group(3)
    else: rex, mr, d = m.group(4)[0], m.group(5)[0], m.group(6)
    incs.append((m.start(), reg(rex, mr), struct.unpack('<i', d)[0]))
zero = {}
for m in re.finditer(rb'([\x48\x49])\xc7([\x80-\x83\x85-\x87])(....)\x00\x00\x00\x00', seg, re.S):
    zero.setdefault((reg(m.group(1)[0], m.group(2)[0]), struct.unpack('<i', m.group(3))[0]), []).append(m.start())
res = []
for pos, r, d in incs:
    if d < 0x120: continue
    dz = [p for p in zero.get((r, d - 8), []) if pos - 0x300 <= p < pos]
    jz = [p for p in zero.get((r, d - 0xf8), []) if pos - 0x300 <= p < pos]
    if dz and jz:
        f = fn(VA + pos)
        res.append(dict(inc='%#x' % (VA + pos), reg=r, D='%#x' % (d - 0x120), depth0=['%#x' % (VA + p) for p in dz],
                        jlen0=['%#x' % (VA + p) for p in jz], fn=['%#x' % x for x in f] if f else None))
json.dump(res, open(outp, 'w'), indent=1)
print(prof, len(res), 'sites; D', Counter(x['D'] for x in res).most_common(), 'functions', len({tuple(x['fn'] or []) for x in res}))
