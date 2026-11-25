"""Run one opdiff tool against second endpoints of this unit. Usage: python3 run_tool.py <tool.py> <args...>"""
import sys, os, runpy
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
EP = [
    (137, 'Polygon bor-onfinality v2.11.2', 'https://polygon.api.onfinality.io/public'),
    (137, 'Polygon bor-quiknode v2.11.1', 'https://rpc-mainnet.matic.quiknode.pro'),
    (56, 'BSC reth-bsc v0.1.4-hotfix-23b510f', 'https://bsc-rpc.publicnode.com'),
    (56, 'BSC geth v1.8.2-4e1c8247 dataseed2', 'https://bsc-dataseed2.bnbchain.org'),
    (43114, 'Avalanche avalanchego 1.15.3 publicnode', 'https://avalanche-c-chain-rpc.publicnode.com'),
]
sel = os.environ.get('EP_FILTER')
if sel: EP = [e for e in EP if any(x in e[1] for x in sel.split(','))]
evm.networks = lambda path=None: list(EP)
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
