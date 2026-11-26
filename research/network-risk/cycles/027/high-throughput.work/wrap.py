"""Run an opdiff script with the Ethereum reference read from https://ethereum.publicnode.com.
The endpoint in networks.json (ethereum-rpc.publicnode.com) answers HTTP 403 to Python's urllib on 2026-11-26.
Usage: python3 wrap.py <script.py> <args...>   (run from tools/opdiff)"""
import sys, runpy, os
sys.path.insert(0, os.getcwd())
import evm
ALT = 'https://ethereum.publicnode.com'
_net = evm.networks
def networks(*a, **k):
    return [(c, n, ALT if c == 1 else u) for (c, n, u) in _net(*a, **k)]
evm.networks = networks
import pmdiff
pmdiff.ETH = ALT
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
