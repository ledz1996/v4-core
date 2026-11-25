# Compare two asm logs instruction by instruction, ignoring the read-only data line; print every
# inserted or changed line, and the exact text of each site's instruction in both.
import sys, difflib, re
a = [l for l in open(sys.argv[1]).read().split('\n') if not l.startswith('.db')]
b = [l for l in open(sys.argv[2]).read().split('\n') if not l.startswith('.db')]
sites = [int(x) for x in sys.argv[3].split(',')]
def section(lines, pc):
    h = '//       0x%02x:' % pc
    out = []; on = False
    for l in lines:
        if l.startswith(h): on = True; out.append(l); continue
        if on and (re.match(r'^//\s+0x[0-9a-f]+:', l) or re.match(r'^L\d+:', l) or l.startswith('B')): break
        if on: out.append(l)
    return out
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
ins = []; chg = []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'insert': ins.append(b[j1:j2])
    elif op != 'equal': chg.append((a[i1:i2], b[j1:j2]))
print('inserted blocks', len(ins), 'changed blocks', len(chg))
for blk in ins: print('INS', ' | '.join(blk)[:300])
for x, y in chg[:20]: print('CHG', ' | '.join(x)[:200], ' ==> ', ' | '.join(y)[:300])
for pc in sites:
    sa = [l for l in section(a, pc) if '[abs ' not in l and 'lea rax, qword ptr [rax+1]' not in l]; sb = [l for l in section(b, pc) if '[abs ' not in l and 'lea rax, qword ptr [rax+1]' not in l]
    print(pc, 'site text identical' if sa == sb else 'SITE TEXT DIFFERS', len(sa))
