"""Probe staged fork features by eth_call with code override. Usage: forkprobe.py <out.json> <url> ..."""
import sys, json, urllib.request
STUB = '0x00000000000000000000000000000000000f0b01'
def rpc(url, m, p):
    r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=60))
# CLZ (0x1e, EIP-7939): PUSH1 0x01 CLZ PUSH1 0 MSTORE PUSH1 32 PUSH1 0 RETURN -> 255 if CLZ exists
probes = {'CLZ(1)': '0x60011e60005260206000f3',
          'TLOAD/TSTORE': '0x602a60015d60015c60005260206000f3',
          'MCOPY': '0x60ff60005260206000600f5e60206000f3',
          'BLOBBASEFEE': '0x4a60005260206000f3',
          'BLOBHASH(0)': '0x60004960005260206000f3',
          'SELFDESTRUCT-in-call': '0x6000ff'}
pcs = {'p256verify 0x100': '0x0000000000000000000000000000000000000100', 'bls12 g1add 0x0b': '0x000000000000000000000000000000000000000b', 'kzg 0x0a': '0x000000000000000000000000000000000000000a', 'modexp 0x05': '0x0000000000000000000000000000000000000005'}
out = {}
for url in sys.argv[2:]:
    o = {'clientVersion': rpc(url, 'web3_clientVersion', []).get('result'), 'block': rpc(url, 'eth_blockNumber', []).get('result')}
    for n, c in probes.items():
        o[n] = rpc(url, 'eth_call', [{'to': STUB, 'data': '0x', 'gas': '0x100000'}, 'latest', {STUB: {'code': c}}])
    for n, a in pcs.items():
        o[n] = {'code': rpc(url, 'eth_getCode', [a, 'latest']).get('result'),
                'call160': rpc(url, 'eth_call', [{'to': a, 'data': '0x' + '00' * 160, 'gas': '0x100000'}, 'latest'])}
    o['eth_config'] = rpc(url, 'eth_config', [])
    o['type4'] = rpc(url, 'eth_estimateGas', [{'from': '0x' + '11' * 20, 'to': '0x' + '22' * 20, 'type': '0x4', 'authorizationList': [], 'maxFeePerGas': '0x174876e800'}])
    out[url] = o
    print(url, json.dumps(o)[:3000]); print()
json.dump(out, open(sys.argv[1], 'w'), indent=1)
