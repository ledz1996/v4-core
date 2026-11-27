"""Check that a block time override past Jenner switches the Jenner rules on dataseed1: TIMESTAMP and a call to 0x70 (BEP-706 millisecond time precompile) in one eth_simulateV1 block. Read-only."""
import json, urllib.request, sys
URL = sys.argv[1]
def rpc(m, p):
    r = urllib.request.Request(URL, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=60))
# runtime: staticcall 0x70 with no input, return (success, returndatasize, first word)
code = '0x' + '6020' + '5f' + '5f' + '5f' + '6070' + '5a' + 'fa' + '5f52' + '3d6020' + '52' + '6040' + '5f' + 'f3'
# PUSH1 32 (retSize) PUSH0 retOff... build carefully: STATICCALL(gas, addr, inOff, inSize, outOff, outSize)
code = '0x' + '6020' + '6040' + '5f' + '5f' + '6070' + '5a' + 'fa' + '5f52' + '3d' + '6020' + '52' + '6060' + '5f' + 'f3'
A = '0x000000000000000000000000000000000000c0de'
for t in (None, 1796697100):
    bo = {'time': hex(t)} if t else {}
    res = rpc('eth_simulateV1', [{'blockStateCalls': [{'blockOverrides': bo, 'stateOverrides': {A: {'code': code}}, 'calls': [{'to': A, 'gas': '0x100000'}]}]}, 'latest'])
    print(t, json.dumps(res)[:600])
