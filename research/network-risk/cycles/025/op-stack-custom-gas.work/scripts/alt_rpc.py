"""Run one opdiff tool with chain 42220 pointed at another public Celo endpoint. Read-only.
Usage: python3 alt_rpc.py <url> <tool.py> [tool args ...]"""
import sys, os, runpy
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, TOOLS)
import evm
URL = sys.argv[1]; _n = evm.networks
evm.networks = lambda *a, **k: [(c, n + ' alt', URL if c == 42220 else u) for (c, n, u) in _n(*a, **k)]
tool = sys.argv[2]; sys.argv = [tool] + sys.argv[3:]
os.chdir(TOOLS)
runpy.run_path(os.path.join(TOOLS, tool), run_name='__main__')
