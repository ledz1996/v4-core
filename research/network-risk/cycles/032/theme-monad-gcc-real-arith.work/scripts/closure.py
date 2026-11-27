"""Direct-call closure of gcc functions from given entries (objdump text only; nothing is run).
Writes each function's text to out/fn/<addr>.s in the format allocdrv.load_fn reads.
usage: STOP=a,b python3 -I closure.py <hexaddr>..."""
import sys, re, os, json, bisect
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN = os.path.join(W, 'out', 'fn')
D = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/dl/dis/monad-0.16.7.s'
IDX = {int(k, 16): v for k, v in json.load(open(os.path.join(W, 'out', 'fnindex.json'))).items()}
KEYS = sorted(IDX)
STOP = set(int(a, 16) for a in os.environ.get('STOP', '').split(',') if a)
fh = open(D, 'rb')
def get(a):
    p = os.path.join(FN, '%016x.s' % a)
    if not os.path.exists(p):
        i = KEYS.index(a); fh.seek(IDX[a]); n = (IDX[KEYS[i + 1]] - IDX[a]) if i + 1 < len(KEYS) else 1 << 20
        open(p, 'wb').write(fh.read(n))
    return open(p).read()
def emit_all(starts=None):
    seen = {}; todo = list(starts) if starts is not None else [int(a, 16) for a in sys.argv[1:]]
    while todo:
        a = todo.pop()
        if a in seen: continue
        if a in STOP: seen[a] = 'STOP'; continue
        if a < 0x90000 or a >= 0x600000 or a not in IDX: seen[a] = 'EXTERN/NONSTART'; continue
        t = get(a); seen[a] = t.splitlines()[0]
        for m in re.finditer(r'\s(?:call|jmp)\s+([0-9a-f]+) <([^>]*)>', t):
            if '+0x' in m.group(2): continue
            todo.append(int(m.group(1), 16))
    return seen
if __name__ == '__main__':
    for a, n in sorted(emit_all().items()): print('%x' % a, n[:170])
