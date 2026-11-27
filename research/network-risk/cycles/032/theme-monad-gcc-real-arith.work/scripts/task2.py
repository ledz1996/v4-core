"""Task 2 summary per site from realarith.json: argument registers, result pointer, spill stores emitted before the
call, vzeroupper before the call, and the helper reached. usage: python3 -I task2.py <realarith.json> <out.json>"""
import sys, json, re
d = json.load(open(sys.argv[1])); out = []
for s in d['sites']:
    g = [l.split('\t', 1)[1].strip() for l in s.get('gccStream', []) if '\t' in l]
    ci = [i for i, l in enumerate(g) if l.startswith('call')]
    row = {'block': s['block'], 'pc': s['pc'], 'op': s['op'], 'operands': s['operands'], 'calls': len(ci)}
    if ci:
        pre = g[:ci[0]]
        row['args'] = {m.group(1): m.group(2) for m in (re.match(r'lea (r\w+),\[(.*)\]', l) for l in pre) if m}
        row['spillStores'] = [l for l in pre if re.match(r'(mov|vmovaps|vmovdqa|vmovdqu) (QWORD|YMMWORD) PTR \[rbp', l)]
        row['vzeroupperBeforeCall'] = 'vzeroupper' in pre
        row['helperConst'] = s.get('rodconst')
    row['liveRegsAfterEmit'] = s.get('liveRegsAfterEmit'); row['stream'] = s.get('stream'); row['postState'] = s.get('postState')
    out.append(row)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
for r in out: print(r['pc'], r['op'], r.get('args'), len(r.get('spillStores', [])), r.get('vzeroupperBeforeCall'), r.get('helperConst'), r['liveRegsAfterEmit'])
