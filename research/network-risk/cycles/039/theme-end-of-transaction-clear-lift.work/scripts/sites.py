"""Cycle 39: for each journal base offset J of a binary's frame code, list every site that zeroes the depth word J+0x118
(mov qword [r+d],0 / mov [r+d],reg / movups/movaps xmm over it), every inc/add of the id word J+0x120, every zeroing
of the journal length J+0x28 and of the transient map items J+0x108, and group them by function (FDE table).
Reads the binary as data and its objdump text only. usage: python3 -I sites.py <profile> <J,J,...> <out.json>"""
import bisect, json, re, struct, subprocess, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
from bins import BINS
prof, Js, outp = sys.argv[1], [int(x, 16) for x in sys.argv[2].split(',')], sys.argv[3]
P = BINS[prof]; b = open(P['bin'], 'rb').read()
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]
def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None
res = {}
for J in Js:
    d = struct.pack('<i', J + 0x118)
    fns = set()
    for m in re.finditer(re.escape(d), seg):
        f = fn(VA + m.start())
        if f: fns.add(f)
    out = []
    for fr in sorted(fns):
        body = seg[fr[0] - VA:fr[1] - VA]
        if struct.pack('<i', J + 0x120) not in body: continue
        txt = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % fr[0],
                              '--stop-address=%#x' % fr[1], P['bin']], capture_output=True, text=True).stdout
        L = [(int(mm.group(1), 16), re.sub(r'\s*<[^>]*>', '', mm.group(2)).split('#')[0].strip())
             for l in txt.splitlines() for mm in [re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)] if mm]
        nm = {J + 0x118: 'depth', J + 0x120: 'txid', J + 0x28: 'jlen', J + 0x108: 'titems', J + 0x100: 'tgrowth', J + 0x10: 'logs', J + 0x40: 'list', J + 0x110: 'depth-8'}
        hits = []
        for x, t in L:
            for o, n in nm.items():
                if re.search(r'PTR \[\w+\+%#x\]' % o, t) and not t.startswith(('cmp', 'test')) and re.match(r'^(mov|inc|add|movups|movaps|movdqu|movdqa|vmovups|vmovdqu|and|sub|lea)\s+\w+ PTR \[', t):
                    hits.append(('%#x' % x, n, t))
        dz = [h for h in hits if h[1] in ('depth', 'depth-8')]
        tx = [h for h in hits if h[1] == 'txid' and h[2].split()[0] in ('inc', 'add')]
        if dz and tx:
            out.append(dict(fn=['%#x' % fr[0], '%#x' % fr[1]], hits=hits))
    res['%#x' % J] = out
json.dump(res, open(outp, 'w'), indent=1)
for J, o in res.items():
    print(prof, 'J', J, 'functions', len(o))
    for r in o:
        print('  ', r['fn'], [(h[0], h[1], h[2][:50]) for h in r['hits'] if h[1] in ('depth', 'txid', 'depth-8')][:6])
