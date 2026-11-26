"""Run an opdiff script against selected Ethereum mainnet endpoints, every eth_call
bracketed by web3_clientVersion before and after. Records each (before, after) pair.
Usage: python3 altrun.py <pinlog.json> <ids comma list> <script.py> <args...>
Read-only: eth_call with state override only."""
import sys, os, runpy, json, threading
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
ALT = [(1, 'Ethereum reth v2.11.0 (publicnode)', 'https://ethereum-rpc.publicnode.com'),
       (1016, 'Ethereum geth v1.17.10 go1.27.3 (nownodes)', 'https://public-eth.nownodes.io'),
       (1020, 'Ethereum pocket mix (reth 2.10.1, reth 2.11.0, geth 1.17.9 go1.25.14, erigon 3.8.1)', 'https://eth.api.pocket.network')]
pinlog = sys.argv[1]; ids = set(map(int, sys.argv[2].split(',')))
ALT = [a for a in ALT if a[0] in ids]
evm.networks = lambda *a, **k: ALT
_orig = evm.rpc
LOG = {}; LOCK = threading.Lock()


def pinned_rpc(url, method, params, timeout=60):
    if method != 'eth_call':
        return _orig(url, method, params, timeout)
    try: before = _orig(url, 'web3_clientVersion', [], 20)
    except Exception as e: before = 'ERR ' + str(e)[:60]
    res = _orig(url, method, params, timeout)
    try: after = _orig(url, 'web3_clientVersion', [], 20)
    except Exception as e: after = 'ERR ' + str(e)[:60]
    with LOCK:
        d = LOG.setdefault(url, {'calls': 0, 'pinned': 0, 'versions': {}, 'pinnedBy': {}})
        d['calls'] += 1
        if before == after:
            d['pinned'] += 1; d['pinnedBy'][before] = d['pinnedBy'].get(before, 0) + 1
        for v in (before, after): d['versions'][v] = d['versions'].get(v, 0) + 1
    return res


evm.rpc = pinned_rpc
script = sys.argv[3]; sys.argv = [script] + sys.argv[4:]
try:
    runpy.run_path(os.path.join(OPD, script), run_name='__main__')
finally:
    json.dump(LOG, open(pinlog, 'w'), indent=1)
    print(json.dumps(LOG, indent=1))
