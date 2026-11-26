"""Cycle 27: rerun cycle 26 hook and native cases (cases.json of theme-hook-and-native-sides) through the fixed harness
build/<ver>/hxf (and, with --old, the cycle 23 hx binaries for control). Same world and scenario construction as
cycles/026/theme-hook-and-native-sides.work/scripts/hxrun26.py. Raw harness stdout of every case is kept.
Usage: python3 hxrun27.py <cases.json> <outdir> [--old] [--env K=V ...] [--ids 1,2,3]"""
import sys, os, json, subprocess, time, re
from concurrent.futures import ThreadPoolExecutor
W27 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S26 = os.path.join(W27, '..', '..', '026', 'theme-hook-and-native-sides.work', 'scripts')
sys.path.insert(0, os.path.abspath(S26))
from common26 import *  # noqa
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
hb = json.load(open(os.path.join(WORK, 'build', 'driver-hx.json')))
drv = bytes.fromhex(hb['driver']).replace(PLACEHOLDER, PM.to_bytes(20, 'big'))
args = sys.argv[1:]
cases = json.load(open(args[0]))['cases']; outdir = args[1]
old = '--old' in args
env = dict(os.environ)
for i, a in enumerate(args):
    if a == '--env': k, v = args[i + 1].split('=', 1); env[k] = v
    if a == '--ids': ids = set(int(x) for x in args[i + 1].split(',')); cases = [c for c in cases if c['id'] in ids]
HXOLD = os.path.join(NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
COV = '--cov' in args  # fixed harness linked with the cycle 23 coverage-patched emitter; HX_COVOUT per case
def binpath(ver): return os.path.join(HXOLD, f'{ver}-plain', 'hx') if old else os.path.join(W27, 'build', ver, 'hxfcov' if COV else 'hxf')
tmp = os.path.join(outdir, 'tmp'); raw = os.path.join(outdir, 'raw'); os.makedirs(tmp, exist_ok=True); os.makedirs(raw, exist_ok=True)
def files(c):
    codes = codes_for(PM, [c]); codes[D] = drv; codes[S] = drv
    toks = [t for t in (c.get('t0'), c.get('t1')) if t]
    for t in toks: codes.pop(t, None)
    codes.pop(IMPL, None)
    world = [f'code {a:040x} {code.hex()}' for a, code in codes.items()]
    for t in toks: world += [f'token {t:040x}', f'tok {t:040x} {D:040x} {(1 << 250):x}']
    world += [f'bal {a:040x} {v:064x}' for a, v in balances_for(PM).items()]
    wf = os.path.join(tmp, f'w{c["id"]}.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(tmp, f's{c["id"]}.txt'); open(sf, 'w').write(f'SCEN case{c["id"]}\nTX {EOA:040x} {D:040x} 00 150000000 {enc_run([c], PM).hex()}\n')
    return wf, sf
def dec(o):
    try:
        r = dec_run(bytes.fromhex(o))[0]
        return {'ok': r[0], 'w': [hex(x) for x in r[1]] if r[1] else None, 'revert': r[2].hex()}
    except Exception:  # noqa
        return {'raw': o[:200]}
PRE = os.environ.get('HX27_PRE', '').split()
def one(c):
    wf, sf = files(c); out = {}
    for ver in ('0.16.5', '0.16.7'):
        e2 = dict(env, HX_COVOUT=os.path.join(outdir, 'cov', f'{ver}-case{c["id"]}.cov')) if COV else env
        if COV: os.makedirs(os.path.join(outdir, 'cov'), exist_ok=True)
        p = subprocess.run(PRE + [binpath(ver), wf, sf, '-v'], capture_output=True, text=True, env=e2)
        open(os.path.join(raw, f'{ver}-case{c["id"]}.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        d = [dict(status=s, gas=int(g), **dec(o)) for s, g, o in outs]
        out[ver] = {'same': p.stdout.startswith('SAME'), 'interp': d[0] if d else None, 'native': d[1] if len(d) > 1 else None, 'rc': p.returncode}
    if not os.environ.get('HX27_KEEP'): os.remove(wf); os.remove(sf)
    return c['id'], out
t0 = time.time(); res = {'0.16.5': {}, '0.16.7': {}}
with ThreadPoolExecutor(4) as ex:
    for cid, out in ex.map(one, cases):
        for v in out: res[v][str(cid)] = out[v]
json.dump({'binaries': {v: binpath(v) for v in res}, 'env': {k: v for k, v in env.items() if k.startswith('MALLOC') or k.startswith('HX')},
           'seconds': round(time.time() - t0), 'results': res}, open(os.path.join(outdir, 'hx-results.json'), 'w'))
for ver in res: print(ver, 'scenarios', len(res[ver]), 'engine DIFF', sorted(int(k) for k, x in res[ver].items() if not x['same']))
