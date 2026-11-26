# Find "sbb r,r" (carry mask) on amd64, or "csetm/ngc"-style masks on arm64, and report the first flag reader that follows
# before any flag writer, on the fall-through path.
import sys, re
arch = sys.argv[2] if len(sys.argv) > 2 else 'amd64'
lines = open(sys.argv[1]).read().split('\n')
fn = None; ins = []
for l in lines:
    if l.startswith('### '): fn = l[4:]; continue
    m = re.match(r'\s+([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(\S+)\s*(.*)', l)
    if m: ins.append((fn, m.group(1), m.group(2), m.group(3).strip()))
W86 = re.compile(r'^(add|sub|cmp|test|and|or|xor|inc|dec|neg|shl|shr|sar|sal|rol|ror|adc|sbb|bt|bts|btr|bsf|bsr|tzcnt|lzcnt|popcnt|imul|mul|div|idiv|cmpxchg|xadd|bzhi|andn|blsr|shld|shrd)')
R86 = re.compile(r'^(set|cmov|j(?!mp)|adc|sbb|rcl|rcr)')
CT86 = re.compile(r'^(jmp|call|ret|ud2|int3)')
W64 = re.compile(r'^(adds|subs|cmp|cmn|tst|ands|bics|adcs|sbcs|ccmp|ccmn|negs|ngcs)')
R64 = re.compile(r'^(cset|csetm|csel|csinc|csinv|csneg|cinc|cinv|cneg|b\.|adc|sbc|ngc|ccmp|ccmn)')
CT64 = re.compile(r'^(b$|bl$|br$|blr$|ret)')
hits = []; masks = 0
for i, (f, a, op, args) in enumerate(ins):
    if arch == 'amd64':
        r = re.match(r'%(\w+),%(\w+)$', args)
        if not (op.startswith('sbb') and r and r.group(1) == r.group(2)): continue
        W, R, CT = W86, R86, CT86
    else:
        # arm64 lowering of carry masks: ngc/sbc x,xzr,xzr or csetm on cs/cc
        if not (op in ('ngc', 'sbc', 'csetm') and ('xzr, xzr' in args or op == 'csetm')): continue
        W, R, CT = W64, R64, CT64
    masks += 1
    if arch == 'amd64' or op != 'csetm':
        pass
    for j in range(i + 1, min(i + 40, len(ins))):
        f2, a2, op2, args2 = ins[j]
        if f2 != f: break
        if R.match(op2):
            hits.append((f, a, op, args, a2, op2, args2)); break
        if W.match(op2) or CT.match(op2): break
print('carry masks', masks, 'masks whose flags reach a reader', len(hits))
for h in hits: print(*h)
