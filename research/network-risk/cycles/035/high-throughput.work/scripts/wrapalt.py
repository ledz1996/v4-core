"""Run an opdiff script with Monad (143) read from the endpoint in env ALTURL (rpc.monad.xyz answered HTTP 429 to swaps.py on 2026-11-27).
Usage (from tools/opdiff): ALTURL=https://rpc1.monad.xyz python3 wrap143.py <script.py> <args...>"""
import sys, runpy, os
sys.path.insert(0, os.getcwd())
import evm
ALT = os.environ['ALTURL']
_net = evm.networks
def networks(*a, **k):
    return [(c, n, ALT if c == int(os.environ["ALTCHAIN"]) else u) for (c, n, u) in _net(*a, **k)]
evm.networks = networks
import json
_load = json.load
def load(f, *a, **k):
    d = _load(f, *a, **k)
    if isinstance(d, dict) and isinstance(d.get('networks'), list):
        for n in d['networks']:
            if n.get("chainId") == int(os.environ["ALTCHAIN"]): n['rpc'] = ALT
    return d
json.load = load
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
