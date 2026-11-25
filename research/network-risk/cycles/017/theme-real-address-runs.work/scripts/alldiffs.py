"""List every differing call (not only the first) between a network's real-address record and Ethereum's, for the scripts
compare.py flagged. Usage: python3 alldiffs.py <set> <out.json>"""
import sys, os, json, gzip
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import compare as C
s = sys.argv[1]
cmp_ = json.load(open(os.path.join(HERE, '..', 'raw', 'compare.json')))['set' + s]
E = C.load(s, 'real', 1)
locked = [False] * len(E['kinds'])
if s == '6':
    import pmdiff6 as S6
    locked = [d[:1] == b'\xff' for _, d in S6.scripts()]
out = {}
for cid, v in cmp_['networks'].items():
    if isinstance(v, str): continue
    X = C.load(s, 'real', int(cid))
    for i in v['differentFromEthereumReal']:
        a = C.calls(s, None, C.norm(C.raw(X['results'][i]), X['pm']), locked[i]); b = C.calls(s, None, C.norm(C.raw(E['results'][i]), E['pm']), locked[i])
        if a is None or b is None: out.setdefault(cid, {})[str(i)] = 'no record'; continue
        d = [[k, x[0], x[1].hex(), y[0], y[1].hex()] for k, (x, y) in enumerate(zip(a, b)) if x != y]
        out.setdefault(cid, {})[str(i)] = {'calls': [len(a), len(b)], 'diffs': d}
json.dump(out, open(sys.argv[2], 'w'), indent=0)
