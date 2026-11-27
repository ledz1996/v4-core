"""Task 3: run pmdiff.py (250 scripts), pmdiff2.py (300 scripts) and the borrow scripts of cycle 32 established-l1
(cycles/032/established-l1.work/borrow.py) against one endpoint, bracketed by web3_clientVersion (and arc_getVersion on
Arc) before and after each, so each result is tied to the build that answered. Read-only.
usage: python3 -I pinned.py <outdir> <tag> <chainId> <url>"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rpcu import version
outdir, tag, chain, url = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
RU = '/home/user/v4-core/research/network-risk/cycles/032/established-l1.work/run_url.py'
BR = '/home/user/v4-core/research/network-risk/cycles/032/established-l1.work/borrow.py'
env = dict(os.environ, RPC_URL=url, RPC_CHAIN=str(chain), PM_FROM=str(chain))
rec = {'url': url, 'chain': chain, 'runs': {}}
for name, cmd in (('pmdiff', ['python3', RU, 'pmdiff.py', f'{outdir}/pm1_{tag}.json', '250', str(chain)]),
                  ('pmdiff2', ['python3', RU, 'pmdiff2.py', f'{outdir}/pm2_{tag}.json', '300', str(chain)]),
                  ('borrow', ['python3', BR, f'{outdir}/borrow_{tag}.json', url])):
    b = version(url, chain)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=7000)
    a = version(url, chain)
    rec['runs'][name] = {'before': b, 'after': a, 'stdoutTail': p.stdout[-1500:], 'stderrTail': p.stderr[-800:], 'rc': p.returncode}
    print(tag, name, p.returncode, p.stdout[-400:].replace('\n', ' | '), p.stderr[-200:])
json.dump(rec, open(f'{outdir}/pinned_{tag}.json', 'w'), indent=1)
