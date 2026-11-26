"""Decode, for both builds, which asmjit instruction each Comparison value (0..9) selects in the functions
where the id comes from a table: conditional jumps and setcc. Data reads only.
usage: python3 -I cctable.py <package elf> <package.s> <harness obj> <harness.s> <names.json> <out.json>"""
import sys, re, json, struct, subprocess
pelf, ps, hobj, hs, names, out = sys.argv[1:7]
nm = {int(k, 16): v for k, v in json.load(open(names)).items()}
FUN = ['Emitter::conditional_jmp(', 'Emitter::discharge_deferred_comparison(monad', 'Emitter::jumpi_spill_fallthrough_stack(', 'Emitter::jumpi_keep_fallthrough_stack(']
def blocks(path):
    cur = None; B = {}
    for line in open(path, errors='replace'):
        m = re.match(r'^([0-9a-f]+) <(.*)>:\s*$', line)
        if m:
            cur = None
            for f in FUN:
                if f in m.group(2): cur = f; B.setdefault(f, [])
            continue
        if cur: B[cur].append(line.rstrip('\n'))
    return B
def secmap(path):
    o = subprocess.run(['readelf', '-S', '-W', path], capture_output=True, text=True).stdout
    S = []
    for m in re.finditer(r'\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', o):
        S.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16), int(m.group(4), 16)))
    return S
pdata = open(pelf, 'rb').read(); PS = secmap(pelf)
def pread(addr, n):
    for name, a, off, sz in PS:
        if a and a <= addr < a + sz: return pdata[off + addr - a: off + addr - a + n]
res = {}
PB = blocks(ps)
for f, lines in PB.items():
    ins = []
    for l in lines:
        m = re.match(r'^\s+([0-9a-f]+):\s+(.*)$', l)
        if m: ins.append((int(m.group(1), 16), m.group(2)))
    maps = []
    for i, (a, t) in enumerate(ins):
        m = re.match(r'lea\s+(\w+),\[rip\+0x[0-9a-f]+\]\s+#\s+([0-9a-f]+)', t)
        if not m: continue
        nxt = ' '.join(x[1] for x in ins[i + 1:i + 5])
        if 'movsxd' in nxt and 'jmp' in ' '.join(x[1] for x in ins[i + 1:i + 7]):
            tab = int(m.group(2), 16)
            vals = struct.unpack('<10i', pread(tab, 40))
            mp = []
            for v in vals:
                tgt = (tab + v) & (2 ** 64 - 1)
                j = [k for k, (aa, tt) in enumerate(ins) if aa >= tgt][0]
                sid = None
                for aa, tt in ins[j:j + 12]:
                    mm = re.match(r'mov\s+esi,(0x[0-9a-f]+)$', tt)
                    if mm: sid = int(mm.group(1), 16); break
                mp.append(nm.get(sid))
            maps.append(mp)
    res.setdefault(f, {})['package'] = maps
hdata = open(hobj, 'rb').read(); HS = secmap(hobj)
rod = [x for x in HS if x[0] == '.rodata'][0]
HB = blocks(hs)
for f, lines in HB.items():
    maps = []
    for i, l in enumerate(lines):
        m = re.search(r'R_X86_64_PC32\s+\.rodata\+0x([0-9a-f]+)', l)
        if not m: continue
        win = ' '.join(lines[i + 1:i + 4])
        if re.search(r'mov\s+(esi|edx),DWORD PTR \[\w+\+\w+\*4\]', win):
            off = int(m.group(1), 16) + 4
            vals = struct.unpack('<10i', hdata[rod[2] + off: rod[2] + off + 40])
            maps.append([nm.get(v) if v > 20 else ('cmp%d' % v) for v in vals])
    res.setdefault(f, {})['harness'] = maps
json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items(): print(k, v)
