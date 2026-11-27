"""Run one tools/opdiff script for BNB Chain (56) with every eth_call carrying the block
override time = 1,796,697,100 (100 s after Jenner) and the endpoint given in JEN_RPC.
The Ethereum reference calls (other urls) are left as they are. Read-only.
Usage: JEN_RPC=<url> python3 -I jenner_run.py <script.py> <script args...>"""
import sys, os, json
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
URL = os.environ['JEN_RPC']; TIME = hex(1796697100)
BSC = {'https://bsc-dataseed1.bnbchain.org', URL}
_rpc = evm.rpc
def rpc(url, method, params, timeout=60):
    if url in BSC and method == 'eth_call':
        params = list(params)
        while len(params) < 3: params.append({})
        params = params[:3] + [{'time': TIME}]
        url = URL
    return _rpc(url, method, params, timeout)
evm.rpc = rpc
_nets = evm.networks
def networks(*a, **k):
    return [(c, n, URL if c == 56 else u) for c, n, u in _nets(*a, **k)]
evm.networks = networks
_load = json.load
def load(f, *a, **k):
    d = _load(f, *a, **k)
    if isinstance(d, dict) and 'networks' in d:
        for n in d['networks']:
            if n.get('chainId') == 56: n['rpc'] = URL
    return d
json.load = load
script = sys.argv[1]; sys.argv = [script] + sys.argv[2:]
code = open(script).read()
g = {'__name__': '__main__', '__file__': script}
exec(compile(code, script, 'exec'), g)
