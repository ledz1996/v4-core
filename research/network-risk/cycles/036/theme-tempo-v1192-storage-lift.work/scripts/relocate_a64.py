"""aarch64 counterpart of relocate.py: relocates routines of tempo v1.19.1 aarch64 to v1.19.2 aarch64.

Each seed is an old address; its new address is found among the v1.19.2 FDEs of the same length whose normalized
instruction stream equals the old one (or, failing that, differs least). The closure of the callees (bl targets) is
then walked in parallel. Normalization masks absolute addresses (5+ hex digits) and symbol comments. Instruction pairs
that still differ are reported; an add/ldr/str immediate right after an adrp of the same register is classed as a
page offset (data relocation) when the full adrp+offset address maps to equal bytes in both files.
Nothing is executed.

usage: python3 -I relocate_a64.py <old bin> <old fde> <new bin> <new fde> <out.json> <old hex>...
"""
import bisect, json, re, subprocess, sys

OB, OF, NB, NF, OUT = sys.argv[1:6]
SEEDS = [int(x, 16) for x in sys.argv[6:]]


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
    t = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', '--start-address=' + hex(lo), '--stop-address=' + hex(hi), b],
                       capture_output=True, text=True).stdout
    out = []
    for l in t.splitlines():
        m = re.match(r'^ *([0-9a-f]+):\s+(.*)$', l)
        if m: out.append((int(m.group(1), 16), m.group(2).split('<')[0].split('//')[0].strip()))
    return out


HEX = re.compile(r'\b0x([0-9a-f]{5,})\b')


def norm(t): return HEX.sub('ADDR', t)


def absops(t): return [int(x, 16) for x in HEX.findall(t)]


class F:
    def __init__(self, p):
        self.raw = open(p, 'rb').read()
        import struct
        e_phoff = struct.unpack_from('<Q', self.raw, 0x20)[0]; n = struct.unpack_from('<H', self.raw, 0x38)[0]
        self.loads = []
        for i in range(n):
            typ, fl, off, va, pa, fsz, msz, al = struct.unpack_from('<IIQQQQQQ', self.raw, e_phoff + 56 * i)
            if typ == 1: self.loads.append((va, va + fsz, off))

    def at(self, va, n):
        for lo, hi, off in self.loads:
            if lo <= va < hi: return self.raw[off + va - lo: off + va - lo + n]
        return None


def main():
    OFd, NFd = fde(OF), fde(NF)
    of, nf = F(OB), F(NB)
    bylen = {}
    for a, b in NFd[0]: bylen.setdefault(b - a, []).append(a)
    work = []
    seedmap = {}
    for o in SEEDS:
        ro = frange(OFd, o); a = dis(OB, *ro); na = [norm(t) for _, t in a]
        best = None
        for c in bylen.get(ro[1] - ro[0], []):
            b = dis(NB, c, c + ro[1] - ro[0]); nb = [norm(t) for _, t in b]
            d = sum(1 for x, y in zip(na, nb) if x != y) + abs(len(na) - len(nb))
            if best is None or d < best[0]: best = (d, c)
            if d == 0: break
        seedmap[hex(o)] = [hex(best[1]), best[0]] if best else None
        if best: work.append((o, best[1]))
    amap = {}; fmap = {}; diffs = []; done = set(); nins = 0; pageoffs = 0
    while work:
        o, n = work.pop()
        if o in done: continue
        done.add(o)
        ro, rn = frange(OFd, o), frange(NFd, n)
        if not ro or not rn or ro[0] != o or rn[0] != n:
            diffs.append({'old': hex(o), 'new': hex(n), 'what': 'not a function start; entry mapped only'}); amap[o] = n; continue
        a, b = dis(OB, *ro), dis(NB, *rn)
        fmap[hex(o)] = [hex(n), ro[1] - ro[0], rn[1] - rn[0]]
        if len(a) != len(b):
            diffs.append({'old': hex(o), 'new': hex(n), 'what': 'length %d/%d' % (len(a), len(b))}); continue
        lastadrp = {}
        for (pa, ta), (pb, tb) in zip(a, b):
            nins += 1; amap[pa] = pb
            if norm(ta) != norm(tb):
                # page offset after adrp of the same register?
                mo = re.match(r'^(add|ldr|ldrb|ldrh|str|ldp|stp)\s+(\w+), .*\[?(x\d+)\]?.*#0x([0-9a-f]+)', ta)
                ok = False
                ma, mb = re.findall(r'#0x([0-9a-f]+)', ta), re.findall(r'#0x([0-9a-f]+)', tb)
                ra = re.findall(r'\b(x\d+)\b', ta)
                if ma and mb and re.sub(r'#0x[0-9a-f]+', '#I', ta) == re.sub(r'#0x[0-9a-f]+', '#I', tb):
                    for r in ra:
                        if r in lastadrp:
                            pa_, pb_ = lastadrp[r]
                            xa, xb = pa_ + int(ma[-1], 16), pb_ + int(mb[-1], 16)
                            ba, bb = of.at(xa, 16), nf.at(xb, 16)
                            amap.setdefault(xa, xb); ok = True; pageoffs += 1
                            if ba != bb: diffs.append({'old': hex(pa), 'new': hex(pb), 'what': 'data %x/%x bytes differ (may be a pointer): %s | %s' % (xa, xb, ta, tb)})
                            break
                if not ok: diffs.append({'old': hex(pa), 'new': hex(pb), 'what': ta + ' | ' + tb})
            xs, ys = absops(ta), absops(tb)
            if ta.startswith('adrp') and xs and ys:
                lastadrp[ta.split()[1].rstrip(',')] = (xs[0], ys[0])
            for x, y in zip(xs, ys):
                amap.setdefault(x, y)
                if ta.startswith('bl\t') or ta.startswith('bl '):
                    if not (ro[0] <= x < ro[1]): work.append((x, y))
    json.dump({'seeds': seedmap, 'functions': fmap, 'instructions': nins, 'pageOffsets': pageoffs, 'diffs': diffs,
               'map': {hex(k): hex(v) for k, v in sorted(amap.items())}}, open(OUT, 'w'), indent=0)
    print('seeds', seedmap); print('functions', len(fmap), 'instructions', nins, 'pageoffs', pageoffs, 'diffs', len(diffs))
    for d in diffs[:60]: print(' ', d)


main()
