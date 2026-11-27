"""Cycle 29 stablecoin-l1: run tools/opdiff/pmdiff.py or pmdiff2.py unchanged against Arc endpoints that
state/networks.json does not list, by replacing evm.networks() with Ethereum (the reference) plus the given URLs under
pseudo chain ids 50421, 50422, ... Read-only.
Usage: python3 pm_urls.py pmdiff|pmdiff2 <out.json> <n_scripts> <url> [<url> ...]"""
import sys, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm  # noqa: E402

which, out, n = sys.argv[1], sys.argv[2], sys.argv[3]
urls = sys.argv[4:]
eth = [x for x in evm.networks() if x[0] == 1]
extra = [(50421 + i, 'Arc@' + u.split('//')[1].split('/')[0][:12], u) for i, u in enumerate(urls)]
evm.networks = lambda *a, **k: eth + extra
sys.argv = [which + '.py', out, n] + [str(c) for c, _, _ in extra]
runpy.run_path('/home/user/v4-core/research/network-risk/tools/opdiff/%s.py' % which, run_name='__main__')
