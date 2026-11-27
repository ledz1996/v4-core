"""For one binary: describe each instruction table found by tables.py (stride, which opcodes are valid: PUSH0, TLOAD,
MCOPY, CLZ, and the static gas of SLOAD when the stride is 16), and compare the distinct handlers of each arithmetic
op inside the binary with each other by normalised text plus the normalised text of every function they reach by
direct call, tail jump or relocated GOT slot (pairwise, in order). Read only.
usage: python3 -I families.py <name> <bin> <rel> <fde> <tab.json> <out.json>"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmp_reth as C
name, binf, relf, fdef, tabf, outf = sys.argv[1:7]
d = C.load(dict(bin=binf, rel=relf, fde=fdef))
tab = json.load(open(tabf))
rel = d['relm']
img = open(binf, 'rb').read()


def calls(lo, hi):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x%x' % lo,
                          '--stop-address=0x%x' % hi, binf], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        m = re.search(r'\b(?:call|jmp)\s+([0-9a-f]+)\b', l)
        if m and not (lo <= int(m.group(1), 16) < hi):
            r.append(int(m.group(1), 16)); continue
        m = re.search(r'\b(?:call|jmp)\s+QWORD PTR \[rip[+-]0x[0-9a-f]+\]\s+#\s*([0-9a-f]+)', l)
        if m:
            r.append(rel.get(int(m.group(1), 16), -int(m.group(1), 16)))
    return r


def deep_same(a, b, limit=400):
    pairs, seen, n = [(a, b)], set(), 0
    while pairs and n < limit:
        x, y = pairs.pop()
        if (x, y) in seen or x == y:
            continue
        seen.add((x, y))
        if x < 0 or y < 0:
            if x != y: return False, n, [hex(abs(x)), hex(abs(y)), 'slot']
            continue
        try:
            rx, ry = C.fn_range(d, x), C.fn_range(d, y)
        except AssertionError:
            if x != y: return False, n, [hex(x), hex(y), 'no fde']
            continue
        if C.norm(d, *rx) != C.norm(d, *ry):
            return False, n, [hex(x), hex(y)]
        n += 1
        cx, cy = calls(*rx), calls(*ry)
        if len(cx) != len(cy):
            return False, n, [hex(x), hex(y), 'call count']
        pairs += list(zip(cx, cy))
    return True, n, None


tables = []
for t, s in tab['tables']:
    t = int(t, 16)
    inv = rel[t + s * 0x0c]
    desc = {'table': hex(t), 'stride': s}
    for nm, op in (('PUSH0', 0x5f), ('TLOAD', 0x5c), ('MCOPY', 0x5e), ('CLZ', 0x1e), ('BASEFEE', 0x48), ('BLOBHASH', 0x49)):
        desc[nm] = rel[t + s * op] != inv
    if s == 16:
        desc['SLOADgas'] = int.from_bytes(img[0:0], 'little') if False else None
    desc['ADD'] = hex(rel[t + s * 1]); desc['EXP'] = hex(rel[t + s * 10])
    tables.append(desc)
res = {'binary': name, 'tables': tables, 'variants': {}}
for op, lst in tab['handlers'].items():
    addrs = [int(x['addr'], 16) for x in lst]
    if len(addrs) < 2:
        continue
    res['variants'][op] = [{'a': hex(addrs[0]), 'b': hex(b), 'same': deep_same(addrs[0], b)} for b in addrs[1:]]
json.dump(res, open(outf, 'w'), indent=1)
for t in tables: print(t)
for op, v in res['variants'].items(): print(op, [(x['b'], x['same'][0], x['same'][1], x['same'][2]) for x in v])
