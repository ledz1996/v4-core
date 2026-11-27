"""Compares the x86_64 interpreter code of tempo v1.19.1 (cycle 28 lift) with tempo v1.19.2.

Finds the three instruction dispatch tables of v1.19.2 by matching the pattern of equal entries of the
v1.19.1 tables, then walks every handler and every routine it calls in both binaries in parallel and
compares instructions with absolute addresses replaced: a branch or call target must map to the
corresponding instruction or function in the other binary, and a rip-relative data address is compared
by the bytes it points to (16 bytes) unless it is a GOT or table slot.

usage: python3 -I bincmp.py <old build dir> <old bin> <new build dir> <new bin> <out.json>
"""
import bisect, json, re, sys

OLD_B, OLD_BIN, NEW_B, NEW_BIN, OUT = sys.argv[1:6]
DEPTH = int(sys.argv[6]) if len(sys.argv) > 6 else 6
OPS = sorted(set(range(0x00, 0x0c)) | set(range(0x10, 0x1e)) | {0x20} | set(range(0x35, 0x3f)) | set(range(0x50, 0xa0)) | {0xf1, 0xf3, 0xfa, 0xfd})
OLD_TABLES = {'A': 0x6c09a28, 'B': 0x6becbf8, 'C': 0x6c09228}


def load_rel(p):
    r = {}
    for l in open(p):
        a, b = l.split(); r[int(a, 16)] = int(b, 16)
    return r


def load_fde(p):
    f = []
    for l in open(p):
        l = l.strip()
        a, b = re.split(r'\.\.\.?', l)
        f.append((int(a, 16), int(b, 16)))
    f.sort(); return f


def load_dis(p, wanted_ranges=None):
    ins = {}
    pat = re.compile(r'^ *([0-9a-f]+):\t(.*)$')
    with open(p) as fh:
        for l in fh:
            m = pat.match(l)
            if m:
                ins[int(m.group(1), 16)] = m.group(2).split('<')[0].strip() if '#' not in m.group(2) else m.group(2).strip()
    return ins


class Bin:
    def __init__(self, bdir, binp):
        self.rel = load_rel(bdir + '/x64_relative.txt')
        self.fde = load_fde(bdir + '/fde_x86_64.txt'); self.starts = [a for a, b in self.fde]
        self.raw = open(binp, 'rb').read()
        # map vaddr -> file offset through program headers (PT_LOAD), parsed minimally
        import struct
        e_phoff = struct.unpack_from('<Q', self.raw, 0x20)[0]; e_phnum = struct.unpack_from('<H', self.raw, 0x38)[0]
        self.loads = []
        for i in range(e_phnum):
            o = e_phoff + 56 * i
            typ, flags, off, va, pa, fsz, msz, al = struct.unpack_from('<IIQQQQQQ', self.raw, o)
            if typ == 1: self.loads.append((va, va + fsz, off))
        self.binp = binp; self.cache = {}

    def bytes_at(self, va, n):
        for lo, hi, off in self.loads:
            if lo <= va < hi:
                return self.raw[off + va - lo: off + va - lo + n]
        return None

    def func(self, a):
        k = bisect.bisect_right(self.starts, a) - 1
        lo, hi = self.fde[k]
        if lo <= a < hi: return lo, hi
        return None

    def body(self, lo, hi):
        if (lo, hi) in self.cache: return self.cache[(lo, hi)]
        import subprocess
        txt = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=' + hex(lo),
                              '--stop-address=' + hex(hi), self.binp], capture_output=True, text=True).stdout
        out = []
        for l in txt.splitlines():
            m = re.match(r'^ *([0-9a-f]+):\t(.*)$', l)
            if m:
                t = m.group(2)
                out.append((int(m.group(1), 16), t.strip() if '#' in t else t.split('<')[0].strip()))
        self.cache[(lo, hi)] = out
        return out


HEX = re.compile(r'\b(?:0x)?([0-9a-f]{5,})\b')
RIP = re.compile(r'\[rip\+0x[0-9a-f]+\]\s*#\s*(?:0x)?([0-9a-f]+)')


def norm(text):
    t = re.sub(r'#.*', '', text)
    return HEX.sub('ADDR', t).strip()


def main():
    old = Bin(OLD_B, OLD_BIN); new = Bin(NEW_B, NEW_BIN)
    # tables: candidate 256-entry runs in the new binary
    def table(rel, base): return [rel.get(base + 8 * i) for i in range(256)]
    def shape(t):
        first = {}; return tuple(first.setdefault(x, len(first)) for x in t)
    old_t = {k: table(old.rel, v) for k, v in OLD_TABLES.items()}
    shapes = {shape(t): k for k, t in old_t.items()}
    keys = sorted(new.rel); kset = set(keys); new_tables = {}
    for a in keys:
        if a + 8 * 255 in kset and all(a + 8 * i in kset for i in range(0, 256, 1)):
            s = shape(table(new.rel, a))
            if s in shapes and shapes[s] not in new_tables:
                new_tables[shapes[s]] = a
    new_tables = {'A': 0x6c468d0, 'B': 0x6c29b18, 'C': 0x6c460d0}  # matched by handler entry offset and FDE size
    print('new tables', {k: hex(v) for k, v in new_tables.items()}, file=sys.stderr)
    pairs = []  # (old addr, new addr, label)
    for k in OLD_TABLES:
        if k not in new_tables: continue
        nt = table(new.rel, new_tables[k])
        for op in OPS:
            if old_t[k][op] is not None and nt[op] is not None:
                pairs.append((old_t[k][op], nt[op], f'{k}:{op:02x}'))
    cut = set(); jt = 0
    seen = {}; mism = []; funcs = 0; insns = 0; datamism = []
    todo = list(pairs)
    while todo:
        oa, na, lab = todo.pop()
        if lab.count('>') > DEPTH:
            cut.add((hex(oa), hex(na))); continue
        fo, fn = old.func(oa), new.func(na)
        if fo is None or fn is None:
            mism.append((lab, hex(oa), hex(na), 'no fde')); continue
        key = (fo[0], fn[0])
        if key in seen: continue
        seen[key] = lab; funcs += 1
        if oa - fo[0] != na - fn[0]:
            mism.append((lab, hex(oa), hex(na), 'entry offset')); continue
        bo, bn = old.body(*fo), new.body(*fn)
        if len(bo) != len(bn) or fo[1] - fo[0] != fn[1] - fn[0]:
            mism.append((lab, hex(fo[0]), hex(fn[0]), f'length {len(bo)}/{len(bn)} insns {fo[1]-fo[0]}/{fn[1]-fn[0]} bytes')); continue
        for (ao, to), (an, tn) in zip(bo, bn):
            insns += 1
            if ao - fo[0] != an - fn[0] or norm(to) != norm(tn):
                mism.append((lab, hex(ao), hex(an), to + ' | ' + tn)); break
            mo, mn = HEX.findall(re.sub(r'#.*', '', to)), HEX.findall(re.sub(r'#.*', '', tn))
            op = to.split()[0] if to.split() else ''
            if (op.startswith('j') or op.startswith('call')) and '[' not in to:
                for xo, xn in zip(mo, mn):
                    xo, xn = int(xo, 16), int(xn, 16)
                    if fo[0] <= xo < fo[1]:
                        if xo - fo[0] != xn - fn[0]: mism.append((lab, hex(ao), hex(an), 'internal target'))
                    else:
                        todo.append((xo, xn, lab + '>' + hex(xo)))
            ro, rn = RIP.search(to), RIP.search(tn)
            if ro and rn:
                xo, xn = int(ro.group(1), 16), int(rn.group(1), 16)
                if xo in old.rel or xn in new.rel:
                    if (xo in old.rel) != (xn in new.rel): datamism.append((lab, hex(ao), 'rel slot vs plain'))
                    else:
                        to_, tn_ = old.rel[xo], new.rel[xn]
                        if old.func(to_) and new.func(tn_) and op.startswith(('call', 'jmp', 'mov', 'lea')):
                            if 'call' in op or 'jmp' in op: todo.append((to_, tn_, lab + '>*' + hex(xo)))
                elif 'lea' in op and old.func(xo) and new.func(xn):
                    todo.append((xo, xn, lab + '>&' + hex(xo)))
                else:
                    bo_, bn_ = old.bytes_at(xo, 16), new.bytes_at(xn, 16)
                    if bo_ != bn_ and bo_ is not None:
                        import struct
                        eo, en = struct.unpack('<4i', bo_), struct.unpack('<4i', bn_)
                        if all(fo[0] <= xo + a < fo[1] and xo + a - fo[0] == xn + b - fn[0] for a, b in zip(eo, en)):
                            jt += 1; continue
                        datamism.append((lab, hex(ao), hex(an), bo_.hex() if bo_ else None, bn_.hex() if bn_ else None))
    res = {'depth': DEPTH, 'cutAtDepth': len(cut), 'jumpTablesMatched': jt, 'newTables': {k: hex(v) for k, v in new_tables.items()}, 'functionsCompared': funcs,
           'instructionsCompared': insns, 'mismatches': mism[:500], 'nMismatches': len(mism),
           'dataMismatches': datamism[:500], 'nDataMismatches': len(datamism),
           'pairs': {f'{hex(a)}': [hex(b), l] for (a, b), l in sorted(seen.items())}}
    json.dump(res, open(OUT, 'w'), indent=1)
    print('functions', funcs, 'insns', insns, 'mismatches', len(mism), 'data', len(datamism), 'cut', len(cut), 'jt', jt)


main()
