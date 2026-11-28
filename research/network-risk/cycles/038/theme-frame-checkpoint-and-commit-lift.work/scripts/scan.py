"""Find every inlined journal checkpoint (journal len, log len, third len saved, depth raised) and every saturating
depth decrement in the .text of a binary, by byte patterns, then decode each site with objdump and classify it.
Reads the binary as data only. usage: python3 -I scan.py <profile> <outjson>"""
import bisect, json, re, struct, subprocess, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from bins import BINS

prof, outp = sys.argv[1], sys.argv[2]
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


def dis(lo, hi):
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, P['bin']], capture_output=True, text=True).stdout
    return [l.strip() for l in out.splitlines() if re.match(r'^\s*[0-9a-f]+:\s', l)]


def insns_from(fr, a, n_before=40, n_after=12):
    """decode the enclosing function from its start and return the instructions around address a"""
    lines = dis(fr[0], fr[1])
    idx = [i for i, l in enumerate(lines) if int(l.split(':')[0], 16) == a]
    if not idx: return None
    i = idx[0]
    return lines[max(0, i - n_before):i + n_after]


# 1. depth increments: REX.W(48/49) FF modrm(mod=10, reg=0) [SIB] disp32, or REX.W 83 modrm(mod=10,reg=0) disp32 01
inc_sites = []
for m in re.finditer(rb'[\x48\x49]\xff([\x80-\x83\x85-\x87])(....)|[\x48\x49]\xff\x84(.)(....)', seg, re.S):
    disp = struct.unpack('<i', m.group(2) or m.group(4))[0]
    if disp < 0x118: continue
    i = m.start()
    win = seg[max(0, i - 160):i]
    need = [struct.pack('<i', disp - d) for d in (0x108, 0xf0, 0xd8)]
    if all(x in win for x in need):
        inc_sites.append((VA + i, disp))
fr_cache = {}
res = dict(profile=prof, bin=P['bin'], text=[VA, SZ], checkpoints=[], decrements=[])
for a, disp in inc_sites:
    fr = fn(a)
    ctx = insns_from(fr, a) if fr else None
    ok = False; loads = {}
    if ctx:
        # the enclosing decode must contain the inc at a, and loads of the three lengths from the same base
        J = disp - 0x118
        for l in ctx:
            mm = re.search(r'mov\s+(\w+),QWORD PTR \[(\w+)\+(0x[0-9a-f]+)\]$', l)
            if mm and int(mm.group(3), 16) in (J + 0x10, J + 0x28, J + 0x40):
                loads[int(mm.group(3), 16) - J] = (mm.group(2), l)
            mm = re.search(r'lea\s+(\w+),\[(\w+)\+(0x[0-9a-f]+)\]$', l)
        ok = len(loads) == 3 and any(('%x:' % a) in l and 'inc' in l for l in ctx)
    res['checkpoints'].append(dict(addr='%#x' % a, J='%#x' % (disp - 0x118), fn=fr and ['%#x' % fr[0], '%#x' % fr[1]],
                                   ooc=bool(fr and fr[0] == P['ooc_checkpoint']), three_loads=ok,
                                   ctx=ctx and [l for l in ctx if any(('+%#x]' % (disp - 0x118 + o)) in l for o in (0x10, 0x28, 0x40, 0x118))]))
# 2. saturating decrements of every depth word found: load [r+D], (cmp r,1; adc r,-1) | (sub r,1; cmovae) |
#    (test; je; dec), store [r+D]
Ds = sorted({d for _, d in inc_sites} | {0x118})
dec = []
for D in Ds:
    pk = struct.pack('<i', D)
    i = seg.find(pk)
    while i >= 0:
        j = seg.find(pk, i + 4, i + 48)
        if j > 0:
            body = seg[i:j]
            if (b'\x83\xf8\x01' in body or re.search(rb'\x48\x83[\xf8-\xff]\x01', body) or
                    re.search(rb'\x48\x83[\xe8-\xef]\x01', body) or re.search(rb'\x48\x83[\xd0-\xd7]\xff', body)):
                dec.append((VA + i - 3, D))
        i = seg.find(pk, i + 1)
seen = set()
for a0, D in dec:
    fr = fn(a0)
    if not fr: continue
    lines = dis(max(fr[0], a0 - 8), min(fr[1], a0 + 60))
    # keep the first load of [..+D] and the instructions up to its store
    sel = []; started = False
    for l in lines:
        if ('+%#x]' % D) in l and not started and 'mov' in l and l.split('\t')[-1].startswith('mov') and ',QWORD PTR' in l:
            started = True
        if started:
            sel.append(l)
            if ('QWORD PTR [' in l and ('+%#x],' % D) in l): break
    if not sel or len(sel) > 8: continue
    key = sel[0].split(':')[0]
    if key in seen: continue
    seen.add(key)
    txt = ' ; '.join(x.split('\t', 1)[-1] for x in sel)
    kind = ('cmp1-adc' if re.search(r'cmp\s+\w+,0x1 ; adc\s+\w+,0xffffffffffffffff', txt) else
            'sub1-cmovae' if re.search(r'sub\s+\w+,0x1 ; cmovae', txt) else 'other')
    res['decrements'].append(dict(addr=key, D='%#x' % D, fn=['%#x' % fr[0], '%#x' % fr[1]],
                                  ooc=fr[0] == P['ooc_commit'], kind=kind, text=txt))
json.dump(res, open(outp, 'w'), indent=1)
print(prof, 'checkpoint sites', len(res['checkpoints']), 'with three loads', sum(c['three_loads'] for c in res['checkpoints']),
      'decrements', len(res['decrements']), {k: sum(1 for d in res['decrements'] if d['kind'] == k) for k in ('cmp1-adc', 'sub1-cmovae', 'other')})
