"""Run an opdiff script against selected Ethereum mainnet endpoints, with every eth_call
bracketed by web3_clientVersion before and after (backend pinning).
Usage: python3 altrun.py <pinlog.json> <ids comma list> <script.py> <args...>
Pseudo chain ids name the endpoints. Read-only: eth_call with state override only."""
import sys, os, runpy, json, threading
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
ALT = [(1, 'Ethereum reth v2.11.0 (publicnode)', 'https://ethereum-rpc.publicnode.com'),
       (1011, 'Ethereum geth v1.17.9 go1.27.2 (blockpi)', 'https://ethereum.public.blockpi.network/v1/rpc/public'),
       (1012, 'Ethereum geth v1.17.5 go1.25.12 (blockrazor)', 'https://eth.blockrazor.xyz'),
       (1016, 'Ethereum geth v1.17.10 go1.27.3 (nownodes)', 'https://public-eth.nownodes.io'),
       (1017, 'Ethereum geth v1.16.7 go1.25.14 (bloxroute)', 'https://eth.rpc.blxrbdn.com'),
       (1018, 'Ethereum reth v2.6.0 (flashbots)', 'https://rpc.flashbots.net'),
       (1019, 'Ethereum reth v2.10.0 (stakely)', 'https://ethereum-json-rpc.stakely.io')]
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
        d = LOG.setdefault(url, {'calls': 0, 'pinned': 0, 'versions': {}})
        d['calls'] += 1; d['pinned'] += int(before == after)
        for v in (before, after): d['versions'][v] = d['versions'].get(v, 0) + 1
    return res


evm.rpc = pinned_rpc
script = sys.argv[3]; sys.argv = [script] + sys.argv[4:]
try:
    runpy.run_path(os.path.join(OPD, script), run_name='__main__')
finally:
    json.dump(LOG, open(pinlog, 'w'), indent=1)
    print(json.dumps(LOG, indent=1))
