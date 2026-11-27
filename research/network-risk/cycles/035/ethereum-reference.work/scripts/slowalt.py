"""Cycle 35 ethereum-reference. Same as cycle 33's pmalt.py (reference: chain 1 endpoint of networks.json; extra endpoints
under made-up ids 9000xx), with a pause before every JSON-RPC request and six retries, for endpoints that answer 429.
Read-only (eth_call with state overrides).
Usage: SLOW=<seconds> python3 slowalt.py pmdiff|pmdiff2|single <out.json> <n scripts or 0> <url> [<url> ...]"""
import sys, os, time, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
pause = float(os.environ.get('SLOW', '1.0'))
_rpc = evm.rpc
def slow_rpc(url, method, params, timeout=90):
    last = None
    for k in range(6):
        time.sleep(pause)
        try:
            return _rpc(url, method, params, timeout)
        except Exception as e:
            last = e
            if '429' not in str(e) and 'Too Many' not in str(e): raise
            time.sleep(5 * (k + 1))
    raise last
evm.rpc = slow_rpc
which, out, n, urls = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
if which == 'single':
    sys.argv = ['single.py', out, urls[0]]
    runpy.run_path('/home/user/v4-core/research/network-risk/cycles/033/ethereum-reference.work/scripts/single.py', run_name='__main__')
else:
    base = [x for x in evm.networks() if x[0] == 1]
    extra = [(900000 + i, u.split('/')[2][:16], u) for i, u in enumerate(urls)]
    evm.networks = lambda *a, **k: base + extra
    sys.argv = [which + '.py', out, n]
    runpy.run_path('/home/user/v4-core/research/network-risk/tools/opdiff/' + which + '.py', run_name='__main__')
