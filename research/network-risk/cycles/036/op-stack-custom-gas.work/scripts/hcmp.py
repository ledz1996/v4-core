"""Compare the normalised machine code (objdump -M intel, addresses, call targets and rip displacements masked) of
the 25 arithmetic, comparison and shift handlers and of every function they reach by direct call, tail jump or call
through a relocated GOT slot, between instruction tables of several reth-family binaries. Reads only.
usage: python3 -I hcmp.py <spec.json> <out.json>
spec: {"name": {"bin", "rel", "fde", "tables": [hex...], "stride": 8|16}}"""
import bisect, hashlib, json, re, subprocess, sys
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
SPEC = json.load(open(sys.argv[1]))
def load(d):
    rel = {}
    for l in open(d['rel']):
        a, b = l.split(); rel[int(a, 16)] = int(b, 16)
    f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(d['fde']) if '..' in l)
    d['relm'], d['fdes'], d['starts'] = rel, f, [x[0] for x in f]
    return d
def rng(d, a):
    i = bisect.bisect_right(d['starts'], a) - 1
    if i < 0: return None
    lo, hi = d['fdes'][i]
    return (lo, hi) if lo <= a < hi else None
CACHE = {}
def dis(d, lo, hi):
    k = (d['bin'], lo)
    if k not in CACHE: CACHE[k] = _dis(d, lo, hi)
    return CACHE[k]
def _dis(d, lo, hi):
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x%x' % lo,
                          '--stop-address=0x%x' % hi, d['bin']], capture_output=True, text=True).stdout
    ins, callees = [], []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m: continue
        s = m.group(2)
        g = re.search(r'\b(call|jmp)\s+QWORD PTR \[rip\+0x[0-9a-f]+\]\s+# ([0-9a-f]+)', s)
        if g:
            t = d['relm'].get(int(g.group(2), 16))
            callees.append(('got', t))
        g = re.match(r'(call|jmp)\s+([0-9a-f]+)\b', s)
        if g:
            t = int(g.group(2), 16)
            if not (lo <= t < hi): callees.append(('dir', t))
        s = re.sub(r'#.*$', '', s); s = re.sub(r'<[^>]*>', '', s)
        s = re.sub(r'\b(call|j[a-z]+)\s+[0-9a-f]+', lambda mm: mm.group(1) + ' T', s)
        s = re.sub(r'\[rip\+0x[0-9a-f]+\]', '[rip+D]', s)
        ins.append(' '.join(s.split()))
    return ins, callees
def closure(d, root, limit=int(__import__('os').environ.get('LIMIT', '40'))):
    """hash of the root and its callee tree in call order (depth first), each function normalised"""
    seen, order, todo, ninsn = {}, [], [root], 0
    while todo and len(order) < limit:
        a = todo.pop(0)
        if a is None: order.append('NONE'); continue
        r = rng(d, a)
        if r is None: order.append('EXT'); continue
        if r[0] in seen: order.append('REF%d' % seen[r[0]]); continue
        seen[r[0]] = len(seen)
        ins, cal = dis(d, *r); ninsn += len(ins)
        order.append(hashlib.sha256('\n'.join(ins).encode()).hexdigest()[:16])
        todo += [t for k, t in cal]
    return hashlib.sha256(' '.join(order).encode()).hexdigest()[:16], len(seen), ninsn, \
        hashlib.sha256('\n'.join(dis(d, *rng(d, root))[0]).encode()).hexdigest()[:16]
res = {}
for name, d in SPEC.items():
    load(d); st = d.get('stride', 8)
    for t in d['tables']:
        T = int(t, 16); row = {}
        for op, c in OPS.items():
            h = d['relm'][T + st * c]
            tree, nf, ni, own = closure(d, h)
            row[op] = {'addr': hex(h), 'own': own, 'tree': tree, 'fns': nf, 'insns': ni}
        res['%s@%s' % (name, t)] = row
        print(name, t, 'done', flush=True)
json.dump(res, open(sys.argv[2], 'w'), indent=1)
keys = list(res)
for op in OPS:
    groups = {}
    for k in keys: groups.setdefault(res[k][op]['tree'], []).append(k)
    print(op, ' | '.join('%s: %s' % (h, ','.join(v)) for h, v in groups.items()))
