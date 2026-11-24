"""Part one: merge the coverage of the five script sets (and optionally set 6), list every unexecuted run and every
JUMPI taken one way or never, with the source construct from the solc source map and the instructions around it.
Usage: python3 jumpmap.py <out.json> [extra coverage json ...]"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcmap as S
sys.path.insert(0, os.path.join(S.ROOT, 'research/network-risk/tools/opdiff'))
from pyevm import NAMES
OPC = os.path.join(S.ROOT, 'research/network-risk/opcodes')
HERE = os.path.dirname(os.path.abspath(__file__))
files = [os.path.join(HERE, 'cov-sets12.json')] + [os.path.join(OPC, f'build-pmdiff{k}-coverage.json') for k in (3, 4, 5)] + sys.argv[2:]
cover = set(); br = {}
for f in files:
    c = json.load(open(f)); cover |= set(c['cover'])
    for k, v in c['branches'].items(): br.setdefault(int(k), set()).update(bool(x) for x in v)
code = S.code; starts = S.starts[:S.NCODE]
def dis(pc, before=6, after=2):
    k = S.PC2I[pc]; out = []
    for p in S.starts[max(0, k - before):k + after + 1]:
        op = code[p]; n = op - 0x5f if 0x60 <= op <= 0x7f else 0
        out.append(f'{p}:{NAMES.get(op, hex(op))}' + (f' 0x{code[p+1:p+1+n].hex()}' if n else ''))
    return ' | '.join(out)
def target(pc):
    k = S.PC2I[pc]; p = S.starts[k - 1]; op = code[p]
    if 0x60 <= op <= 0x7f: return int.from_bytes(code[p + 1:p + op - 0x5e], 'big')
    return None
jumpis = [p for p in starts if code[p] == 0x57]
one = []; never = []
for p in jumpis:
    o = br.get(p)
    if not o: never.append(p)
    elif len(o) == 1: one.append((p, 'taken' if True in o else 'fallthrough'))
runs = []; cur = None
for p in starts:
    if p not in cover:
        if cur is None: cur = [p, p, 0]
        cur[1] = p; cur[2] += 1
    elif cur: runs.append(cur); cur = None
if cur: runs.append(cur)
res = {'instructions': len(S.starts), 'codeInstructions': len(starts), 'executed': len(cover & set(starts)),
       'jumpi': len(jumpis), 'both': sum(1 for p in jumpis if len(br.get(p, ())) == 2), 'oneSide': len(one), 'never': len(never),
       'runs': [{'from': a, 'to': b, 'n': n, 'src': S.loc(a)} for a, b, n in runs],
       'oneSided': [{'pc': p, 'seen': side, 'target': target(p), 'src': S.loc(p), 'ctx': dis(p)} for p, side in one],
       'neverReached': [{'pc': p, 'target': target(p), 'src': S.loc(p), 'ctx': dis(p)} for p in never]}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print({k: v for k, v in res.items() if not isinstance(v, list)}, 'runs', len(runs))
