# Summarise out/: marker counts per site (native and interpreter), the operands the interpreter saw at each
# site, the site's result in both engines against Python, and the result each prologue call returned.
import json, re, collections, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
M = (1 << 256) - 1
ex = json.load(open('runs/expect.json'))
def sar(s, x):
    if x >> 255: x -= 1 << 256
    return (x >> min(s, 255)) & M
summary = {}
for name, site in (('q128', 22378), ('q96', 22639), ('sar', 15519), ('shl', 16642), ('cdl', 12232), ('hook', 15519), ('pmq96', 22639), ('pmq128', 22378)):
    for v in ('167', '165'):
        rec = collections.defaultdict(dict)
        cnt = open('out/%s-%s-cnt.out' % (name, v)).read(); cap = open('out/%s-%s-cap.out' % (name, v)).read()
        marks = collections.Counter(); imarks = collections.Counter(); scen_hit = 0
        for m in re.finditer(r'^MARK (\S+) pc=(\d+) native=(\d+) interp=(\d+)', cnt, re.M):
            marks[int(m.group(2))] += int(m.group(3)); imarks[int(m.group(2))] += int(m.group(4))
            if int(m.group(2)) == site and int(m.group(3)) > 0: scen_hit += 1
        mism = [re.search(r'mismatches=(\d+)', t).group(1) for t in (cnt, cap)]
        pre = collections.defaultdict(list); ints = collections.defaultdict(list); nats = collections.defaultdict(list)
        for l in open('out/%s-%s.pre' % (name, v)):
            p = l.split()
            if p[1] == 'pre' and int(p[2]) == site: pre[p[0]].append([int(x, 16) for x in p[3:6]])
            elif p[1] == 'int': ints[p[0]].append(int(p[3], 16))
            elif p[1] == 'nat': nats[p[0]].append(int(p[3], 16))
        # outputs of the prologue calls (tx 0 of each scenario, interpreter dump == native dump already)
        outs = {}
        for m in re.finditer(r'^(SAME|DIFF) (\S+)', cap, re.M): pass
        nsite = sum(len(x) for x in pre.values())
        eq_engines = all(ints[k] == nats.get(k) for k in ints) and set(ints) == set(nats)
        spec_bad = 0; spec_n = 0; classes = collections.Counter()
        for k, ops in pre.items():
            for (o0, o1, o2), r_int in zip(ops, ints[k]):
                if site in (22378, 22639):
                    want = (o0 * o1) % o2 if o2 else 0
                    p = o0 * o1; p1 = p >> 256; p0 = p & M
                    classes['prod1=%s' % ('1' if p1 == 1 else ('max' if p1 == o2 - 1 else ('0' if p1 == 0 else 'other')))] += 1
                    if p1 == 1:
                        for nm, val in (('0', 0), ('1', 1), ('2^96-1', (1 << 96) - 1), ('2^96', 1 << 96), ('2^96+1', (1 << 96) + 1), ('2^128-1', (1 << 128) - 1), ('2^128', 1 << 128), ('2^128+1', (1 << 128) + 1), ('N-1', o2 - 1), ('N', o2), ('N+1', o2 + 1)):
                            if p0 == val: classes['prod1=1,prod0=' + nm] += 1
                        if p0 < o2: classes['prod1=1,prod0<N'] += 1
                        if p0 < r_int: classes['prod1=1,prod0<remainder'] += 1
                elif site == 15519: want = sar(o0, o1)
                elif site == 16642: want = (o1 << o0) & M if o0 < 256 else 0
                else: want = None
                if want is not None:
                    spec_n += 1; spec_bad += (want != r_int)
        summary['%s v0.16.%s' % (name, v[2])] = {'site': site, 'scenarios': len(re.findall(r'^(SAME|DIFF) ', cnt, re.M)),
            'mismatchesCounterBuild': int(mism[0]), 'mismatchesCaptureBuild': int(mism[1]),
            'nativeMarkerCount': marks[site], 'interpreterCount': imarks[site], 'scenariosReachingSite': scen_hit,
            'siteResultsCompared': nsite, 'nativeEqualsInterpreterAtSite': eq_engines, 'checkedAgainstPython': spec_n, 'pythonMismatches': spec_bad,
            'otherSiteMarkers': {str(k): marks[k] for k in marks if k != site and marks[k]}, 'operandClasses': dict(classes)}
# prologue return values against Python mulDiv
for nm in ('q128', 'q96'):
    for v in ('167', '165'):
        cap = open('out/%s-%s-cap.out' % (nm, v)).read()
        bad = 0; n = 0; reverts = 0
        blocks = re.split(r'^(?=SAME |DIFF )', cap, flags=re.M)
        # outputs are not printed without -v; rerun is avoided: use the interpreter result recorded in dump? Use -v run.
summary_path = 'out/summary.json'
json.dump(summary, open(summary_path, 'w'), indent=1)
for k, s in summary.items(): print(k, json.dumps(s))
