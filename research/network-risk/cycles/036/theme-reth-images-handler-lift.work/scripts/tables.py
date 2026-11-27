"""Find every 256-entry EVM instruction table in a reth-derived x86-64 binary, read as data (RELATIVE relocations),
for entry strides of 8 and 16 bytes, and compare each distinct arithmetic, comparison and shift handler, the EXP
variants and the legacy jump analysis with the op-reth v2.10.0-rc.4 code lifted in cycle 32, instruction by
instruction with addresses and rip displacements masked (normalisation of cmp_reth.py).
Nothing from the binary is executed: objdump prints text, Python compares it.
usage: python3 -I tables.py <bin> <rel> <fde> <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmp_reth as C

INVALID = list(range(0x0c, 0x10)) + list(range(0x21, 0x30)) + list(range(0xb0, 0xd0))


def tables(d):
    rel = d['relm']
    out = []
    keys = sorted(rel)
    ks = set(keys)
    for stride in (8, 16):
        for t in keys:
            if not all((t + stride * i) in ks for i in (0, 1, 0x60, 0xff)):
                continue
            if not all((t + stride * i) in ks for i in range(256)):
                continue
            inv = {rel[t + stride * i] for i in INVALID}
            if len(inv) != 1:
                continue
            ar = [rel[t + stride * c] for c in C.OPS.values()]
            if len(set(ar)) != len(ar) or inv & set(ar):
                continue
            out.append((t, stride))
    return out


def main():
    binf, relf, fdef, outf = sys.argv[1:5]
    old, new = C.load(dict(C.OLD)), C.load(dict(bin=binf, rel=relf, fde=fdef))
    ref = {op: C.norm(old, *C.fn_range(old, old['relm'][C.OLD['table'] + 8 * c])) for op, c in C.OPS.items()}
    # all four EXP variants of the reference (one per gas schedule)
    oc = [t for t, s in tables(old)]
    refexp = {}
    for t in oc:
        a = old['relm'][t + 8 * 10]
        refexp.setdefault(a, C.norm(old, *C.fn_range(old, a)))
    found = tables(new)
    res = {'tables': [[hex(t), s] for t, s in found], 'handlers': {}, 'refExpVariants': [hex(a) for a in refexp]}
    seen = {}
    for t, s in found:
        for op, c in C.OPS.items():
            a = new['relm'][t + s * c]
            if (op, a) in seen:
                continue
            ni = C.norm(new, *C.fn_range(new, a))
            if op == 'EXP':
                same = [hex(k) for k, v in refexp.items() if v == ni]
                ident = bool(same)
            else:
                ident = ni == ref[op]; same = None
            first = None
            if not ident:
                r = ref[op]
                i = next((i for i in range(max(len(r), len(ni))) if i >= len(r) or i >= len(ni) or r[i] != ni[i]), None)
                first = [i, r[i] if i is not None and i < len(r) else None, ni[i] if i is not None and i < len(ni) else None]
            seen[(op, a)] = True
            res['handlers'].setdefault(op, []).append({'addr': hex(a), 'len': len(ni), 'refLen': len(ref[op]),
                                                       'identical': ident, 'sameAsRefExp': same, 'firstDiff': first,
                                                       'tables': [hex(tt) for tt, ss in found if new['relm'][tt + ss * c] == a]})
    # legacy jump analysis: identical normalised text among FDE ranges of the same length
    oi = C.norm(old, *C.fn_range(old, C.OLD['jd']))
    lo, hi = C.fn_range(old, C.OLD['jd'])
    same = [(a, b) for a, b in new['fdes'] if b - a == hi - lo]
    hit = [hex(a) for a, b in same if C.norm(new, a, b) == oi]
    res['jumpAnalysis'] = {'old': hex(C.OLD['jd']), 'oldBytes': hi - lo, 'oldInsns': len(oi), 'sameLengthFns': len(same),
                           'identicalIn': hit}
    json.dump(res, open(outf, 'w'), indent=1)
    print('tables', res['tables'])
    for op, v in res['handlers'].items():
        print(op, [(x['addr'], x['identical']) for x in v])
    print('jd', res['jumpAnalysis'])


if __name__ == '__main__':
    main()
