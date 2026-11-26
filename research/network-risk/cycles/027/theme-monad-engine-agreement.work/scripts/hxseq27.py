"""Cycle 27: rerun the cycle 26 long sequences (cycles/026/theme-stateful-interpreter.work, seqlib.py, salt of
build/salt.json) through the fixed harness build/<ver>/hxf and, with --old, the cycle 23 hx binaries. World and scenario
lines as in that unit's scripts/hxrun.py. Reference: pyevm.py (tools/opdiff) through the same World construction.
HX_FWD=1 places the token double behind DELEGATECALL forwarders (the eth_call layout), which the old harness ran wrongly.
Usage: python3 -I hxseq27.py <outdir> [--old] [names...]"""
import sys, os, json, subprocess, re
W27 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S26 = os.path.abspath(os.path.join(W27, '..', '..', '026', 'theme-stateful-interpreter.work', 'scripts'))
sys.path.insert(0, S26)
import seqlib as S
import pyevm as P
args = sys.argv[1:]; outdir = args[0]; old = '--old' in args
names = [a for a in args[1:] if not a.startswith('--')] or ['a64', 'a512', 'b', 'c', 'c2', 'd40', 'd300']
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
SEQ = S.sequences(salt)
direct = os.environ.get('HX_FWD') != '1'
HXOLD = os.path.join(S.NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
def binpath(ver): return os.path.join(HXOLD, f'{ver}-plain', 'hx') if old else os.path.join(W27, 'build', ver, 'hxf')
os.makedirs(outdir, exist_ok=True); res = {'salt': salt, 'direct': direct, 'old': old, 'seq': {}}
for nm in names:
    codes = S.codes(PM, direct=direct)
    world = [f'code {a:040x} {c.hex()}' for a, c in codes.items()]
    wf = os.path.join(outdir, f'w-{nm}.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(outdir, f's-{nm}.txt'); open(sf, 'w').write(f'SCEN {nm}\nTX {S.EOA:040x} {S.D:040x} 00 400000000 {S.enc_run(SEQ[nm]).hex()}\n')
    wd = P.World(S.codes(PM, direct=direct)); ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(SEQ[nm]), False, 0); ref = S.dec_run(ret) if ok else None
    res['seq'][nm] = {'refOk': ok}
    for ver in ('0.16.5', '0.16.7'):
        p = subprocess.run([binpath(ver), wf, sf, '-v'], capture_output=True, text=True)
        open(os.path.join(outdir, f'out-{nm}-{ver}.txt'), 'w').write(p.stdout + '\n--stderr--\n' + p.stderr[:20000])
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        dec = []
        for st, g, o in outs:
            try: dec.append({'status': st, 'gas': int(g), 'steps': S.dec_run(bytes.fromhex(o))})
            except Exception: dec.append({'status': st, 'gas': int(g), 'raw': o[:400]})  # noqa
        r = {'sameEngines': p.stdout.startswith('SAME'), 'rc': p.returncode, 'engines': len(dec),
             'interpEqRef': bool(dec) and ref is not None and dec[0].get('steps') == ref,
             'nativeEqRef': len(dec) > 1 and ref is not None and dec[1].get('steps') == ref,
             'gas': [d['gas'] for d in dec], 'nsteps': [len(d.get('steps') or []) for d in dec], 'refSteps': len(ref or [])}
        res['seq'][nm][ver] = r
        print(nm, ver, r, flush=True)
    os.remove(wf)
json.dump(res, open(os.path.join(outdir, 'hx-results.json'), 'w'), indent=1)
