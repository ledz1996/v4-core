"""Run one opdiff tool against this unit's endpoints. Usage: python3 run_tool.py <tool.py> <args...>
The endpoint list replaces evm.networks() so several clients per chain can be tested."""
import sys, os, runpy
T = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, T)
import evm
EP = [
    (137, 'Polygon bor-publicnode v2.11.1-private a863b8e5cce1', 'https://polygon-bor-rpc.publicnode.com'),
    (137, 'Polygon bor-onfinality v2.11.2', 'https://polygon.api.onfinality.io/public'),
    (137, 'Polygon bor-quiknode v2.11.1', 'https://rpc-mainnet.matic.quiknode.pro'),
    (137, 'Polygon bor-1rpc v2.11.0', 'https://1rpc.io/matic'),
    (56, 'BSC geth v1.8.2-4e1c8247 dataseed1', 'https://bsc-dataseed1.bnbchain.org'),
    (56, 'BSC reth-bsc v0.1.4-hotfix-23b510f', 'https://bsc-rpc.publicnode.com'),
    (43114, 'Avalanche avalanchego 1.15.3 api', 'https://api.avax.network/ext/bc/C/rpc'),
    (43114, 'Avalanche avalanchego 1.15.3 publicnode', 'https://avalanche-c-chain-rpc.publicnode.com'),
]
sel = os.environ.get('EP_FILTER')
if sel:
    EP = [e for e in EP if sel in e[1]]
ex = os.environ.get('EP_EXCLUDE')
if ex:
    EP = [e for e in EP if ex not in e[1]]
if os.environ.get('PSEUDO'):
    import json as _j
    _eth=[n for n in _j.load(open(os.path.join(T,'..','..','state','networks.json')))['networks'] if n['chainId']==1][0]
    EP = [(1,'Ethereum',_eth['rpc'])] + [(c*1000+i, nm, u) for i,(c,nm,u) in enumerate(EP)]
    print('endpoints', EP, flush=True)
evm.networks = lambda path=None: list(EP)
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(os.path.join(T, tool), run_name='__main__')
