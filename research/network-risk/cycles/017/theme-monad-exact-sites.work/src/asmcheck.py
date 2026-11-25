# For each release: the counter build's text at the five sites equals the plain build (counter lines
# removed), and each single-site capture build's text at its site starts with the plain text.
import sys, re
def load(p): return [l for l in open(p).read().split('\n') if not l.startswith('.db')]
def section(lines, pc):
    h = '//       0x%02x:' % pc; out = []; on = False
    for l in lines:
        if l.startswith(h): on = True; out.append(l); continue
        if on and (re.match(r'^//\s+0x[0-9a-f]+:', l) or re.match(r'^L\d+:', l)): break
        if on: out.append(l)
    return out
f = lambda L: [l for l in L if '[abs ' not in l and 'lea rax, qword ptr [rax+1]' not in l]
res = {}
for v in ('167', '165'):
    pl = load('asm/plain%s.asm' % v); cn = load('asm/cnt%s.asm' % v)
    other = [l for l in cn if '[abs ' not in l and 'lea rax, qword ptr [rax+1]' not in l]
    res[v] = {'counterBuildEqualsPlainOutsideCounters': other == pl}
    for pc in (22378, 22639, 15519, 16642, 12232):
        sp = f(section(pl, pc)); sc = f(section(cn, pc)); cp = f(section(load('asm/cap%s-%d.asm' % (v, pc)), pc))
        res[v][pc] = {'plainLines': len(sp), 'counterBuildSame': sc == sp, 'captureBuildPrefix': cp[:len(sp)] == sp, 'text': sp}
import json; json.dump(res, open('asm/sitecheck.json', 'w'), indent=1)
for v in res:
    print(v, 'counter build equals plain apart from counters:', res[v]['counterBuildEqualsPlainOutsideCounters'])
    for pc in (22378, 22639, 15519, 16642, 12232): r = res[v][pc]; print(' ', pc, r['plainLines'], r['counterBuildSame'], r['captureBuildPrefix'])
