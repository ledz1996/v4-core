"""Re-run one recorded mismatch of journal_seq.py with the F2->F3 call gas lowered from 200,000 to 30,000, to test
whether the difference comes from gas exhaustion (the reference EVM has no gas). usage: journal_recheck.py <url> <in.json> <out.json>"""
import json, sys, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); import pyevm
URL, IN, OUT = sys.argv[1:4]
d = json.load(open(IN)); out = []
def rpc(p):
    r = urllib.request.Request(URL, json.dumps(p).encode(), {'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=90))
cv = rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []})
for m in d['mismatches']:
    codes = {int(k, 16): bytes.fromhex(v.replace('62030d40', '62007530')) for k, v in m['codes'].items()}
    w = pyevm.World(codes); ok, ret = w.call(0xca11e4, 0xc0de0000, 0, b'', False, 0)
    a = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'from': '0x%040x' % 0xca11e4, 'to': '0x%040x' % 0xc0de0000, 'gas': hex(20_000_000)}, 'latest',
             {('0x%040x' % k): {'code': '0x' + v.hex()} for k, v in codes.items()}]})
    out.append({'index': m['index'], 'equalAfterGasChange': a.get('result') == '0x' + bytes(ret).hex(), 'node': a})
json.dump({'clientVersion': cv, 'rechecks': out}, open(OUT, 'w'), indent=1); print(cv.get('result'), [(o['index'], o['equalAfterGasChange']) for o in out])
