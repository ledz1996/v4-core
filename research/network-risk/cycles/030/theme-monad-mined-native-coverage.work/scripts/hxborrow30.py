"""Cycle 30, lead L-1172: the three getFeeGrowthInside borrow scripts of cycles/028/hyperevm.work/scripts/borrow.py
(Pool.sol:499-500, 502-503, 505-508, with Position.update at Position.sol:91-96 on the poke and the removal), run with the
PoolManager bytecode deployed on Monad (PM_FROM=143) in the reference interpreter (pyevm) and in both engines
(interpreter and native code from the clang build of the emitter) of the cycle 27/28 harness rebuilt in this work dir
(build/<ver>/hxf, scripts/build.sh). World: the pmdiff6 codes, balances and the one storage word of pmdiff6.world.
Usage: python3 -I hxborrow30.py <outdir>"""
import sys, os, json, hashlib, subprocess, re
os.environ['PM_FROM'] = '143'
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/hyperevm.work/scripts')
import borrow as BR
D = BR.D; P = BR.P
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EOA = 0xE0A0000000000000000000000000000000000E0A
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
code = P.fetch_code()
res = {'codeSha256': hashlib.sha256(code).hexdigest(), 'caller': hex(EOA), 'scripts': {}}
for i, (name, data) in enumerate(BR.scripts.items()):
    wd = D.world(code); wd.max_steps = 40_000_000
    ok, ret = wd.call(EOA, D.DRV, 0, data, False, 0)
    rec = D.P.parse(D.unwrap(ret)); ref = hashlib.sha256(ret).hexdigest()
    world = [f'code {a:040x} {c.hex()}' for a, c in wd.codes.items()]
    world += [f'bal {a:040x} {v:064x}' for a, v in D.BAL.items()]
    world += [f'st {D.PMI:040x} {0:064x} {D.DRV:064x}']
    wf = os.path.join(out, f'w{i}.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(out, f's{i}.txt'); open(sf, 'w').write(f'SCEN b{i}\nTX {EOA:040x} {D.DRV:040x} 00 150000000 {data.hex()}\n')
    r = {'refOk': ok, 'refHash': ref, 'refCalls': len(rec), 'refFailed': [j for j, (k, _) in enumerate(rec) if not k],
         'refWordsTail': [x.hex() for k, x in rec[-12:]]}
    for ver in ('0.16.5', '0.16.7'):
        b = os.path.join(W, 'build', ver, 'hxf')
        p = subprocess.run([b, wf, sf, '-v'], capture_output=True, text=True)
        open(os.path.join(out, f'out-b{i}-{ver}.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        r[ver] = {'rc': p.returncode, 'same': p.stdout.startswith('SAME'), 'binSha256': hashlib.sha256(open(b, 'rb').read()).hexdigest(),
                  'engines': [{'status': s, 'gasleft': int(g), 'eqRef': hashlib.sha256(bytes.fromhex(o)).hexdigest() == ref} for s, g, o in outs]}
    res['scripts'][name] = r
    print(name, json.dumps({k: v for k, v in r.items() if k != 'refWordsTail'}), flush=True)
json.dump(res, open(os.path.join(out, 'hxborrow.json'), 'w'), indent=1)
