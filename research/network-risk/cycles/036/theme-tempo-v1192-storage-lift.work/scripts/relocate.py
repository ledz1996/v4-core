"""Relocates routines of tempo v1.19.1 x86_64 to v1.19.2 x86_64 by walking both disassemblies in parallel.

Starting from function pairs given on the command line (old:new), it disassembles each old function over its
FDE range and the new one from the paired address over the paired FDE range, zips the instruction streams,
requires that each pair is equal after absolute addresses are masked, and records every absolute operand
(branch and call targets, rip-relative data) as an old->new address pair. Call targets found this way are
added to the work list, so the closure of the callees is relocated too. Nothing is executed.

usage: python3 -I relocate.py <old bin> <old fde> <new bin> <new fde> <out.json> old:new [old:new ...]
"""
import bisect, json, re, subprocess, sys

OB, OF, NB, NF, OUT = sys.argv[1:6]
SEEDS = [tuple(int(x, 16) for x in s.split(':')) for s in sys.argv[6:]]


def fde(p):
    f = []
    for l in open(p):
        a, b = re.split(r'\.\.\.?', l.strip()); f.append((int(a, 16), int(b, 16)))
    f.sort(); return f, [a for a, b in f]


def frange(F, a):
    f, s = F; k = bisect.bisect_right(s, a) - 1
    if k >= 0 and f[k][0] <= a < f[k][1]: return f[k]
    return None


def dis(b, lo, hi):
    t = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=' + hex(lo),
                        '--stop-address=' + hex(hi), b], capture_output=True, text=True).stdout
    out = []
    for l in t.splitlines():
        m = re.match(r'^ *([0-9a-f]+):\t(.*)$', l)
        if m: out.append((int(m.group(1), 16), m.group(2)))
    return out


HEX = re.compile(r'\b(?:0x)?([0-9a-f]{5,})\b')


def consts(t):
    m = re.search(r'#\s*(?:0x)?([0-9a-f]+)', t)
    rip = [int(m.group(1), 16)] if m else []
    body = re.sub(r'#.*', '', re.sub(r'<[^>]*>', '', t))
    br = []
    if re.match(r'^\s*(j\w+|call)\s+([0-9a-f]+)\s*$', body):
        br = [int(body.split()[-1], 16)]
    return rip, br, HEX.sub('ADDR', re.sub(r'\[rip\+0x[0-9a-f]+\]', '[rip+R]', body)).strip()


def main():
    OFd, NFd = fde(OF), fde(NF)
    amap = {}; fmap = {}; diffs = []; work = list(SEEDS); done = set(); nins = 0
    while work:
        o, n = work.pop()
        if o in done: continue
        done.add(o)
        ro, rn = frange(OFd, o), frange(NFd, n)
        if not ro or not rn or ro[0] != o or rn[0] != n:
            diffs.append({'old': hex(o), 'new': hex(n), 'what': 'not a function start (fragment); entry mapped only'})
            amap[o] = n; continue
        a, b = dis(OB, *ro), dis(NB, *rn)
        fmap[hex(o)] = [hex(n), ro[1] - ro[0], rn[1] - rn[0]]
        if len(a) != len(b):
            diffs.append({'old': hex(o), 'new': hex(n), 'what': 'length %d/%d' % (len(a), len(b))}); continue
        for (pa, ta), (pb, tb) in zip(a, b):
            nins += 1
            amap[pa] = pb
            ra, ba, na = consts(ta); rb, bb, nb = consts(tb)
            if na != nb:
                diffs.append({'old': hex(pa), 'new': hex(pb), 'what': ta.strip() + ' | ' + tb.strip()})
            for x, y in zip(ra, rb): amap.setdefault(x, y)
            for x, y in zip(ba, bb):
                amap.setdefault(x, y)
                if ta.split()[0] == 'call' and not (ro[0] <= x < ro[1]): work.append((x, y))
    json.dump({'functions': fmap, 'instructions': nins, 'diffs': diffs,
               'map': {hex(k): hex(v) for k, v in sorted(amap.items())}}, open(OUT, 'w'), indent=0)
    print('functions', len(fmap), 'instructions', nins, 'diffs', len(diffs))
    for d in diffs: print(' ', d)


main()
