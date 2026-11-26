"""Run tools/opdiff/swaps.py (or replay.py) for Ethereum with the endpoint replaced, since the networks.json endpoint
answers with a challenge page. Read-only: eth_getLogs, eth_getStorageAt, eth_call. Usage: python3 swapsrun.py <script> <url> <args...>"""
import sys, os, json
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
script, url = sys.argv[1], sys.argv[2]
src = open(os.path.join(OPD, script)).read()
real_load = json.load
def load(fp, *a, **k):
    d = real_load(fp, *a, **k)
    if isinstance(d, dict) and 'networks' in d:
        for n in d['networks']:
            if n['chainId'] == 1: n['rpc'] = url
    return d
json.load = load
src = src.replace("LOG_RPC = {8453:", "LOG_RPC = {1: %r, 8453:" % url)
sys.argv = [script] + sys.argv[3:]
exec(compile(src, os.path.join(OPD, script), 'exec'), {'__name__': '__main__', '__file__': os.path.join(OPD, script)})
