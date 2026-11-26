"""Run one opdiff tool against a chosen endpoint for chain 999 only.
Usage: python3 run_on.py <rpc url> <label> <tool.py> <tool args...>
Patches evm.networks so chain 999 is reached at the given URL; Ethereum stays as the reference."""
import sys, os, runpy
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, TOOLS)
import evm
url, label, tool = sys.argv[1], sys.argv[2], sys.argv[3]
_orig = evm.networks
evm.networks = lambda path=None: [(c, n, u) if c != 999 else (999, label, url) for c, n, u in _orig()]
sys.argv = [os.path.join(TOOLS, tool)] + sys.argv[4:]
runpy.run_path(os.path.join(TOOLS, tool), run_name='__main__')
