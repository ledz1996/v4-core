"""Run one opdiff tool with every request to forno.celo.org pinned to one backend.

forno.celo.org load balances two execution clients. A JSON-RPC batch goes to one
backend as a whole, so each request is sent as [web3_clientVersion, request,
web3_clientVersion] and kept only when both version answers start with the wanted
prefix. Other answers are discarded and the batch is sent again. Read-only.

Usage: python3 pin.py <Geth|reth> <tool.py> [tool args ...]
"""
import sys, os, json, runpy, time, urllib.request, collections

TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, TOOLS)
import evm  # noqa: E402

WANT = sys.argv[1]
FORNO = 'https://forno.celo.org'
STATS = collections.Counter()
_orig = evm.rpc


def pinned(url, method, params, timeout=60):
    if not url.startswith(FORNO):
        return _orig(url, method, params, timeout)
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                       {'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params},
                       {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]).encode()
    for k in range(200):
        req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=evm._ctx) as r:
                j = {x['id']: x for x in json.load(r)}
        except Exception as e:  # noqa
            STATS['transport'] += 1; time.sleep(1 + k % 5); continue
        v1, v3 = j[1].get('result', ''), j[3].get('result', '')
        if v1.startswith(WANT) and v3.startswith(WANT):
            STATS['kept:' + v1] += 1
            if 'error' in j[2]:
                raise RuntimeError(json.dumps(j[2]['error'])[:300])
            return j[2]['result']
        STATS['skip:' + v1 + '|' + v3] += 1
    raise RuntimeError('backend %s not reached' % WANT)


evm.rpc = pinned
tool = sys.argv[2]
sys.argv = [tool] + sys.argv[3:]
try:
    runpy.run_path(os.path.join(TOOLS, tool), run_name='__main__')
finally:
    print('PIN', WANT, dict(STATS), file=sys.stderr)
