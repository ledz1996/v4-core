"""Run every case through Monad's interpreter and Monad's native x86 code with the cycle 23 harness (hx), at v0.16.5
and v0.16.7. One world and one scenario per case (codes, the two token doubles of the case funded for the driver, and
any override storage), one transaction from EOA to the driver with run([case]). The harness compares the whole result
of the two engines (trace, storage, transient storage, balances, token balances, logs); this script also decodes the
driver's return words of each engine for comparison with the reference EVM.
A first version ran all cases against one world holding every case's tokens; the harness's interpreter side then gave
varying results between runs of the same scenario (out/hx/rep1369.txt), which disappear with a per-case world
(out/hx/rep1369b.txt). Usage: python3 hxrun.py <allcases.json> <outdir>"""
import sys, os, json, subprocess, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
HX = os.path.join(NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
hb = json.load(open(os.path.join(WORK, 'build', 'driver-hx.json')))
drv = bytes.fromhex(hb['driver']).replace(PLACEHOLDER, PM.to_bytes(20, 'big'))
allc = json.load(open(sys.argv[1])); cases = allc['cases']; outdir = sys.argv[2]
tmp = os.path.join(outdir, 'hx', 'tmp'); os.makedirs(tmp, exist_ok=True)
base = [f'code {PM:040x} {pm_build(PM).hex()}', f'code {D:040x} {drv.hex()}', f'code {S:040x} {drv.hex()}']
res = {'0.16.5': {}, '0.16.7': {}}
t0 = time.time()
for c in cases:
    world = list(base)
    for t in (c.get('t0'), c.get('t1')):
        if t: world += [f'token {t:040x}', f'tok {t:040x} {D:040x} {(1 << 250):x}']
    for k, v in c.get('storage', {}).items(): world.append(f'st {PM:040x} {int(k, 16):064x} {int(v, 16):064x}')
    wf = os.path.join(tmp, 'w.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(tmp, 's.txt'); open(sf, 'w').write(f'SCEN case{c["id"]}\nTX {EOA:040x} {D:040x} 00 150000000 {enc_run([c]).hex()}\n')
    for ver in res:
        p = subprocess.run([os.path.join(HX, f'{ver}-plain', 'hx'), wf, sf, '-v'], capture_output=True, text=True)
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        same = p.stdout.startswith('SAME')
        dec = []
        for st, g, o in outs:
            try:
                r = dec_run(bytes.fromhex(o))[0]
                dec.append({'status': st, 'gas': int(g), 'ok': r[0], 'w': [hex(x) for x in r[1]] if r[1] else None, 'revert': r[2].hex()})
            except Exception as e:  # noqa
                dec.append({'status': st, 'gas': int(g), 'raw': o[:200]})
        res[ver][c['id']] = {'same': same, 'interp': dec[0] if dec else None, 'native': dec[1] if len(dec) > 1 else None, 'rc': p.returncode}
    if c['id'] % 100 == 0: print(c['id'], round(time.time() - t0), flush=True)
json.dump(res, open(os.path.join(outdir, 'hx-results.json'), 'w'))
for ver in res:
    print(ver, 'scenarios', len(res[ver]), 'engine DIFF', sum(1 for x in res[ver].values() if not x['same']))
