"""L-415 two-call transient storage test with eth_simulateV1: one block, call 1 stores 0x2a in
transient slot 7 of contract C, call 2 (a separate transaction in the same block) loads slot 7.
Code of C: if calldata is empty, TLOAD(7) and return it; else TSTORE(7, 0x2a) and return TLOAD(7)."""
import json, urllib.request, sys
C = '0x00000000000000000000000000000000000c0ffe'
# CALLDATASIZE ISZERO PUSH1 load JUMPI ; PUSH1 2a PUSH1 07 TSTORE ; JUMPDEST(load) PUSH1 07 TLOAD PUSH0 MSTORE PUSH1 20 PUSH0 RETURN
code = '0x' + '3615600a57602a60075d' + '5b' + '60075c5f5260205ff3'
def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except Exception as e: return {'err': str(e)}
out = {}
for u in sys.argv[1:]:
    single = rpc(u, 'eth_call', [{'to': C, 'data': '0x01'}, 'latest', {C: {'code': code}}])
    sim = rpc(u, 'eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': {C: {'code': code}},
          'calls': [{'from': '0x00000000000000000000000000000000000000aa', 'to': C, 'data': '0x01'},
                    {'from': '0x00000000000000000000000000000000000000aa', 'to': C, 'data': '0x'}]}], 'validation': False}, 'latest'])
    out[u] = {'client': rpc(u, 'web3_clientVersion', []).get('result'), 'singleStoreThenLoad': single, 'simulate': sim}
print(json.dumps(out, indent=1))
