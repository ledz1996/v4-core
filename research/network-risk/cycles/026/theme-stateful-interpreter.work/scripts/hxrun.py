"""Run each sequence through Monad's interpreter and Monad's native x86 code with the cycle 23 harness (hx) built from
v0.16.5 and v0.16.7. One world per sequence with the codes of seqlib.codes (the build at Monad's PoolManager address,
the driver, both hook doubles, the token double and forwarders), one transaction EOA -> driver run(steps). The harness
compares the two engines on trace, storage, transient storage, balances and logs; this script also decodes each engine's
returned words and compares them with the reference interpreter (out/refcache.json via compare.ref).
Usage: python3 -I hxrun.py <out.json> [names...]"""
import sys, os, json, subprocess, re, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
HX = os.path.join(S.NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
SEQ = S.sequences(salt)
names = sys.argv[2:] or ['a64', 'a512', 'b', 'c', 'c2', 'd300']  # e needs CREATE2, which the harness does not implement
tmp = os.path.join(S.WORK, 'out', 'hx'); os.makedirs(tmp, exist_ok=True)
import pyevm as P
res = {}
for nm in names:
    world = [f'code {a:040x} {c.hex()}' for a, c in S.codes(PM, direct=os.environ.get('HX_FWD') != '1').items()]
    wf = os.path.join(tmp, f'w-{nm}.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(tmp, f's-{nm}.txt'); open(sf, 'w').write(f'SCEN {nm}\nTX {S.EOA:040x} {S.D:040x} 00 400000000 {S.enc_run(SEQ[nm]).hex()}\n')
    ref = None
    if nm != 'e':
        wd = P.World(S.codes(PM, direct=os.environ.get('HX_FWD') != '1')); ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(SEQ[nm]), False, 0); ref = S.dec_run(ret) if ok else None
    res[nm] = {}
    for ver in ('0.16.5', '0.16.7'):
        p = subprocess.run([os.path.join(HX, f'{ver}-plain', 'hx'), wf, sf, '-v'], capture_output=True, text=True)
        open(os.path.join(tmp, f'out-{nm}-{ver}.txt'), 'w').write(p.stdout[:200000] + '\n--stderr--\n' + p.stderr[:20000])
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        dec = []
        for st, g, o in outs:
            try:
                dec.append({'status': st, 'steps': S.dec_run(bytes.fromhex(o))})
            except Exception:  # noqa
                dec.append({'status': st, 'raw': o[:400]})
        r = {'sameEngines': p.stdout.startswith('SAME'), 'rc': p.returncode, 'engines': len(dec)}
        if ref is not None:
            r['interpEqRef'] = bool(dec) and dec[0].get('steps') == ref
            r['nativeEqRef'] = len(dec) > 1 and dec[1].get('steps') == ref
        else:
            r['steps'] = [d.get('steps') for d in dec]
        res[nm][ver] = r
        print(nm, ver, r if nm != 'e' else {k: v for k, v in r.items() if k != 'steps'}, flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
