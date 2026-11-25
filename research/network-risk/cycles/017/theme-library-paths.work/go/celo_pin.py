"""Runs the offsets.py vectors on forno.celo.org pinned to one backend: each eth_call is batched between two
web3_clientVersion requests and kept only when both name the wanted backend (Geth = celo op-geth, reth = celo-reth).
Usage: python3 -I celo_pin.py <out.json> <Geth|reth> [repeat batch up to N times]"""
import sys, json, time, urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import offsets_lib as L
from evm import assemble, STUB
U = 'https://forno.celo.org'; want = sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def batch(code):
    tx = {'to': STUB, 'data': '0x' + L.CD.hex(), 'gas': hex(1_000_000)}
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [tx, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
    r = json.load(urllib.request.urlopen(urllib.request.Request(U, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'}), timeout=60, context=ctx))
    r = {x['id']: x for x in r}
    return r[1].get('result', ''), r[3].get('result', ''), r[2]
out = []; bad = 0; vers = set()
for kind in L.KINDS:
    for o in L.OFFS:
        code = assemble(L.prog(kind, o)); exp = L.expect(kind, o, code); e = exp if isinstance(exp, str) else exp.hex()
        got = None
        for k in range(N):
            try: v1, v3, c = batch(code)
            except Exception: time.sleep(2); continue
            if v1.startswith(want) and v3.startswith(want):
                vers.add(v1); got = c['result'][2:] if 'result' in c else 'FAIL:' + json.dumps(c.get('error'))[:100]; break
        if got is None: got = 'UNPINNED'
        ok = got == e or (e == 'FAIL' and got.startswith('FAIL:'))
        bad += not ok; out.append(dict(kind=kind, offset=hex(o), ok=ok, got=got[:140], expected=e[:140]))
json.dump({'backend': sorted(vers), 'vectors': out}, open(sys.argv[1], 'w'), indent=0)
print('backend', sorted(vers), 'vectors', len(out), 'mismatches', bad, 'unpinned', sum(r['got'] == 'UNPINNED' for r in out))
