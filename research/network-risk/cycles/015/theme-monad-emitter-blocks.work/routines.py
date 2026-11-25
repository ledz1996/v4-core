"""Classify the x86 that the emitter wrote for each EVM instruction of the target blocks."""
import re, json, glob, collections
out = {}
for f in sorted(glob.glob('blocks/*.asm')):
    name = f.split('/')[-1][:-4]
    lines = open(f).read().split('\n')
    cur = None; seq = []; kinds = collections.Counter()
    def flush():
        if cur is None: return
        body = [l for l in seq if l and not l.startswith('//') and not re.match(r'^[A-Za-z0-9_]+:$', l)]
        txt = '\n'.join(body)
        if not body: k = 'virtual-stack-only (no code)'
        elif 'call qword ptr [ROD' in txt: k = 'runtime-call'
        elif 'ymm' in txt or 'xmm' in txt: k = 'avx'
        elif re.search(r'\b(sbb|adc|cmp)\b', txt): k = 'gpr-4limb-arith-or-compare'
        elif re.search(r'\bset[a-z]+\b', txt): k = 'flags-materialised'
        elif re.search(r'\b(shl|shr|sar|shld|shrd|shlx|shrx|sarx)\b', txt): k = 'gpr-shift'
        elif 'JumpTable' in txt: k = 'dynamic-jump-table'
        elif re.search(r'\bj[a-z]+ ', txt): k = 'branch'
        else: k = 'gpr-other'
        kinds[(cur, k)] += 1
    for l in lines:
        m = re.match(r'^//\s+0x[0-9a-f]+: (\w+)', l)
        if m:
            flush(); cur = m.group(1); seq = []
        else:
            seq.append(l)
    flush()
    out[name] = {'%s|%s' % k: v for k, v in sorted(kinds.items())}
json.dump(out, open('blocks/routines.json', 'w'), indent=1)
tot = collections.Counter()
for v in out.values():
    for k, n in v.items(): tot[k.split('|')[1]] += n
print(tot)
