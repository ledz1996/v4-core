"""Cycle 39: run one tools/opdiff script with extra networks next to Ethereum (chain 1 stays the reference).
Used to run the battery and the PoolManager script sets on Ethereum Sepolia, which runs the Amsterdam (Glamsterdam)
rules since 2026-10-06 (EIP-7773 table; eth_config on ethereum-sepolia-rpc.publicnode.com), as a rehearsal of the
fork that mainnet has not scheduled. Nothing is sent; every call is eth_call with state override.
usage: EXTRA='11155111|Sepolia|https://...' python3 withnets.py <tool.py> <tool args...>"""
import os, runpy, sys
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
import evm
_orig = evm.networks
EXTRA = [tuple(x.split('|')) for x in os.environ.get('EXTRA', '').split(',') if x]
EXTRA = [(int(c), n, u) for c, n, u in EXTRA]


def networks(*a, **k):
    base = [n for n in _orig(*a, **k) if n[0] == 1]
    return base + EXTRA


evm.networks = networks
tool = os.path.join(TOOLS, sys.argv[1])
sys.argv = [tool] + sys.argv[2:]
runpy.run_path(tool, run_name='__main__')
