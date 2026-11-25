"""Run an opdiff tool with chain endpoints replaced. Usage: ALT='137=https://...' python3 run_alt.py <tool.py> <args...>
Ethereum (chain 1) stays on its networks.json endpoint because pmdiff compares against it."""
import sys, os, runpy, json
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
orig = evm.networks()
alt = dict(kv.split('=', 1) for kv in os.environ.get('ALT', '').split(',') if kv)
EP = [(c, n + (' alt' if str(c) in alt else ''), alt.get(str(c), u)) for c, n, u in orig]
evm.networks = lambda path=None: list(EP)
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
