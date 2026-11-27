"""Task 4 (L-1241): locate the 256-entry instruction table of the op-reth v2.8.1 release binary (amd64, read as data)
by the handler-sharing fingerprint of the cycle 32 table of op-reth v2.10.0-rc.4, and compare the machine code of
the 25 arithmetic, comparison and shift handlers and of the jump destination analysis function with the lifted
v2.10.0-rc.4 code, instruction by instruction, with addresses and rip-relative displacements masked.
Nothing is executed: objdump prints the text, Python compares it.
usage: python3 -I cmp_reth.py <new bin> <new rel> <new fde> <out.json>"""
import bisect, json, re, subprocess, sys
C32 = '/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/'
OLD = dict(bin=C32 + 'dl/opreth/x/amd64/usr/local/bin/op-reth', rel=C32 + 'build/opreth-amd64.rel', fde=C32 + 'build/opreth-amd64.fde',
           table=0x5a0e458, jd=0x4a4a8c0)
NEW = dict(bin=sys.argv[1], rel=sys.argv[2], fde=sys.argv[3])
OUT = sys.argv[4]
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}


def load(d):
    rel = {}
    for l in open(d['rel']):
        a, b = l.split(); rel[int(a, 16)] = int(b, 16)
    fde = []
    for l in open(d['fde']):
        a, b = re.split(r'\.\.+', l.strip()); fde.append((int(a, 16), int(b, 16)))
    fde.sort()
    d['relm'], d['fdes'], d['starts'] = rel, fde, [f[0] for f in fde]
    return d


def fn_range(d, a):
    i = bisect.bisect_right(d['starts'], a) - 1
    lo, hi = d['fdes'][i]
    assert lo <= a < hi, hex(a)
    return lo, hi


def pattern(rel, t):
    fns = [rel.get(t + 8 * i) for i in range(256)]
    if None in fns:
        return None
    first = {}
    return tuple(first.setdefault(f, len(first)) for f in fns)


def norm(d, lo, hi):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x%x' % lo,
                          '--stop-address=0x%x' % hi, d['bin']], capture_output=True, text=True).stdout
    ins = []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m:
            continue
        s = m.group(2)
        s = re.sub(r'#.*$', '', s)
        s = re.sub(r'<[^>]*>', '', s)
        s = re.sub(r'\b(call|j[a-z]+)\s+[0-9a-f]+', lambda mm: mm.group(1) + ' T', s)
        s = re.sub(r'\[rip\+0x[0-9a-f]+\]', '[rip+D]', s)
        ins.append(' '.join(s.split()))
    return ins


def main():
    old, new = load(OLD), load(NEW)
    pat = pattern(old['relm'], old['table'])
    cands = [a for a in sorted(new['relm']) if pattern(new['relm'], a) == pat]
    res = {'oldTable': hex(old['table']), 'distinctHandlersOld': len(set(pat)), 'candidates': [hex(a) for a in cands],
           'handlers': {}, 'jumpAnalysis': None}
    ocands = [a for a in sorted(old['relm']) if pattern(old['relm'], a) == pat]
    res['oldCandidates'] = [hex(a) for a in ocands]
    # the per-spec tables share the arithmetic handlers: list the distinct handler per opcode over all candidates
    res['arithHandlersPerOpOld'] = {op: sorted({hex(old['relm'][a + 8 * c]) for a in ocands}) for op, c in OPS.items()}
    res['arithHandlersPerOpNew'] = {op: sorted({hex(new['relm'][a + 8 * c]) for a in cands}) for op, c in OPS.items()}
    # EXP has one handler per gas schedule; the old table is the first candidate (cycle 32), so take the first here
    if not cands or any(len(v) != 1 for k, v in res['arithHandlersPerOpNew'].items() if k != 'EXP') or \
            ocands.index(OLD['table']) != 0:
        json.dump(res, open(OUT, 'w'), indent=1); print('ambiguous', res['candidates']); return
    t = cands[0]
    res['newTable'] = hex(t)
    for op, code in OPS.items():
        oa, na = old['relm'][old['table'] + 8 * code], new['relm'][t + 8 * code]
        oi, ni = norm(old, *fn_range(old, oa)), norm(new, *fn_range(new, na))
        diff = [i for i in range(max(len(oi), len(ni))) if i >= len(oi) or i >= len(ni) or oi[i] != ni[i]]
        res['handlers'][op] = {'old': hex(oa), 'new': hex(na), 'oldLen': len(oi), 'newLen': len(ni), 'identical': not diff,
                               'firstDiff': None if not diff else [oi[diff[0]] if diff[0] < len(oi) else None,
                                                                  ni[diff[0]] if diff[0] < len(ni) else None]}
    # jump analysis: the function at the same normalised text in the new binary, searched among FDE ranges of the
    # same length
    oi = norm(old, *fn_range(old, OLD['jd']))
    lo, hi = fn_range(old, OLD['jd'])
    same = [(a, b) for a, b in new['fdes'] if b - a == hi - lo]
    hit = None
    for a, b in same:
        if norm(new, a, b) == oi:
            hit = (a, b); break
    res['jumpAnalysis'] = {'old': hex(OLD['jd']), 'oldBytes': hi - lo, 'oldInsns': len(oi), 'sameLengthFns': len(same),
                           'identicalIn': hex(hit[0]) if hit else None}
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'handlers'}))
    print({k: v['identical'] for k, v in res['handlers'].items()})


if __name__ == '__main__' and len(sys.argv) == 5:
    main()


def calls(d, lo, hi):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x%x' % lo,
                          '--stop-address=0x%x' % hi, d['bin']], capture_output=True, text=True).stdout
    return [int(m.group(1), 16) for m in re.finditer(r'\b(?:call|jmp)\s+([0-9a-f]+)\b', out)
            if not (lo <= int(m.group(1), 16) < hi)]


def deep(out_json):
    """Second pass: follow the direct calls and tail jumps of every handler and of the jump analysis pairwise (the
    n-th call target of the old function against the n-th of the new) and compare those functions the same way."""
    old, new = load(dict(OLD)), load(dict(NEW))
    r = json.load(open(out_json))
    pairs = [(int(v['old'], 16), int(v['new'], 16)) for v in r['handlers'].values()]
    pairs.append((OLD['jd'], int(r['jumpAnalysis']['identicalIn'], 16)))
    seen, cmp_, bad = set(), 0, []
    while pairs:
        oa, na = pairs.pop()
        if (oa, na) in seen:
            continue
        seen.add((oa, na))
        try:
            orng, nrng = fn_range(old, oa), fn_range(new, na)
        except AssertionError:
            continue  # PLT or GOT stub outside the FDE list (memcpy, memset, panic)
        if norm(old, *orng) != norm(new, *nrng):
            bad.append([hex(oa), hex(na)])
        cmp_ += 1
        oc, nc = calls(old, *orng), calls(new, *nrng)
        if len(oc) != len(nc):
            bad.append([hex(oa), hex(na), 'call count'])
            continue
        pairs += list(zip(oc, nc))
    r['deep'] = {'functionsCompared': cmp_, 'differences': bad}
    json.dump(r, open(out_json, 'w'), indent=1)
    print('deep', cmp_, 'functions compared, differences', bad[:10])


if __name__ == '__main__' and len(sys.argv) > 5 and sys.argv[5] == 'deep':
    deep(OUT)


def storage(out_json, limit=4000):
    """Third pass: the SLOAD, SSTORE, TLOAD and TSTORE handlers (0x54, 0x55, 0x5c, 0x5d) of the first table and every
    function they reach by direct call or tail jump, compared pairwise in the two releases (dyn calls are not
    followed)."""
    old, new = load(dict(OLD)), load(dict(NEW))
    r = json.load(open(out_json))
    T_new = int(r['newTable'], 16)
    roots = {op: (old['relm'][OLD['table'] + 8 * c], new['relm'][T_new + 8 * c]) for op, c in
             (('SLOAD', 0x54), ('SSTORE', 0x55), ('TLOAD', 0x5c), ('TSTORE', 0x5d))}
    res = {}
    for op, pr in roots.items():
        pairs, seen, cmp_, bad, ext = [pr], set(), 0, [], 0
        while pairs and cmp_ < limit:
            oa, na = pairs.pop()
            if (oa, na) in seen:
                continue
            seen.add((oa, na))
            try:
                orng, nrng = fn_range(old, oa), fn_range(new, na)
            except AssertionError:
                ext += 1; continue
            same = norm(old, *orng) == norm(new, *nrng)
            cmp_ += 1
            if not same:
                bad.append([hex(oa), hex(na), orng[1] - orng[0], nrng[1] - nrng[0]])
                continue  # do not pair the callees of a function whose text differs
            pairs += list(zip(calls(old, *orng), calls(new, *nrng)))
        res[op] = {'old': hex(pr[0]), 'new': hex(pr[1]), 'functionsCompared': cmp_, 'external': ext, 'differences': bad,
                   'truncated': bool(pairs)}
        print(op, cmp_, 'compared,', len(bad), 'differ', bad[:6])
    r['storage'] = res
    json.dump(r, open(out_json, 'w'), indent=1)


if __name__ == '__main__' and len(sys.argv) > 5 and sys.argv[5] == 'storage':
    storage(OUT)
