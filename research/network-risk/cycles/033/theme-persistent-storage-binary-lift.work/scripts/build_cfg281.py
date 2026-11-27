"""Build the cycle 32 arith.py configuration for the op-reth v2.8.1 amd64 binary: map the 73 functions of the
v2.10.0-rc.4 arithmetic closure (cycles/032/.../build/opreth-amd64-arith.json) to v2.8.1 by following the handlers'
direct calls pairwise (cmp_reth.py), print their text with objdump, and take the GOT slots by relocation symbol.
Reads files only. usage: python3 -I build_cfg281.py <new bin> <rel> <fde> <outdir>"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
newbin, rel, fde, outdir = sys.argv[1:5]
sys.argv = ['x', newbin, rel, fde, '/dev/null']
import cmp_reth as C
C32 = C.C32
old, new = C.load(dict(C.OLD)), C.load(dict(C.NEW))
ocfg = json.load(open(C32 + 'build/opreth-amd64.cfg.json'))
oar = json.load(open(C32 + 'build/opreth-amd64-arith.json'))
T_old = C.OLD['table']
r = json.load(open(os.path.join(os.path.dirname(HERE), 'out/cmp-opreth281-amd64.json')))
T_new = int(r['newTable'], 16)
# pairs: every function reachable from the table's arithmetic handlers (all EXP variants included)
pairs = []
for op, code in C.OPS.items():
    pairs.append((old['relm'][T_old + 8 * code], new['relm'][T_new + 8 * code]))
for i, (oa, na) in enumerate(zip(r['arithHandlersPerOpOld']['EXP'], r['arithHandlersPerOpNew']['EXP'])):
    pairs.append((int(oa, 16), int(na, 16)))
m, ext = {}, {}
while pairs:
    oa, na = pairs.pop()
    if oa in m or oa in ext:
        continue
    try:
        orng, nrng = C.fn_range(old, oa), C.fn_range(new, na)
    except AssertionError:
        ext[oa] = na
        continue
    m[orng[0]] = nrng
    pairs += list(zip(C.calls(old, *orng), C.calls(new, *nrng)))
want = [int(a, 16) for a in oar['functions']]
missing = [hex(a) for a in want if a not in m]
texts = []
for a in want:
    if a in m:
        lo, hi = m[a]
        out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x%x' % lo,
                              '--stop-address=0x%x' % hi, newbin], capture_output=True, text=True).stdout
        texts.append('\n'.join(l for l in out.splitlines() if re.match(r'^\s*[0-9a-f]+:\s', l)))
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, 'opreth281-amd64-arith.s'), 'w').write('\n'.join(texts) + '\n')
got = {}
for l in subprocess.run(['readelf', '-rW', newbin], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 5 and p[2] == 'R_X86_64_GLOB_DAT':
        for sym, kind in (('memcpy@', 'memcpy'), ('memset@', 'memset'), ('memmove@', 'memmove'), ('abort@', 'panic')):
            if p[4].startswith(sym):
                got['0x%x' % int(p[0], 16)] = kind
externs = {('0x%x' % ext[int(k, 16)]): v for k, v in ocfg['externs'].items() if int(k, 16) in ext}
cfg = dict(ocfg)
cfg.update({'bin': newbin, 'asm': os.path.join(outdir, 'opreth281-amd64-arith.s'), 'table': hex(T_new), 'rel': rel,
            'got': got, 'externs': externs, 'faults': {}})
json.dump(cfg, open(os.path.join(outdir, 'opreth281-amd64.cfg.json'), 'w'), indent=1)
json.dump({'map': {hex(k): [hex(v[0]), hex(v[1])] for k, v in m.items()}, 'external': {hex(k): hex(v) for k, v in ext.items()},
           'missing': missing}, open(os.path.join(outdir, 'opreth281-amd64-map.json'), 'w'), indent=1)
print('mapped', len([a for a in want if a in m]), 'of', len(want), 'missing', missing, 'got', got, 'externs', externs)
