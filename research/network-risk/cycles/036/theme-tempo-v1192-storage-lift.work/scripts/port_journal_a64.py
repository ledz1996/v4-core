"""Builds the v1.19.2 aarch64 port of cycle 30's journal_a64.py (Task 4), as port_journal.py does for x86_64.

Writes each routine's v1.19.2 disassembly (llvm-objdump, instruction lines only) at the address relocate_a64.py
found, rewrites every code address of journal_a64.py through the relocation map, moves the hash secret writes to the
secret's v1.19.2 page offset (the page offset of the words the hash loads moved from +0x210 to +0xb90, so the
block written at +0x200 moves to +0xb80), and sets the new ELF bounds. Prints every substitution.

usage: python3 -I port_journal_a64.py <new bin> <reloc_a64.json> <old journal_a64.py> <build dir> <out script>
"""
import json, re, subprocess, sys

NB, RJ, SRC, BUILD, OUT = sys.argv[1:6]
R = json.load(open(RJ))
amap = {int(k, 16): int(v, 16) for k, v in R['map'].items()}
funcs = [(int(k, 16), int(k, 16) + lo, int(v, 16)) for k, (v, lo, ln) in R['functions'].items()]


def reloc(a):
    if a in amap: return amap[a], 'exact'
    for lo, hi, n in funcs:
        if lo <= a <= hi: return a - lo + n, 'delta'
    return None, None


FILES = {'a64_tstore_host.s': 0x1d975ac, 'a64_0x1d97914.s': 0x1d97914, 'a64_0x1dc85d4.s': 0x1dc85d4, 'a64_0x1d97448.s': 0x1d97448,
         'a64_rollback.s': 0x1d98170, 'a64_0x1d98608.s': 0x1d98608, 'a64_0x1d9883c.s': 0x1d9883c, 'a64_sstore.s': 0x3b563d4}
src = open(SRC).read()
for f, o in FILES.items():
    lo, hi, n = next(x for x in funcs if x[0] == o)
    t = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', '--start-address=' + hex(n), '--stop-address=' + hex(n + hi - lo), NB],
                       capture_output=True, text=True).stdout
    nn = 'a64v2_%x.s' % n
    open(BUILD + '/' + nn, 'w').write('\n'.join(l for l in t.splitlines() if re.match(r'^ *[0-9a-f]+:\s', l)) + '\n')
    src = src.replace("'%s'" % f, "'%s'" % nn)
subs = []
head, body = src.split('class CPU(_CPU):', 1)
head = head.replace("sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')", "sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')\nsys.path.insert(1, '/home/user/v4-core/research/network-risk/cycles/030/theme-tempo-binary-storage-journal.work/scripts')")


def sub(m):
    s = m.group(0); a = int(s, 16)
    if a < 0x1880000 or a >= 0x5c00000 and a not in (0x5c66c30, 0x5c66bd0): return s
    n, how = reloc(a)
    if n is None: subs.append((s, 'UNMAPPED')); return s
    subs.append((s, hex(n), how)); return hex(n)


body = body.replace('Mem(fb, 0, 0x18742d8 + 0x43e2ed0)', 'Mem(fb, 0, 0x187c5c8 + 0x440c9a0)')
body = body.replace('SECRET = 0x5e84000', 'SECRET = 0x5eb6000')
body = body.replace('self.m.write(SECRET + 0x200 + i, 8', 'self.m.write(SECRET + 0xb80 + i, 8')
body = re.sub(r'(?<![0-9a-fx])0x[0-9a-f]{6,8}\b', sub, body)
open(OUT, 'w').write('"""PORTED TO v1.19.2 aarch64 by cycle 36 port_journal_a64.py (addresses relocated)."""\n' + head + 'class CPU(_CPU):' + body)
for s in subs: print(*s)
assert 'SECRET + 0xb80' in body and '0x187c5c8' in body
