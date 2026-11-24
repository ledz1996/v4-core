"""A1 probe: eth_simulateV1 with two calls in one simulated block to one contract placed by state override.
Call 1 (empty calldata) runs TSTORE(0,1); call 2 (one byte of calldata) returns TLOAD(0). Expected 0. Also the same pair in one
transaction is not possible here; this only exercises the boundary between transactions in the simulation path."""
import json, sys, urllib.request, ssl
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
body = bytes.fromhex('6000' '5c' '6000' '52' '6020' '6000' 'f3')
pre = bytes.fromhex('36' '15' '60') ; jd = len(pre) + 1 + 1 + len(body)
code = pre + bytes([jd]) + bytes.fromhex('57') + body + bytes.fromhex('5b' '6001' '6000' '5d' '00')
assert code[jd] == 0x5b
A = '0x00000000000000000000000000000000007e5701'
def rpc(u, m, p):
    q = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    try: return json.load(urllib.request.urlopen(q, timeout=40, context=ctx))
    except Exception as e: return {'exc': str(e)[:200]}
for u in sys.argv[1:]:
    p = [{'blockStateCalls': [{'stateOverrides': {A: {'code': '0x' + code.hex()}}, 'calls': [{'from': '0x00000000000000000000000000000000000c0ffe', 'to': A, 'data': '0x'}, {'from': '0x00000000000000000000000000000000000c0ffe', 'to': A, 'data': '0x01'}]}]}, 'latest']
    r = rpc(u, 'eth_simulateV1', p)
    try: print(u, [c.get('returnData') or c.get('status') for c in r['result'][0]['calls']])
    except Exception: print(u, json.dumps(r)[:300])
