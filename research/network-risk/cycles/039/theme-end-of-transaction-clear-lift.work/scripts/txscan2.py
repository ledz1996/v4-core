"""Cycle 39: layout-free search for inlined end-of-transaction blocks in revm builds whose TransactionId is a
NonMaxU32 (stored as value XOR 0xffffffff, so increment = 'dec' of the stored dword, panic on zero). Byte patterns
(binary read as data): a 'mov qword [R+d],0' (depth, d = J+0x118) with, within 0x400 bytes after it, either
'mov dword [R'+d+8],r32' (increment) or 'mov dword [R'+d+8],0xffffffff' (reset to ZERO, finalize), and a zero store to
the journal length J+0x28 (= d-0xf0) within 0x400 bytes either side. Groups by function and J.
usage: python3 -I txscan2.py <profile> <out.json>"""
import bisect, json, re, struct, subprocess, sys
from collections import Counter, defaultdict
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
MR = rb'([\x80-\x83\x85-\x87\x88-\x8b\x8d-\x8f\x90-\x93\x95-\x97\x98-\x9b\x9d-\x9f\xa0-\xa3\xa5-\xa7\xa8-\xab\xad-\xaf\xb0-\xb3\xb5-\xb7\xb8-\xbb\xbd-\xbf])'
zq = defaultdict(list)   # disp -> positions of mov qword [r+disp],0
for m in re.finditer(rb'[\x48\x49]\xc7([\x80-\x83\x85-\x87])(....)\x00\x00\x00\x00', seg, re.S):
    zq[struct.unpack('<i', m.group(2))[0]].append(m.start())
dw = defaultdict(list)   # disp -> positions of mov dword [r+disp],r32  (opt REX 40-4f, 89 /r mod10)
for m in re.finditer(rb'(?:[\x40-\x47\x41\x44\x45])?\x89' + MR + rb'(....)', seg, re.S):
    dw[struct.unpack('<i', m.group(2))[0]].append(m.start())
dff = defaultdict(list)  # mov dword [r+disp],0xffffffff
for m in re.finditer(rb'(?:\x41)?\xc7([\x80-\x83\x85-\x87])(....)\xff\xff\xff\xff', seg, re.S):
    dff[struct.unpack('<i', m.group(2))[0]].append(m.start())
res = defaultdict(lambda: dict(depth0=[], inc=[], reset=[], jlen0=[]))
for d, ps in zq.items():
    if d < 0x118: continue
    for p in ps:
        inc = [q for q in dw.get(d + 8, []) if p < q < p + 0x400]
        rst = [q for q in dff.get(d + 8, []) if p - 0x400 < q < p + 0x400]
        jz = [q for q in zq.get(d - 0xf0, []) if p - 0x400 < q < p + 0x400]
        if (inc or rst) and jz:
            f = fn(VA + p)
            k = ('%#x-%#x' % f if f else 'nofde', '%#x' % (d - 0x118))
            r = res[k]; r['depth0'].append('%#x' % (VA + p)); r['inc'] += ['%#x' % (VA + q) for q in inc]
            r['reset'] += ['%#x' % (VA + q) for q in rst]; r['jlen0'] += ['%#x' % (VA + q) for q in jz]
out = [dict(fn=k[0], J=k[1], **{x: sorted(set(y)) for x, y in v.items()}) for k, v in sorted(res.items())]
json.dump(out, open(outp, 'w'), indent=1)
print(prof, len(out), 'function/J groups; J', Counter(o['J'] for o in out).most_common(),
      'with increment', sum(1 for o in out if o['inc']), 'with reset', sum(1 for o in out if o['reset']))
