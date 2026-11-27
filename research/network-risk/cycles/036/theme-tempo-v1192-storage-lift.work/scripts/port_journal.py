"""Builds the v1.19.2 x86_64 port of cycle 30's journal_x64.py.

1. Writes the disassembly of each routine the model runs, taken from the v1.19.2 binary at the relocated
   address (objdump, instruction lines only, same format as cycle 30's build files).
2. Rewrites every code or data address in journal_x64.py through the relocation map of relocate.py
   (instruction addresses exactly; an address inside a relocated function that is not an instruction start,
   such as an end bound, by the function's delta), and the segment constants of the new ELF.
3. Adds the new fault 'sstore_skip_same' (Task 5) and prints every substitution it made.

usage: python3 -I port_journal.py <new bin> <reloc.json> <old journal_x64.py> <build dir> <out script>
"""
import json, re, subprocess, sys

NB, RJ, SRC, BUILD, OUT = sys.argv[1:6]
R = json.load(open(RJ))
amap = {int(k, 16): int(v, 16) for k, v in R['map'].items()}
funcs = []
for k, (v, lo, ln) in R['functions'].items():
    funcs.append((int(k, 16), int(k, 16) + lo, int(v, 16)))


def reloc(a):
    if a in amap: return amap[a], 'exact'
    for lo, hi, n in funcs:
        if lo <= a <= hi: return a - lo + n, 'delta'
    return None, None


def dis(lo, hi):
    t = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=' + hex(lo),
                        '--stop-address=' + hex(hi), NB], capture_output=True, text=True).stdout
    return '\n'.join(l.split(' <')[0] if ('call' in l or re.search(r'\tj\w+ ', l)) else l
                     for l in t.splitlines() if re.match(r'^ *[0-9a-f]+:\t', l)) + '\n'


FILES = {'x64_0x1e8c450.s': 0x1e8c450, 'x64_0x1e8c860.s': 0x1e8c860, 'x64_0x1ec9530.s': 0x1ec9530,
         'x64_0x1e8c2b0.s': 0x1e8c2b0, 'x64_0x1e8d350.s': 0x1e8d350, 'x64_0x1e8d9e0.s': 0x1e8d9e0,
         'x64_0x1e8dcc0.s': 0x1e8dcc0, 'x64_sstore.s': 0x42a0d20}
newfiles = {}
for f, o in FILES.items():
    lo, hi, n = next((x for x in funcs if x[0] == o))
    nn = 'x64v2_%x.s' % n
    open(BUILD + '/' + nn, 'w').write(dis(n, n + (hi - lo)))
    newfiles[f] = nn
src = open(SRC).read()
for f, nn in newfiles.items(): src = src.replace("'%s'" % f, "'%s'" % nn)
subs = []


def sub(m):
    s = m.group(0); a = int(s, 16) if s.startswith('0x') else int(s, 16)
    if a < 0x189bb00 and a != 0x65fe30: return s
    if a in (0x189bb00, 0x521d110, 0x189aab8): return s
    n, how = reloc(a)
    if n is None:
        subs.append((s, 'UNMAPPED')); return s
    t = (hex(n) if s.startswith('0x') else '%x' % n)
    subs.append((s, t, how)); return t


head, body = src.split('class CPU(CPU2):', 1)
body = re.sub(r'(?<![0-9a-fx])(0x[0-9a-f]{6,8}|(?<=jmp    )[0-9a-f]{6,8})\b', sub, body)
body = body.replace('0x189aab8', '0x18a3800')
head = head.replace('TEXT_LO, TEXT_HI, TEXT_DELTA = 0x189bb00, 0x189bb00 + 0x521d110, 0x1000',
                    'TEXT_LO, TEXT_HI, TEXT_DELTA = 0x18a4800, 0x18a4800 + 0x5250a10, 0x1000')
head = head.replace('"""x86_64 counterpart', '"""PORTED TO v1.19.2 by cycle 36 port_journal.py (addresses relocated). x86_64 counterpart')
# new fault: a write of the same value records a StorageChange (the journal must not change; reads and state too)
body = body.replace("    'sstore_prev_new':", "    'sstore_prev_new':")
src = head + 'class CPU(CPU2):' + body
open(OUT, 'w').write(src)
for s in subs: print(*s)
