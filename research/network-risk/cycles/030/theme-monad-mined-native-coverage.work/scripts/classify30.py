"""Task 2: the compiled IR blocks (913, Monad v0.16.7 compiler, cycle 28 covtable) that no sampled mined transaction entered,
with their src/ lines (solc source map through cycle 28 blocks.py) and the conditional jumps of opcodes/jumpmap.json
that sit in them, split into: unreachable (cycle 28 task 4 reasons), revert paths (the block ends in REVERT/INVALID or is a
CustomRevert/panic helper), dispatch and ABI decoding of functions the sample never called, and value-computing paths
(with the src/ function named). Also the per-library coverage of the math blocks.
Usage: python3 -I classify30.py <hits.json> <out.json>"""
import sys, os, json, re, collections
NR = '/home/user/v4-core/research/network-risk'; R = '/home/user/v4-core'
C28 = os.path.join(NR, 'cycles', '028', 'theme-monad-native-unentered-blocks.work')
sys.path.insert(0, os.path.join(C28, 'scripts')); import blocks as BL
cov = json.load(open(os.path.join(C28, 'out', 'covtable-0.16.7.json'))); rows = {r['block']: r for r in cov['rows']}
unr = {x['block']: x['why'] for x in json.load(open(os.path.join(C28, 'out', 'summary.json')))['task4']}
jm = json.load(open(os.path.join(NR, 'opcodes', 'jumpmap.json')))
H = json.load(open(sys.argv[1]))['hits']
offs = sorted(int(o, 16) for o in H); spans = BL.block_spans(offs); code = BL.code
_fn = {}
def func_of(path, line):
    if path not in _fn:
        L = open(os.path.join(R, path)).read().split('\n'); fs = []
        for i, t in enumerate(L, 1):
            m = re.search(r'\bfunction\s+(\w+)', t)
            if m: fs.append((i, m.group(1)))
        _fn[path] = fs
    best = None
    for i, n in _fn[path]:
        if i <= line: best = n
    return best
def wide(pc):
    r = BL.M.get(pc); return f'{r[0]}:{r[1]}-{r[2]}' if r else None
jumps = collections.defaultdict(list)
for k in ('oneSided', 'neverReached'):
    for e in jm.get(k, []): jumps[e['pc']].append({'kind': k, 'src': f"{e['src']['file']}:{e['src']['line']}", 'why': e.get('why', '')[:200]})
MATH = ['FullMath', 'SqrtPriceMath', 'SwapMath', 'TickMath', 'TickBitmap', 'LiquidityMath', 'Position', 'Pool', 'BitMath', 'UnsafeMath']
out = []; per = {m: {'blocks': 0, 'entered': 0, 'notEntered': []} for m in MATH}
for o in offs:
    h = hex(o); sp = spans[o]; src = rows[h]['src']; ops = [code[p] for p in sp]
    files = {s.split(':')[0].split('/')[-1].replace('.sol', '') for s in src}
    for m in MATH:
        if m in files:
            per[m]['blocks'] += 1
            if H[h]: per[m]['entered'] += 1
            else: per[m]['notEntered'].append(h)
    if H[h]: continue
    last = ops[-1]; js = [j for p in sp for j in jumps.get(p, [])]
    if h in unr: cls = 'unreachable'; why = unr[h]
    elif last in (0xfd, 0xfe) or any('CustomRevert.sol' in s for s in src): cls = 'revert'; why = 'ends in REVERT or INVALID' if last in (0xfd, 0xfe) else 'CustomRevert helper call'
    elif not src: cls = 'dispatch-decode'; why = 'no narrow source range; selector dispatch or ABI decoding (' + (wide(sp[0]) or '?') + ')'
    else:
        cls = 'value'; why = ''
    fns = sorted({f"{s.split(':')[0].split('/')[-1]}:{func_of(s.split(':')[0], int(s.split(':')[1].split('-')[0]))}" for s in src if s.startswith('src/')})
    out.append({'block': h, 'class': cls, 'why': why, 'src': src, 'functions': fns, 'jumpmap': js, 'changed167': rows[h]['changed167'],
                'lastOp': BL.OPN.get(last, hex(last))})
c = collections.Counter(x['class'] for x in out)
json.dump({'notEntered': len(out), 'byClass': c, 'math': per, 'blocks': out}, open(sys.argv[2], 'w'), indent=1)
print(len(out), dict(c)); print(json.dumps({m: {k: v for k, v in d.items() if k != 'notEntered'} | {'n': len(d['notEntered'])} for m, d in per.items()}))
for x in out:
    if x['class'] == 'value': print(x['block'], x['functions'], x['src'][:3])
