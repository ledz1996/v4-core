"""Run one opdiff tool on BNB Smart Chain endpoints under the Jenner rules, by adding a block
override with time 1796697600 (2026-12-08 02:40 UTC, ten minutes after JennerTime 1796697000)
to every eth_call sent to a BSC endpoint. The Ethereum reference is called unchanged.
Check that the rules switch: eth_call to 0x70 returns the millisecond time only under the override.
Usage: python3 run_jenner.py <tool.py> <args...>"""
import sys, os, runpy
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
JT = hex(1796697600)
EP = [
    (56, 'BSC dataseed1 v1.8.2-4e1c8247 Jenner', 'https://bsc-dataseed1.bnbchain.org'),
    (56, 'BSC 48club v1.8.2 Jenner', 'https://rpc-bsc.48.club'),
    (56, 'BSC reth-bsc v0.1.4 Jenner', 'https://bsc-rpc.publicnode.com'),
]
BSC = {e[2] for e in EP}
sel = os.environ.get('EP_FILTER')
if sel: EP = [e for e in EP if any(x in e[1] for x in sel.split(','))]
_all = evm.networks()
want_eth = os.environ.get('WITH_ETH')
evm.networks = lambda path=None: ([n for n in _all if n[0] == 1] if want_eth else []) + list(EP)
orig = evm.rpc
def rpc(url, method, params, timeout=60):
    if url in BSC and method == 'eth_call':
        p = list(params)
        while len(p) < 3:
            p.append('latest' if len(p) == 1 else {})
        p = p[:3] + [{'time': JT}]
        return orig(url, method, p, timeout)
    return orig(url, method, params, timeout)
evm.rpc = rpc
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
