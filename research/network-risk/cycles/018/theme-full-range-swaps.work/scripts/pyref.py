"""Reference interpreter (tools/opdiff/pyevm.py, no gas) on the 16 full-range scripts; hash compared with the full
Ethereum answer (reth v2.10.0 at eth-mainnet.public.blastapi.io, 500M gas). Usage: python3 pyref.py <out.json>"""
import sys, os, json, hashlib, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
import pmdiff as P, pmdiff2 as Q  # noqa
from pyevm import World  # noqa
code = bytes.fromhex(open(os.path.join(HERE, '..', 'raw', 'pm-fresh-code.hex')).read())
pm, drv = int(P.PM, 16), int(P.DRV, 16)
rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(250)]
rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(300)]
ref = {s: json.load(open(os.path.join(HERE, '..', 'raw', f'eth-blast-s{s}.json')))['scripts'] for s in ('1', '2')}
out = {}
for s, idx in (('1', [41, 76, 86, 147, 151, 177, 233, 67]), ('2', [22, 189, 196, 210, 213, 227, 295, 297])):
    for i in idx:
        t0 = time.time()
        if s == '1': wd = World({pm: code, drv: P.driver()}); data = s1[i][0]
        else:
            codes = {pm: code, drv: Q.driver(), Q.TOKEN: Q.token()}
            for f in Q.HOOK_FLAGS: codes[Q.HOOK_BASE | f] = Q.hook()
            wd = World(codes, {pm: 10 ** 19}); data = s2[i][0]
        wd.max_steps = 2_000_000_000
        ok, ret = wd.call(0, drv, 0, data, False, 0)
        h = hashlib.sha256(ret).hexdigest()
        out[f'{s}-{i}'] = {'hash': h, 'equalsEthFull': h == ref[s][str(i)]['plainHash'], 'steps': wd.steps, 'seconds': round(time.time() - t0)}
        print(s, i, out[f'{s}-{i}'], flush=True)
        json.dump(out, open(sys.argv[1], 'w'), indent=1)
