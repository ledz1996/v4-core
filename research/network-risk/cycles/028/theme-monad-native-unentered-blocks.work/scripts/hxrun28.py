"""Cycle 28 copy of cycles/027/theme-monad-engine-agreement.work/scripts/hxrun25b.py with binaries from this work dir (build/<ver>/hxf, hxfcov); HX28_PRE prefixes a command such as valgrind. Original text: rerun the 1,533 cycle 25 cases (cycles/025/theme-unexecuted-sides.work/out/allcases.json) through the fixed
harness build/<ver>/hxf, or with --old the cycle 23 hx binaries, with the per-case world of the cycle 25 script
scripts/hxrun.py of that unit (same world and scenario lines). Raw stdout per case kept.
Usage: python3 hxrun25b.py <allcases.json> <outdir> [--old] [--env K=V] [--ids a,b] [--shared]
--shared builds one world with every selected case's tokens and storage lines and one scenario file with all cases
(the first cycle 25 layout, which exposed the harness fault)."""
import sys, os, json, subprocess, time, re
from concurrent.futures import ThreadPoolExecutor
W28 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W27 = os.path.abspath(os.path.join(W28, '..', '..', '027', 'theme-monad-engine-agreement.work'))
S25 = os.path.abspath(os.path.join(W27, '..', '..', '025', 'theme-unexecuted-sides.work', 'scripts'))
sys.path.insert(0, S25)
from common import *  # noqa
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
hb = json.load(open(os.path.join(WORK, 'build', 'driver-hx.json')))
drv = bytes.fromhex(hb['driver']).replace(PLACEHOLDER, PM.to_bytes(20, 'big'))
args = sys.argv[1:]
cases = json.load(open(args[0]))['cases']; outdir = args[1]; old = '--old' in args; shared = '--shared' in args
env = dict(os.environ)
for i, a in enumerate(args):
    if a == '--env': k, v = args[i + 1].split('=', 1); env[k] = v
    if a == '--ids': ids = [int(x) for x in args[i + 1].split(',')]; cases = [c for c in cases if c['id'] in ids]
HXOLD = os.path.join(NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
PRE = os.environ.get('HX28_PRE', '').split()
COV = '--cov' in args  # fixed harness linked with the cycle 23 coverage-patched emitter; HX_COVOUT per case
def binpath(ver): return os.path.join(HXOLD, f'{ver}-plain', 'hx') if old else os.path.join(W28, 'build', ver, 'hxfcov' if COV else 'hxf')
tmp = os.path.join(outdir, 'tmp'); raw = os.path.join(outdir, 'raw'); os.makedirs(tmp, exist_ok=True); os.makedirs(raw, exist_ok=True)
base = [f'code {PM:040x} {pm_build(PM).hex()}', f'code {D:040x} {drv.hex()}', f'code {S:040x} {drv.hex()}']
def wlines(c):
    world = []
    for t in (c.get('t0'), c.get('t1')):
        if t: world += [f'token {t:040x}', f'tok {t:040x} {D:040x} {(1 << 250):x}']
    for k, v in c.get('storage', {}).items(): world.append(f'st {PM:040x} {int(k, 16):064x} {int(v, 16):064x}')
    return world
def dec(o):
    try:
        r = dec_run(bytes.fromhex(o))[0]
        return {'ok': r[0], 'w': [hex(x) for x in r[1]] if r[1] else None, 'revert': r[2].hex()}
    except Exception:  # noqa
        return {'raw': o[:200]}
def parse(stdout):
    res = {}
    for blk in re.split(r'(?m)^(?=SAME |DIFF )', stdout):
        m = re.match(r'(SAME|DIFF) case(\d+)', blk)
        if not m: continue
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', blk)
        d = [dict(status=s, gas=int(g), **dec(o)) for s, g, o in outs]
        res[m.group(2)] = {'same': m.group(1) == 'SAME', 'interp': d[0] if d else None, 'native': d[1] if len(d) > 1 else None}
    return res
def scen(c): return f'SCEN case{c["id"]}\nTX {EOA:040x} {D:040x} 00 150000000 {enc_run([c]).hex()}\n'
def one(c):
    wf = os.path.join(tmp, f'w{c["id"]}.txt'); open(wf, 'w').write('\n'.join(base + wlines(c)) + '\n')
    sf = os.path.join(tmp, f's{c["id"]}.txt'); open(sf, 'w').write(scen(c))
    out = {}
    for ver in VERS:
        e2 = dict(env, HX_COVOUT=os.path.join(outdir, 'cov', f'{ver}-case{c["id"]}.cov')) if COV else env
        if COV: os.makedirs(os.path.join(outdir, 'cov'), exist_ok=True)
        p = subprocess.run(PRE + [binpath(ver), wf, sf, '-v'], capture_output=True, text=True, env=e2)
        open(os.path.join(raw, f'{ver}-case{c["id"]}.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
        r = parse(p.stdout).get(str(c['id'])) or {'same': False, 'interp': None, 'native': None}
        r['rc'] = p.returncode; out[ver] = r
    os.remove(wf); os.remove(sf)
    return c['id'], out
VERS = os.environ.get('HX28_VERS', '0.16.5 0.16.7').split()
t0 = time.time(); res = {v: {} for v in VERS}
if shared:
    world = list(base)
    for c in cases: world += wlines(c)
    wf = os.path.join(tmp, 'w-shared.txt'); open(wf, 'w').write('\n'.join(dict.fromkeys(world)) + '\n')
    sf = os.path.join(tmp, 's-shared.txt'); open(sf, 'w').write(''.join(scen(c) for c in cases))
    for ver in res:
        p = subprocess.run(PRE + [binpath(ver), wf, sf, '-v'], capture_output=True, text=True, env=env)
        open(os.path.join(raw, f'{ver}-shared.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
        res[ver] = parse(p.stdout)
else:
    with ThreadPoolExecutor(4) as ex:
        for cid, out in ex.map(one, cases):
            for v in out: res[v][str(cid)] = out[v]
json.dump({'binaries': {v: binpath(v) for v in res}, 'env': {k: v for k, v in env.items() if k.startswith('MALLOC')},
           'shared': shared, 'seconds': round(time.time() - t0), 'results': res}, open(os.path.join(outdir, 'hx-results.json'), 'w'))
for ver in res: print(ver, 'scenarios', len(res[ver]), 'engine DIFF', sorted(int(k) for k, x in res[ver].items() if not x['same']))
