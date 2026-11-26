"""Run cases through Monad's interpreter and native x86 code with the cycle 23 harness (hx) at v0.16.5 and v0.16.7, one
world and one scenario per case. The world holds the codes of common26.codes_for with the driver of src/Driver26Hx.sol
and the harness's own tokens in place of the token doubles (the driver holds 2^250 of each) and the native balances of common26.balances_for. Usage: python3 hxrun26.py <cases.json> <outdir>"""
import sys, os, json, subprocess, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import *  # noqa
HX = os.path.join(NR, 'cycles', '023', 'theme-monad-compiled-coverage.work', 'build')
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
hb = json.load(open(os.path.join(WORK, 'build', 'driver-hx.json')))
drv = bytes.fromhex(hb['driver']).replace(PLACEHOLDER, PM.to_bytes(20, 'big'))
cases = json.load(open(sys.argv[1]))['cases']; outdir = sys.argv[2]
tmp = os.path.join(outdir, 'hx', 'tmp'); os.makedirs(tmp, exist_ok=True)
res = {'0.16.5': {}, '0.16.7': {}}; t0 = time.time()
for c in cases:
    codes = codes_for(PM, [c]); codes[D] = drv; codes[S] = drv
    toks = [t for t in (c.get('t0'), c.get('t1')) if t]
    for t in toks: codes.pop(t, None)
    codes.pop(IMPL, None)
    world = [f'code {a:040x} {code.hex()}' for a, code in codes.items()]
    for t in toks: world += [f'token {t:040x}', f'tok {t:040x} {D:040x} {(1 << 250):x}']
    world += [f'bal {a:040x} {v:064x}' for a, v in balances_for(PM).items()]
    wf = os.path.join(tmp, 'w.txt'); open(wf, 'w').write('\n'.join(world) + '\n')
    sf = os.path.join(tmp, 's.txt'); open(sf, 'w').write(f'SCEN case{c["id"]}\nTX {EOA:040x} {D:040x} 00 150000000 {enc_run([c], PM).hex()}\n')
    for ver in res:
        p = subprocess.run([(os.environ['HX_BIN'] if os.environ.get('HX_BIN') and ver == '0.16.7' else os.path.join(HX, f'{ver}-plain', 'hx')), wf, sf, '-v'], capture_output=True, text=True)
        outs = re.findall(r'tx 0 status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', p.stdout)
        dec = []
        for st, g, o in outs:
            try:
                r = dec_run(bytes.fromhex(o))[0]
                dec.append({'status': st, 'gas': int(g), 'ok': r[0], 'w': [hex(x) for x in r[1]] if r[1] else None, 'revert': r[2].hex()})
            except Exception:  # noqa
                dec.append({'status': st, 'gas': int(g), 'raw': o[:200]})
        res[ver][str(c['id'])] = {'same': p.stdout.startswith('SAME'), 'interp': dec[0] if dec else None,
                                  'native': dec[1] if len(dec) > 1 else None, 'rc': p.returncode, 'head': p.stdout[:300] if not dec else ''}
    if c['id'] % 100 == 0: print(c['id'], round(time.time() - t0), flush=True)
json.dump(res, open(os.path.join(outdir, 'hx-results.json'), 'w'))
for ver in res: print(ver, 'scenarios', len(res[ver]), 'engine DIFF', sum(1 for x in res[ver].values() if not x['same']))
