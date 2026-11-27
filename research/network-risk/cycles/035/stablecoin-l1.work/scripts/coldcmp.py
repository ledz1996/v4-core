"""Second pass of bincmp.py: for each 'entry offset' mismatch (a branch into another FDE fragment, usually a cold
or panic block), compares the straight-line instruction streams from the two targets up to the first ret, jmp,
ud2 or call, with absolute addresses replaced, and reports per opcode which handler trees are equal.
usage: python3 -I coldcmp.py <old bin> <new bin> <bincmp.json> <out.json>"""
import json, re, subprocess, sys
OB, NB, IN, OUT = sys.argv[1:5]
d = json.load(open(IN))
HEX = re.compile(r'\b(?:0x)?([0-9a-f]{5,})\b')
def stream(b, a):
    t = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=' + hex(a), '--stop-address=' + hex(a + 400), b], capture_output=True, text=True).stdout
    out = []
    for l in t.splitlines():
        m = re.match(r'^ *([0-9a-f]+):\t(.*)$', l)
        if not m: continue
        x = re.sub(r'#.*', '', m.group(2)); x = re.sub(r'<[^>]*>', '', x)
        out.append(HEX.sub('ADDR', x).strip())
        op = x.split()[0] if x.split() else ''
        if op in ('ret', 'jmp', 'ud2', 'call', 'int3') or op.startswith('ret'): break
    return out
res = {'cold': [], 'other': []}
for lab, oa, na, why in d['mismatches']:
    if why == 'entry offset':
        so, sn = stream(OB, int(oa, 16)), stream(NB, int(na, 16))
        res['cold'].append({'label': lab, 'old': oa, 'new': na, 'equal': so == sn, 'len': len(so), 'last': so[-1] if so else None, 'diff': None if so == sn else [so, sn]})
    else:
        res['other'].append([lab, oa, na, why])
ops = {}
for lab in [p[1] for p in d['pairs'].values()]:
    ops.setdefault(lab.split('>')[0], 0)
bad = {}
for c in res['cold']:
    if not c['equal']: bad.setdefault(c['label'].split('>')[0], []).append(c['label'])
for o in res['other']:
    bad.setdefault(o[0].split('>')[0], []).append(o[0] + ' ' + o[3][:80])
res['handlerRootsCompared'] = len(ops); res['rootsWithDifference'] = bad
res['rootsEqual'] = sorted(k for k in ops if k not in bad)
json.dump(res, open(OUT, 'w'), indent=1)
print('cold', len(res['cold']), 'cold equal', sum(c['equal'] for c in res['cold']), 'other', len(res['other']))
print('roots', len(ops), 'with difference', {k: len(v) for k, v in bad.items()})
