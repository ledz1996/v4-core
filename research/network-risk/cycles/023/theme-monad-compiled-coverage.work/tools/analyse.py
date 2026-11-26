"""Join the coverage files of all runs and list IR blocks and native leaders never entered, with source lines.
Usage: analyse.py <out.json> <code.bin from HX_COVKEEP> <base hex of that dump> <cov files...>"""
import sys, json, collections, subprocess, re
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/016/theme-monad-harness-exact.work')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import srcmap
from pyevm import NAMES
code = srcmap.code
JM = json.load(open('/home/user/v4-core/research/network-risk/opcodes/jumpmap.json'))
out, binp, base_hex = sys.argv[1], sys.argv[2], sys.argv[3]; files = sys.argv[4:]
def load(p):
    B = []; L = []
    for line in open(p):
        t = line.split()
        if t[0] == 'B': B.append((int(t[2]), int(t[3], 16), int(t[4])))
        elif t[0] == 'L': L.append((int(t[1], 16), int(t[2]), int(t[3]), int(t[4])))
    return B, L
B0, L0 = load(files[0])
key0 = {}
def keyed(L):
    per = collections.defaultdict(list)
    for a, eb, st, hit in L: per[eb].append((a, hit))
    K = {}
    for eb, xs in per.items():
        for k, (a, hit) in enumerate(sorted(xs)): K[(eb, k)] = (a, hit)
    return K
K0 = keyed(L0); hits = {k: 0 for k in K0}; perfile = {}
for p in files:
    B, L = load(p); K = keyed(L)
    assert [o for o, _, _ in B] == [o for o, _, _ in B0], p
    assert set(K) == set(K0), ('leader shape differs', p)
    for k, (a, h) in K.items(): hits[k] |= h
    perfile[p] = {'irEntered': sum(1 for i in range(len(B)) if K.get((i, 0), (0, 0))[1]), 'leadersHit': sum(h for a, h in K.values())}
# disassembly of the kept dump, offsets relative to base
base = int(base_hex, 16)
dis = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '-w', binp], capture_output=True, text=True).stdout
INS = {}
for line in dis.splitlines():
    m = re.match(r'\s*([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$', line)
    if m: INS[int(m.group(1), 16)] = m.group(3).strip()
insoff = sorted(INS)
import bisect
def native_ctx(off, n=4):
    i = bisect.bisect_left(insoff, off); return ' | '.join(INS[insoff[j]] for j in range(i, min(i + n, len(insoff))))
def prev_ins(off):
    i = bisect.bisect_left(insoff, off); return INS[insoff[i - 1]] if i else ''
# EVM instruction listing
starts = srcmap.pcs
def evm_ctx(a, b, n=6):
    xs = [p for p in starts if a <= p < b][:n]
    return ' | '.join(f"{p}:{NAMES.get(code[p], hex(code[p]))}" for p in xs)
offs = [o for o, _, _ in B0]
ends = offs[1:] + [len(code)]
# one-sided jumps: untaken side block offset
untaken = {}
for x in JM['oneSided']:
    side = x['target'] if x['seen'] == 'fallthrough' else x['pc'] + 1
    untaken.setdefault(side, []).append(x)
for x in JM['neverReached']:
    untaken.setdefault(x['pc'] + 1, []).append(dict(x, seen='never'))
    untaken.setdefault(x['target'], []).append(dict(x, seen='never'))
# the fallthrough block after a one-sided jump taken only one way may start at pc+1
def first_code_pc(a, b):
    for p in starts:
        if a <= p < b and code[p] != 0x5b: return p
    return a
blocks = []
for i, (o, a, en) in enumerate(B0):
    entered = bool(hits.get((i, 0), 0))
    nlead = sum(1 for k in hits if k[0] == i); nhit = sum(v for k, v in hits.items() if k[0] == i)
    fc = first_code_pc(o, ends[i])
    blocks.append({'index': i, 'evmFrom': o, 'evmTo': ends[i] - 1, 'jumpdest': code[o] == 0x5b, 'entered': entered, 'enterable': en,
                   'nativeLeaders': nlead, 'nativeLeadersHit': nhit, 'src': srcmap.where(fc), 'srcNear': srcmap.near(fc),
                   'evm': evm_ctx(o, ends[i]), 'oneSidedJumps': [{'pc': x['pc'], 'seen': x['seen'], 'why': x['why']} for x in untaken.get(o, [])]})
never_blocks = [b for b in blocks if not b['entered']]
# native leaders not hit inside entered IR blocks
nl = []
for (eb, k), h in sorted(hits.items()):
    if h or eb < 0: continue
    if not blocks[eb]['entered']: continue
    a = K0[(eb, k)][0]  # cov files hold offsets from the code base
    nl.append({'irBlock': eb, 'evmFrom': blocks[eb]['evmFrom'], 'ordinal': k, 'nativeOffset': a, 'prev': prev_ins(a), 'native': native_ctx(a), 'src': blocks[eb]['src'], 'evm': blocks[eb]['evm']})
res = {'files': files, 'perFile': perfile, 'irBlocks': len(blocks), 'irBlocksEntered': sum(1 for b in blocks if b['entered']),
       'nativeLeaders': len(hits), 'nativeLeadersHit': sum(hits.values()),
       'irBlocksNeverEntered': never_blocks, 'nativeLeadersNeverHitInEnteredBlocks': nl}
json.dump(res, open(out, 'w'), indent=1)
print({k: v for k, v in res.items() if k in ('irBlocks', 'irBlocksEntered', 'nativeLeaders', 'nativeLeadersHit')}, 'never IR', len(never_blocks), 'unhit leaders in entered blocks', len(nl))
