"""Find the inlined end-of-transaction routines (commit_tx, discard_tx, finalize) of a binary: every function that
stores zero to a depth word J+0x118 and also zeroes the journal length J+0x28 for the same J, with the transaction id
word J+0x120 changed nearby. Decodes each site and prints the stores to J..J+0x130 in program order. Reads only.
usage: python3 -I txclear.py <profile> <out.json>"""
import bisect, json, re, struct, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bins import BINS
prof, outp = sys.argv[1:3]
P = BINS[prof]
b = open(P['bin'], 'rb').read()
for l in subprocess.run(['readelf', '-SW', P['bin']], capture_output=True, text=True).stdout.splitlines():
    m = re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
    if m: VA, OFF, SZ = (int(x, 16) for x in m.groups())
seg = b[OFF:OFF + SZ]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]


def fn(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k] if k >= 0 and F[k][0] <= a < F[k][1] else None


# mov QWORD PTR [r+disp32], 0 : REX.W(48/49) C7 modrm(mod=10, reg=0) [SIB] disp32 imm32=0
cands = {}
for m in re.finditer(rb'[\x48\x49]\xc7([\x80-\x83\x85-\x87])(....)\x00\x00\x00\x00|[\x48\x49]\xc7\x84(.)(....)\x00\x00\x00\x00', seg, re.S):
    disp = struct.unpack('<i', m.group(2) or m.group(4))[0]
    if disp < 0x118: continue
    a = VA + m.start(); fr = fn(a)
    if fr: cands.setdefault(fr, set()).add(disp)
res = []
for fr, ds in sorted(cands.items()):
    Js = [d - 0x118 for d in ds]
    if not Js: continue
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % fr[0],
                          '--stop-address=%#x' % fr[1], P['bin']], capture_output=True, text=True).stdout
    L = [(int(mm.group(1), 16), re.sub(r'\s*<[^>]*>', '', mm.group(2)).split('#')[0].strip())
         for l in out.splitlines() for mm in [re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)] if mm]
    for J in Js:
        offs = {J + 0x118: 'depth', J + 0x28: 'journal_len', J + 0x10: 'logs_len', J + 0x40: 'list_len', J + 0x120: 'txid',
                J + 0xf0: 'tmap_ctrl', J + 0xf8: 'tmap_mask', J + 0x100: 'tmap_growth', J + 0x108: 'tmap_items'}
        hits = []
        for x, t in L:
            for o, nm in offs.items():
                if re.search(r'\[\w+\+%#x\]' % o, t):
                    hits.append(('%#x' % x, nm, t))
        z = [h for h in hits if h[1] == 'depth' and h[2].endswith(',0x0')]
        jz = [h for h in hits if h[1] == 'journal_len' and (h[2].endswith(',0x0') or re.search(r'mov\s+QWORD PTR \[.*\],r\w+$', h[2]))]
        tx = [h for h in hits if h[1] == 'txid']
        if z and jz and tx:
            res.append(dict(fn=['%#x' % fr[0], '%#x' % fr[1]], J='%#x' % J, depth_zero=[h[0] for h in z],
                            txid=[(h[0], h[2]) for h in tx], tmap=[(h[0], h[1], h[2]) for h in hits if h[1].startswith('tmap')],
                            all=[(h[0], h[1], h[2]) for h in hits]))
json.dump(res, open(outp, 'w'), indent=1)
for r in res:
    print(r['fn'], 'J', r['J'], 'depth=0 at', r['depth_zero'][:3], 'txid', r['txid'][:3], 'tmap writes', len(r['tmap']))
