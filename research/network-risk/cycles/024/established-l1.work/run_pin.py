"""Cycle 24 copy of cycles/021/established-l1.work/run_48pin.py with PIN_URL. Pinned variant. Retries each batch until the tag contains $WANT (up to 60 times).
Run one opdiff tool against rpc-bsc.48.club, sending every eth_call as a JSON-RPC batch
[web3_clientVersion, eth_call] so each answer is tagged with the build that served it.
Usage: python3 run_48club.py <tool.py> <args...>; tags go to $TAGLOG."""
import sys, os, runpy, json, urllib.request, collections, atexit
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
URL = os.environ.get('PIN_URL','https://bsc-dataseed1.bnbchain.org')
WANT = os.environ['WANT']
_all = evm.networks()
evm.networks = lambda path=None: [n for n in _all if n[0] == 1] + [(56, 'BSC pinned ' + WANT, URL)]
tags = collections.Counter(); misses = collections.Counter()
orig = evm.rpc
def rpc(url, method, params, timeout=60):
    if url != URL or method != 'eth_call':
        return orig(url, method, params, timeout)
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                       {'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params}]).encode()
    for attempt in range(60):
        req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
        with urllib.request.urlopen(req, timeout=timeout, context=evm._ctx) as r:
            j = json.load(r)
        d = {x['id']: x for x in j}
        tag = d[1].get('result', 'ERR')
        if WANT in tag: break
        misses[tag] += 1
    else:
        raise RuntimeError('pinned build not reached: ' + WANT)
    tags[tag] += 1
    if 'error' in d[2]:
        raise RuntimeError(json.dumps(d[2]['error'])[:300])
    return d[2]['result']
evm.rpc = rpc
atexit.register(lambda: open(os.environ.get('TAGLOG', 'tags.log'), 'a').write(json.dumps({'tool': sys.argv[0], 'want': WANT, 'tags': tags, 'discardedOtherBuild': misses}) + '\n'))
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
