"""Positive control for tsim.py: one call that runs TSTORE(0,1) then returns TLOAD(0). Expected 1."""
import json, sys, urllib.request, ssl
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
code = bytes.fromhex('6001' '6000' '5d' '6000' '5c' '6000' '52' '6020' '6000' 'f3')
B = '0x00000000000000000000000000000000007e5702'
for u in sys.argv[1:]:
    q = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': B, 'data': '0x'}, 'latest', {B: {'code': '0x' + code.hex()}}]}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    print(u, json.load(urllib.request.urlopen(q, timeout=40, context=ctx)).get('result'))
