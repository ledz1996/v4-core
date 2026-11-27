"""Task 4: compare the storage, transient storage and journal routines of two reth-family x86-64 binaries.
For each binary: every 256-entry instruction table (found by sharing the ADD handler of a known table), the
SLOAD, SSTORE, TLOAD and TSTORE handlers of every table and every function they reach within 3 direct calls, plus
the journal entry revert routine (the function with a jump table that calls the account lookup at least 10 times),
its callers (checkpoint_revert) and the standalone checkpoint routine. Each function is normalised (absolute
addresses and rip displacements masked) and hashed; the two sets are matched. Nothing is executed.
usage: python3 -I cmp_journal.py <binA> <relA> <fdeA> <tableA> <binB> <relB> <fdeB> <tableB> <out.json>"""
import bisect, hashlib, json, re, struct, subprocess, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))


def load(binf, relf, fdef, table):
    rel = {}
    for l in open(relf):
        a, b = l.split(); rel[int(a, 16)] = int(b, 16)
    f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdef))
    return dict(bin=binf, rel=rel, f=f, s=[a for a, b in f], table=int(table, 16), cache={})


def fn(d, a):
    k = bisect.bisect_right(d['s'], a) - 1
    lo, hi = d['f'][k]
    return (lo, hi) if lo <= a < hi else None


def body(d, lo):
    if lo in d['cache']: return d['cache'][lo]
    hi = fn(d, lo)[1]
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, d['bin']],
                         capture_output=True, text=True).stdout
    ins = []; calls = []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m: continue
        t = re.sub(r'<[^>]*>', '', m.group(2)).split('#')[0].strip()
        c = re.match(r'^(call|jmp)\s+([0-9a-f]+)$', t)
        if c:
            x = int(c.group(2), 16)
            if not (lo <= x < hi): calls.append(x)
        n = re.sub(r'\b(0x)?[0-9a-f]{6,}\b', 'A', t); n = re.sub(r'\[rip[+-]0x[0-9a-f]+\]', '[R]', n)
        ins.append(n)
    r = dict(lo=lo, size=hi - lo, n=len(ins), h=hashlib.sha256('\n'.join(ins).encode()).hexdigest()[:16], calls=calls, ins=ins)
    d['cache'][lo] = r
    return r


def tables(d):
    st = d.get('stride', 8)
    add = d['rel'][d['table'] + st]
    return sorted(a - st for a, v in d['rel'].items() if v == add and all((a - st + st * j) in d['rel'] for j in (0x54, 0x55, 0x5c, 0x5d)))


def walk(d, roots, depth=3, cap=6000):
    seen = {}; todo = [(r, 0) for r in roots]
    while todo:
        a, k = todo.pop()
        r = fn(d, a)
        if not r or r[0] in seen: continue
        b = body(d, r[0]); seen[r[0]] = b
        if k < depth and b['size'] <= cap:
            todo += [(c, k + 1) for c in b['calls']]
    return seen


def journal_fns(d, acct):
    text = subprocess.run(['readelf', '-SW', d['bin']], capture_output=True, text=True).stdout
    m = [re.search(r'\]\s+\.text\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', l) for l in text.splitlines()]
    VA, OFF, SZ = [int(x, 16) for x in [x for x in m if x][0].groups()]
    raw = open(d['bin'], 'rb').read()[OFF:OFF + SZ]
    def callers(t):
        r = []; i = raw.find(b'\xe8')
        while i != -1:
            if i + 5 <= len(raw) and VA + i + 5 + struct.unpack_from('<i', raw, i + 1)[0] == t: r.append(VA + i)
            i = raw.find(b'\xe8', i + 1)
        return r
    cnt = {}
    for c in callers(acct):
        r = fn(d, c)
        if r: cnt[r[0]] = cnt.get(r[0], 0) + 1
    rev = [a for a, n in cnt.items() if n >= 10 and any('jmp    rax' == x for x in body(d, a)['ins'])]
    out = {'entry_revert': rev}
    cr = set()
    for a in rev:
        for c in callers(a):
            r = fn(d, c)
            if r and body(d, r[0])['size'] < 1200: cr.add(r[0])
    out['checkpoint_revert'] = sorted(cr)
    cps = []
    for mm in re.finditer(rb'\x48\xff\x81\x18\x01\x00\x00\xc3', raw):
        r = fn(d, VA + mm.start())
        if r and r[1] - r[0] < 64: cps.append(r[0])
    out['checkpoint'] = sorted(set(cps))
    return out


if __name__ == '__main__':
    A = load(*sys.argv[1:5]); B = load(*sys.argv[5:9]); OUT = sys.argv[9]
    import os as _os
    A['stride'] = int(_os.environ.get('STRIDE_A', '8')); B['stride'] = int(_os.environ.get('STRIDE_B', '8'))  # cycle 36: 16-byte tables
    res = {}
    sets = {}
    for nm, d in (('A', A), ('B', B)):
        ts = tables(d)
        roots = [d['rel'][t + d['stride'] * o] for t in ts for o in (0x54, 0x55, 0x5c, 0x5d)]
        fs = walk(d, roots)
        # the account lookup: the 70-instruction leaf called first by the SLOAD path (imul by 0xa8 bucket size)
        acct = [a for a, b in fs.items() if any('imul   r9,r9,0xa8' == x for x in b['ins']) and b['n'] < 90]
        jf = journal_fns(d, acct[0]) if acct else {}
        for k in ('entry_revert', 'checkpoint_revert', 'checkpoint'):
            for a in jf.get(k, []):
                fs[a] = body(d, a)
                for c in fs[a]['calls']:
                    r = fn(d, c)
                    if r and r[0] not in fs and body(d, r[0])['size'] < 6000: fs[r[0]] = body(d, r[0])
        sets[nm] = fs
        res[nm] = {'tables': [hex(t) for t in ts], 'functions': len(fs), 'account_lookup': [hex(a) for a in acct],
                   'journal': {k: [hex(x) for x in v] for k, v in jf.items()}}
    ha = {}; hb = {}
    for a, b in sets['A'].items(): ha.setdefault(b['h'], []).append(a)
    for a, b in sets['B'].items(): hb.setdefault(b['h'], []).append(a)
    common = set(ha) & set(hb)
    res['identical_hashes'] = len(common)
    res['only_A'] = [{'fn': hex(a), 'size': sets['A'][a]['size'], 'n': sets['A'][a]['n']} for h in set(ha) - common for a in ha[h]]
    res['only_B'] = [{'fn': hex(a), 'size': sets['B'][a]['size'], 'n': sets['B'][a]['n']} for h in set(hb) - common for a in hb[h]]
    # named journal routines: are they identical?
    named = {}
    for k in ('entry_revert', 'checkpoint_revert', 'checkpoint'):
        xa = [sets['A'][int(x, 16)]['h'] for x in res['A']['journal'].get(k, [])]
        xb = [sets['B'][int(x, 16)]['h'] for x in res['B']['journal'].get(k, [])]
        named[k] = {'A': xa, 'B': xb, 'same_set': sorted(set(xa)) == sorted(set(xb))}
    xa = [sets['A'][int(x, 16)]['h'] for x in res['A']['account_lookup']]; xb = [sets['B'][int(x, 16)]['h'] for x in res['B']['account_lookup']]
    named['account_lookup'] = {'A': xa, 'B': xb, 'same_set': sorted(set(xa)) == sorted(set(xb))}
    res['named'] = named
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('only_A', 'only_B')}, indent=1)[:3000])
    print('only_A', len(res['only_A']), 'only_B', len(res['only_B']))
