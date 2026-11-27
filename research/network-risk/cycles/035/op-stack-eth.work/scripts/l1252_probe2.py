"""L-1252 second probe: full eth_simulateV1 block objects and gas estimation on a gas-sensitive frame, repeated, to find
an answer that differs between the two OP Mainnet builds. Read-only."""
import json, sys, urllib.request, collections
U = 'https://mainnet.optimism.io'
def rpc(body):
    r = urllib.request.Request(U, data=json.dumps(body).encode(), headers={'content-type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())
A = '0x00000000000000000000000000000000000c0de1'; B = '0x00000000000000000000000000000000000c0de2'
# A: CALL B with all gas, then require success: GAS PUSH20 B ... simplified: PUSH1 0 DUP1 DUP1 DUP1 DUP1 PUSH20 B GAS CALL PUSH1 0x1a JUMPI INVALID ; JUMPDEST STOP
callB = '6000808080807300000000000000000000000000000000000c0de25af1601d57fe5b00'
# B: burn gas in a loop of 200 SSTOREs to fresh slots then stop
burn = '60005b8060010190818155610c8081106002575000'
probes = {
 'simv1full': {'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'calls': [{'to': A}], 'stateOverrides': {A: {'code': '0x' + callB}, B: {'code': '0x' + burn}}}]}, 'latest']},
 'estimate63': {'method': 'eth_estimateGas', 'params': [{'to': A}, 'latest', {A: {'code': '0x' + callB}, B: {'code': '0x' + burn}}]},
 'accesslist': {'method': 'eth_createAccessList', 'params': [{'to': A}, 'latest']},
 'trace': {'method': 'debug_traceCall', 'params': [{'to': A}, 'latest', {'tracer': 'callTracer', 'stateOverrides': {A: {'code': '0x' + callB}, B: {'code': '0x' + burn}}}]},
 'feehist': {'method': 'eth_feeHistory', 'params': ['0x1', '0x98af000', [50]]},
 'blockfull': {'method': 'eth_getBlockByNumber', 'params': ['0x98af000', False]},
 'receipts': {'method': 'eth_getBlockReceipts', 'params': ['0x98af000']},
}
N = int(sys.argv[2]); out = {}
for k, p in probes.items():
    c = collections.Counter()
    for i in range(N):
        try:
            a = rpc(dict(jsonrpc='2.0', id=1, **p)); a.pop('id', None); s = json.dumps(a, sort_keys=True)
        except Exception as e: s = 'EXC ' + str(e)[:120]
        c[s] += 1
    out[k] = c.most_common()
    print(k, len(c), [(s[:400], n) for s, n in c.most_common(3)], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
