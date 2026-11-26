"""Cycle 24 copy of cycles/021/established-l1.work/run_eps.py. Run one opdiff tool against this unit's endpoints (Polygon, BNB Chain, Avalanche) only.
EP_FILTER=<substr,...> narrows the endpoint list; WITH_ETH=1 adds the Ethereum reference from networks.json (ETH_URL replaces its URL).
Usage: python3 run_eps.py <tool.py> <args...>"""
import sys, os, runpy
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
EP = [
    (137, 'Polygon publicnode bor', 'https://polygon-bor-rpc.publicnode.com'),
    (137, 'Polygon quiknode bor', 'https://rpc-mainnet.matic.quiknode.pro'),
    (56, 'BSC dataseed1', 'https://bsc-dataseed1.bnbchain.org'),
    (56, 'BSC 48club', 'https://rpc-bsc.48.club'),
    (43114, 'Avalanche api.avax', 'https://api.avax.network/ext/bc/C/rpc'),
]
sel = os.environ.get('EP_FILTER')
if sel: EP = [e for e in EP if any(x in e[1] for x in sel.split(','))]
_all = evm.networks()
want_eth = os.environ.get('WITH_ETH')
ETH_URL = os.environ.get('ETH_URL')
_eth = [(c, nm, ETH_URL or u) for c, nm, u in _all if c == 1]
evm.networks = lambda path=None: (_eth if want_eth else []) + list(EP)
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
