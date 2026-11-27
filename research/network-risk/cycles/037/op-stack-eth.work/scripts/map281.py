"""Cycle 37, op-stack-eth, lead L-1289: derive an op-reth v2.8.1 profile for rethj.py from the v2.10.0-rc.4 one.
Pairs functions of the two binaries that are identical with addresses masked (cmp_journal.py normalisation),
starting from the storage handlers of corresponding instruction tables and following direct calls position by
position, then zips the raw instructions of each pair to map every absolute address (rip targets, call targets,
immediates of 6+ hex digits, and instruction addresses) of v2.10.0-rc.4 onto v2.8.1. Reads files only; nothing
from either binary is executed.
usage: python3 -I map281.py <out.json>"""
import json, re, subprocess, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/035/theme-reth-journal-binary-lift.work/scripts')
import cmp_journal as CJ

C = '/home/user/v4-core/research/network-risk/cycles/'
A = CJ.load(C + '032/theme-opstack-reth-binary-lift.work/dl/opreth/x/amd64/usr/local/bin/op-reth',
            C + '032/theme-opstack-reth-binary-lift.work/build/opreth-amd64.rel',
            C + '032/theme-opstack-reth-binary-lift.work/build/opreth-amd64.fde', '0x5a0e458')
B = CJ.load(C + '033/theme-persistent-storage-binary-lift.work/dl/opreth281/x/amd64/usr/local/bin/op-reth',
            C + '033/theme-persistent-storage-binary-lift.work/build/opreth281/opreth281-amd64.rel',
            C + '033/theme-persistent-storage-binary-lift.work/build/opreth281/opreth281-amd64.fde', '0x5eee9b8')


def raw(d, lo):
    hi = CJ.fn(d, lo)[1]
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, d['bin']], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m: continue
        t = m.group(2)
        c = re.search(r'#\s*([0-9a-f]+)', t)
        body = re.sub(r'<[^>]*>', '', t).split('#')[0].strip()
        nums = [int(x, 16) for x in re.findall(r'\b(?:0x)?([0-9a-f]{6,})\b', body)]
        if c: nums.append(int(c.group(1), 16))
        r.append((int(m.group(1), 16), nums))
    return r


amap = {}; pairs = {}; conflicts = []


def addmap(a, b, why):
    if a in amap and amap[a] != b: conflicts.append((hex(a), hex(amap[a]), hex(b), why)); return
    amap[a] = b


def pair(fa, fb, depth=0):
    if fa in pairs: return
    ba = CJ.body(A, fa); bb = CJ.body(B, fb)
    pairs[fa] = (fb, ba['h'] == bb['h'])
    addmap(fa, fb, 'fn')
    if ba['h'] != bb['h']:
        return
    ra = raw(A, fa); rb = raw(B, fb)
    for (pa, na), (pb, nb) in zip(ra, rb):
        addmap(pa, pb, 'pc')
        for x, y in zip(na, nb): addmap(x, y, 'op@%x' % pa)
    if depth < 6:
        for ca, cb in zip(ba['calls'], bb['calls']):
            ka = CJ.fn(A, ca); kb = CJ.fn(B, cb)
            if ka and kb and ka[0] == ca and kb[0] == cb: pair(ca, cb, depth + 1)


ta = CJ.tables(A); tb = CJ.tables(B)
for x, y in [(0x5a0e458, 0x5eee9b8), (0x5aea7c0, 0x5fc9cc0)]:
    for o in (0x54, 0x55, 0x5c, 0x5d):
        pair(A['rel'][x + 8 * o], B['rel'][y + 8 * o])
# journal routines named by cmp_journal (identical hashes)
for x, y in [(0x2d07000, 0x2eae2c0), (0x44daef0, 0x4666bc0), (0x4579590, 0x470de30), (0x4a4e6e0, 0x46736c0), (0x4a4dd50, 0x4bb29f0)]:
    pair(x, y)
json.dump({'pairs': {hex(a): [hex(b), s] for a, (b, s) in pairs.items()}, 'map': {hex(a): hex(b) for a, b in amap.items()},
           'conflicts': conflicts[:200], 'nconflicts': len(conflicts), 'tablesA': [hex(t) for t in ta], 'tablesB': [hex(t) for t in tb]},
          open(sys.argv[1], 'w'), indent=0)
print(len(pairs), 'pairs', sum(1 for v in pairs.values() if v[1]), 'identical;', len(amap), 'addresses;', len(conflicts), 'conflicts')
for a, (b, s) in sorted(pairs.items()):
    if not s: print('differs', hex(a), hex(b))
