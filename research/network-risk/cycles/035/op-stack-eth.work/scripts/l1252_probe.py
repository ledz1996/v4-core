"""L-1252: look for a response field of mainnet.optimism.io that differs between its two builds, by sending the same
read-only request many times and counting distinct answers. Read-only JSON-RPC only."""
import json, sys, urllib.request, collections, time
U = 'https://mainnet.optimism.io'
def rpc(body):
    r = urllib.request.Request(U, data=json.dumps(body).encode(), headers={'content-type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())
# runtime code: PUSH1 0x2a PUSH1 0 MSTORE PUSH1 0x20 PUSH1 0 REVERT  -> revert with one word
REV = '602a60005260206000fd'
ADDR = '0x00000000000000000000000000000000000c0de1'
probes = {
 'revert': {'method': 'eth_call', 'params': [{'to': ADDR}, 'latest', {ADDR: {'code': '0x' + REV}}]},
 'invalidop': {'method': 'eth_call', 'params': [{'to': ADDR}, 'latest', {ADDR: {'code': '0xfe'}}]},
 'oog': {'method': 'eth_call', 'params': [{'to': ADDR, 'gas': '0x5208'}, 'latest', {ADDR: {'code': '0x5b600056'}}]},
 'badtag': {'method': 'eth_call', 'params': [{'to': ADDR}, 'nonsense']},
 'future': {'method': 'eth_call', 'params': [{'to': ADDR}, '0xffffffff']},
 'config': {'method': 'eth_config', 'params': []},
 'nomethod': {'method': 'eth_notamethod', 'params': []},
 'simv1': {'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'calls': [{'to': ADDR}], 'stateOverrides': {ADDR: {'code': '0x' + REV}}}]}, 'latest']},
 'estimate': {'method': 'eth_estimateGas', 'params': [{'to': ADDR}, 'latest', {ADDR: {'code': '0x' + REV}}]},
}
N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
out = {}
for k, p in probes.items():
    c = collections.Counter()
    for i in range(N):
        try:
            a = rpc(dict(jsonrpc='2.0', id=1, **p)); a.pop('id', None)
            if k == 'simv1' and 'result' in a:
                for b in a['result']:
                    for f in ('number', 'hash', 'timestamp', 'parentHash', 'stateRoot', 'receiptsRoot', 'logsBloom', 'size', 'baseFeePerGas', 'transactions', 'mixHash', 'transactionsRoot', 'parentBeaconBlockRoot', 'requestsHash', 'withdrawalsRoot', 'blobGasUsed', 'excessBlobGas'):
                        b.pop(f, None)
            s = json.dumps(a, sort_keys=True)
        except Exception as e:
            s = 'EXC ' + str(e)[:120]
        c[s] += 1
    out[k] = c.most_common()
    print(k, len(c), [(s[:300], n) for s, n in c.most_common(4)], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
