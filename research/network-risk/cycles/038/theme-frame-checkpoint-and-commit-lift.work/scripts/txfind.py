"""Locate the inlined commit_tx / discard_tx / finalize blocks of a binary for the journal offsets J of its frame
code (from cls-<profile>.json): functions that store 0 to J+0x118 and also write the journal length J+0x28, the
transient map items word J+0x108 and the transaction id J+0x120. Prints each block's writes in order. Reads only.
usage: python3 -I txfind.py <profile> <cls.json> <out.json>"""
import bisect, json, re, struct, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bins import BINS
prof, clsf, outp = sys.argv[1:4]
P = BINS[prof]
Js = sorted({int(c['J'], 16) for c in json.load(open(clsf))['checkpoints'] if c['cls'].get('ok')})
b = open(P['bin'], 'rb').read()
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]
def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None
res = []
for J in Js:
    pat = re.compile(rb'[\x48\x49]\xc7[\x80-\x83\x85-\x87]' + re.escape(struct.pack('<i', J + 0x118)) + rb'\x00\x00\x00\x00', re.S)
    fns = {fn(VA + m.start()) for m in pat.finditer(seg)} - {None}
    for fr in sorted(fns):
        body = seg[fr[0] - VA:fr[1] - VA]
        if not all(struct.pack('<i', J + o) in body for o in (0x28, 0x108, 0x120)): continue
        out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % fr[0],
                              '--stop-address=%#x' % fr[1], P['bin']], capture_output=True, text=True).stdout
        L = [(int(mm.group(1), 16), re.sub(r'\s*<[^>]*>', '', mm.group(2)).split('#')[0].strip())
             for l in out.splitlines() for mm in [re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)] if mm]
        names = {J + 0x118: 'depth', J + 0x28: 'journal_len', J + 0x10: 'logs_len', J + 0x40: 'list_len', J + 0x120: 'txid',
                 J + 0x108: 'tmap_items', J + 0x100: 'tmap_growth'}
        w = [('%#x' % x, names[o], t) for x, t in L for o in names if re.search(r'\[\w+\+%#x\],' % o, t) or (names[o] == 'txid' and '+%#x]' % o in t and t.split()[0] in ('inc', 'dec', 'add', 'sub'))]
        kinds = [h[1] for h in w]
        res.append(dict(fn=['%#x' % fr[0], '%#x' % fr[1]], J='%#x' % J, writes=w,
                        complete=all(k in kinds for k in ('depth', 'journal_len', 'logs_len', 'list_len', 'txid', 'tmap_items'))))
json.dump(res, open(outp, 'w'), indent=1)
for r in res:
    tx = [h[2] for h in r['writes'] if h[1] == 'txid']
    print(prof, r['fn'], 'J', r['J'], 'complete', r['complete'], 'txid', sorted(set(re.sub(r'r\w\w?\+', 'R+', t) for t in tx))[:3])
