"""Run a tools/opdiff script against another endpoint for one chain id. Read-only.
Usage: RPC_URL=https://avax.api.pocket.network RPC_CHAIN=43114 python3 run_url.py <script.py> <args...>
evm.networks is replaced before the script imports it, so the named chain uses RPC_URL.
"""
import os, sys, runpy
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../tools/opdiff'))
sys.path.insert(0, TOOLS)
import evm  # noqa: E402

_orig = evm.networks
URL, CID = os.environ['RPC_URL'], int(os.environ['RPC_CHAIN'])


def networks(*a, **k):
    return [(c, n + ' @' + URL, URL if c == CID else u) for c, n, u in _orig(*a, **k)]


evm.networks = networks
script = os.path.join(TOOLS, sys.argv[1])
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name='__main__')
