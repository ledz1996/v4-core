"""Cycle 39: anchor on the panic 'transaction id overflow' (revm-state TransactionId::increment). Finds the message in
the binary, every RIP-relative lea that loads it, the conditional jumps into that panic stub, and for each jump the
instruction window before it (objdump text of the function). Records which journal words the window stores and
their base offsets. Binary read as data only. usage: python3 -I txpanic.py <profile> <out.json>"""
import bisect, json, re, struct, subprocess, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
from bins import BINS
prof, outp = sys.argv[1:3]
P = BINS[prof]; b = open(P['bin'], 'rb').read()
secs = {}
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: secs[m.group(1)] = tuple(int(x, 16) for x in m.groups()[1:])
VA, OFF, SZ = secs['.text']; seg = b[OFF:OFF + SZ]
msg = b'transaction id overflow'
tg = []
for nm, (a, o, s) in secs.items():
    if nm in ('.rodata', '.rodata.str', '.lrodata') or nm.startswith('.rodata'):
        for m in re.finditer(re.escape(msg), b[o:o + s]): tg.append(a + m.start())
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]
def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None
leas = []
for m in re.finditer(rb'[\x48\x4c]\x8d([\x05\x0d\x15\x1d\x25\x2d\x35\x3d])(....)', seg, re.S):
    t = VA + m.end() + struct.unpack('<i', m.group(2))[0]
    if t in tg: leas.append(VA + m.start())
_c = {}
def dis(fr):
    if fr not in _c:
        txt = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % fr[0],
                              '--stop-address=%#x' % fr[1], P['bin']], capture_output=True, text=True).stdout
        _c[fr] = [(int(mm.group(1), 16), re.sub(r'\s*<[^>]*>', '', mm.group(2)).split('#')[0].strip())
                  for l in txt.splitlines() for mm in [re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)] if mm]
    return _c[fr]
out = []
for la in leas:
    fr = fn(la)
    if not fr: out.append(dict(lea='%#x' % la, fn=None)); continue
    L = dis(fr); A = [x for x, _ in L]
    # panic stub start: the lea itself or up to 3 instructions before it
    i = A.index(la); stub = {A[j] for j in range(max(0, i - 3), i + 1)}
    jumps = [(x, t) for x, t in L if re.match(r'^j\w+\s+([0-9a-f]+)$', t) and int(t.split()[1], 16) in stub]
    for jx, jt in jumps:
        k = A.index(jx); win = L[max(0, k - 120):k + 40]
        # the increment: the 'dec'/'add -1' on a 32-bit register right before the jump, loaded from [R+d]
        inc = None
        for x, t in reversed(L[max(0, k - 6):k]):
            mm = re.match(r'^mov\s+(e\w+|r\d+d),DWORD PTR \[(\w+)\+(0x[0-9a-f]+)\]$', t)
            if mm: inc = (mm.group(2), int(mm.group(3), 16)); break
        rec = dict(lea='%#x' % la, fn=['%#x' % fr[0], '%#x' % fr[1]], jump='%#x' % jx, jt=jt,
                   pre=[(('%#x' % x), t) for x, t in L[max(0, k - 4):k + 1]])
        if inc:
            base, d = inc; J = d - 0x120; rec['J'] = '%#x' % J; rec['base'] = base
            nm = {J + 0x118: 'depth', J + 0x28: 'jlen', J + 0x10: 'logs', J + 0x40: 'list', J + 0x108: 'titems', J + 0x100: 'tgrowth', J + 0x120: 'txid', J + 0xb0: 'coinbase', J + 0x88: 'alist_items'}
            st = []
            for x, t in win:
                for o, n in nm.items():
                    if re.match(r'^mov\s+\w+ PTR \[\w+\+%#x\],' % o, t): st.append(('%#x' % x, n, t))
            rec['stores'] = st
        out.append(rec)
json.dump(dict(msg=['%#x' % t for t in tg], sites=out), open(outp, 'w'), indent=1)
print(prof, 'msg', ['%#x' % t for t in tg], 'leas', len(leas), 'jumps', sum(1 for o in out if 'jump' in o))
from collections import Counter
print(' J', Counter(o.get('J') for o in out).most_common(), 'fns', len({tuple(o['fn'] or ()) for o in out}))
