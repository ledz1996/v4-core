"""Cycle 28: PoolManager IR blocks (Monad compiler, read from the B lines of a coverage file) mapped to source lines
with the solc deployed source map of this checkout's build (cycles/016/theme-monad-harness-exact.work/build/solc/
PoolManager.srcmap.json, whose runtime equals research/network-risk/build/PoolManager.json byte for byte; checked below).
Also reads coverage files: a block counts as entered in native code when the leader at its IR block start was hit."""
import os, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE)
NR = os.path.abspath(os.path.join(WORK, '..', '..', '..')); R = os.path.abspath(os.path.join(NR, '..', '..'))
SM = json.load(open(os.path.join(NR, 'cycles', '016', 'theme-monad-harness-exact.work', 'build', 'solc', 'PoolManager.srcmap.json')))
assert SM['runtime'] == json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))['runtime']
code = bytes.fromhex(SM['runtime']); ids = SM['sourceIds']
pcs = []; i = 0
while i < len(code):
    pcs.append(i); o = code[i]; i += 1 + (o - 0x5f if 0x60 <= o <= 0x7f else 0)
ent = []; s = l = f = -1; j = '-'
for e in SM['sourceMap'].split(';'):
    p = e.split(':')
    if len(p) > 0 and p[0] != '': s = int(p[0])
    if len(p) > 1 and p[1] != '': l = int(p[1])
    if len(p) > 2 and p[2] != '': f = int(p[2])
    if len(p) > 3 and p[3] != '': j = p[3]
    ent.append((s, l, f, j))
_c = {}
def _line(fn, off):
    if fn not in _c:
        try: _c[fn] = open(os.path.join(R, fn), 'rb').read()
        except Exception: _c[fn] = None
    t = _c[fn]; return None if t is None else t[:off].count(b'\n') + 1
M = {}; JT = {}
for k, pc in enumerate(pcs):
    if k >= len(ent): break
    s, l, f, j = ent[k]; fn = ids.get(str(f)); JT[pc] = j
    if fn is None or s < 0: M[pc] = None; continue
    M[pc] = (fn, _line(fn, s), _line(fn, s + l))
OPN = {0x00: 'STOP', 0x56: 'JUMP', 0x57: 'JUMPI', 0x5b: 'JUMPDEST', 0xfd: 'REVERT', 0xf3: 'RETURN', 0xfe: 'INVALID'}
def op(pc): return code[pc]
def where(pc):
    r = M.get(pc); return f'{r[0]}:{r[1]}' + (f'-{r[2]}' if r[2] != r[1] else '') if r else '?'
def narrow(pc):
    """source ranges of a pc that are narrower than a whole contract or function body (<= 12 lines)"""
    r = M.get(pc)
    return r if r and r[1] is not None and r[2] - r[1] <= 12 else None
def block_offsets(covfile):
    return [int(t.split()[2]) for t in open(covfile) if t.startswith('B ')]
def block_spans(offs):
    offs = sorted(offs); out = {}
    for a, b in zip(offs, offs[1:] + [len(code)]):
        out[a] = [p for p in pcs if a <= p < b]
    return out
def block_src(span):
    """distinct narrow source ranges in a block, in pc order"""
    seen = []
    for p in span:
        r = narrow(p)
        if r and r not in seen: seen.append(r)
    return seen
def entered(covfile):
    B = []; hit = set()
    for line in open(covfile):
        t = line.split()
        if t[0] == 'B': B.append(int(t[2]))
        elif t[0] == 'L' and t[3] == '1' and t[4] == '1': hit.add(B[int(t[2])])
    return hit
def enterable(covfile):
    return {int(t.split()[2]): int(t.split()[4]) for t in open(covfile) if t.startswith('B ')}
