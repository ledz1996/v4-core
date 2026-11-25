# Task 3 classes of returned swap deltas through the hook double, outcome of the ordinary calls that reach the
# 2^96 and 2^128 sites, and prologue return values against Python mulDiv.
import re, json, collections
M = (1 << 256) - 1
def i128(x): x &= (1 << 128) - 1; return x - (1 << 128) if x >> 127 else x
def scen_blocks(path):
    t = open(path).read(); out = {}
    for m in re.finditer(r'^(SAME|DIFF) (\S+)\n--- interp\n(.*?)--- native\n', t, re.S | re.M): out[m.group(2)] = (m.group(1), m.group(3))
    return out
res = {}
# hook swaps: step 1 is the swap
cls = collections.Counter(); want = {}
targets = {'-1': -1, '-2^127': -(1 << 127), '2^127-1': (1 << 127) - 1, '0': 0}
examples = {}
for name, (same, body) in scen_blocks('out/hook-167-v.txt').items():
    m = re.search(r'^  step 1 to=\S+ status=(\S+) gasleft=\d+ out=(\S*)', body, re.M)
    if not m: continue
    st, out = m.group(1), m.group(2)
    cls['swap ' + st] += 1
    if st == 'success' and len(out) == 64:
        d = int(out, 16); a0 = i128(d >> 128); a1 = i128(d)
        for tn, tv in targets.items():
            if a0 == tv and a1 < 0: cls['amount0=%s, amount1<0' % tn] += 1; examples.setdefault('amount0=%s, amount1<0' % tn, name)
            if a1 == tv and a0 < 0: cls['amount1=%s, amount0<0' % tn] += 1; examples.setdefault('amount1=%s, amount0<0' % tn, name)
            if a0 == tv: cls['amount0=%s' % tn] += 1
            if a1 == tv: cls['amount1=%s' % tn] += 1
res['hookSwaps'] = {'classes': dict(cls), 'examples': examples}
# ordinary calls reaching 22639
q = json.load(open('runs/pm-q96.json'))
kinds = {0: 'exact input below 2^160', 1: 'exact input above 2^160', 2: 'exact output of token0', 3: 'exact output (positive amount)'}
cnt = open('out/pmq96-167-cnt.out').read() if False else open('out/pmq96-167-v.txt').read()
marks = {m.group(1): int(m.group(2)) for m in re.finditer(r'^MARK (\S+) pc=22639 native=(\d+)', open('out/pmq96-167-cnt.out').read(), re.M)}
byk = collections.defaultdict(collections.Counter)
for name, (same, body) in scen_blocks('out/pmq96-167-v.txt').items():
    i = int(name.split('-')[1]); k = kinds[i % 4]
    st = re.findall(r'^  step (\d) to=\S+ status=(\S+) gasleft=\d+ out=(\S*)', body, re.M)
    s = {int(a): (b, c) for a, b, c in st}
    byk[k]['scenarios'] += 1
    byk[k]['reached 22639'] += marks.get(name, 0) > 0
    byk[k]['site executions'] += marks.get(name, 0)
    if 1 in s: byk[k]['swap ' + s[1][0] + ((' ' + s[1][1][:8]) if s[1][0] == 'revert' else '')] += 1
    m3 = [x for x in st if x[0] == '6']
    for x in st:
        if x[0] in ('2', '3', '4', '5', '6', '7', '8', '9'):
            pass
    ml = re.findall(r'^  step (\d+) to=\S+ status=(\S+) gasleft=\d+ out=(\S*)', body, re.M)
    if ml: byk[k]['last modifyLiquidity ' + ml[-1][1] + ((' ' + ml[-1][2][:8]) if ml[-1][1] == 'revert' else '')] += 1
res['ordinary2^96'] = {k: dict(v) for k, v in byk.items()}
res['ordinary2^96prod1'] = collections.Counter(str(v['prod1']) for v in q.values())
# ordinary calls reaching 22378
marks = {m.group(1): int(m.group(2)) for m in re.finditer(r'^MARK (\S+) pc=22378 native=(\d+)', open('out/pmq128-167-cnt.out').read(), re.M)}
c = collections.Counter()
for name, (same, body) in scen_blocks('out/pmq128-167-v.txt').items():
    if marks.get(name, 0):
        st = re.findall(r'^  step (\d+) to=\S+ status=(\S+) gasleft=\d+ out=(\S*)', body, re.M)
        for a, b, o in st:
            c['step %s %s %s' % ('poke/remove', b, o[:8])] += 0
        last = [x for x in st if x[1] == 'revert']
        c['reverting steps: ' + ','.join(sorted(set(x[2][:8] for x in last)))] += 1
res['ordinary2^128'] = dict(c)
# prologue return values
ex = json.load(open('runs/expect.json'))
for nm in ('q128', 'q96'):
    bad = 0; n = 0; rev = 0; okrev = 0
    for name, (same, body) in scen_blocks('out/%s-167-v.txt' % nm).items():
        m = re.search(r'^tx 0 status=(\S+) gasleft=\d+ out=(\S*)', body, re.M); e = ex[nm][name]
        if e['result'] is None:
            okrev += m.group(1) != 'success'; rev += 1
        else:
            n += 1; bad += not (m.group(1) == 'success' and int(m.group(2), 16) == e['result'])
    res['prologue ' + nm] = {'returned': n, 'wrongAgainstPython': bad, 'expectedReverts': rev, 'reverted': okrev}
for nm in ('sar', 'shl'):
    n = sum(1 for _ in scen_blocks('out/%s-167-v.txt' % nm)); res['prologue ' + nm] = {'scenarios': n}
json.dump(res, open('out/summary2.json', 'w'), indent=1, default=dict)
print(json.dumps(res, indent=1, default=dict))
