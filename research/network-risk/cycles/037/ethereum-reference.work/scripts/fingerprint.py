"""Collect raw eth_call response shapes (error text, codes, field order) for a few probes on
endpoints that answer from one known client, to find a shape that identifies an erigon backend
inside a single eth_call answer. Read-only calls with state overrides only.
usage: python3 -I fingerprint.py out.json url [url ...]"""
import json, sys, time, urllib.request

T = '0x00000000000000000000000000000000000c0de1'
F = '0x0000000000000000000000000000000000000001'
PROBES = {
    'invalid': ({'from': F, 'to': T, 'gas': '0x100000'}, {T: {'code': '0xfe'}}),
    'revert': ({'from': F, 'to': T, 'gas': '0x100000'}, {T: {'code': '0x60aa60005360016000fd'}}),
    'oog': ({'from': F, 'to': T, 'gas': '0x5300'}, {T: {'code': '0x5b600056'}}),
    'badjump': ({'from': F, 'to': T, 'gas': '0x100000'}, {T: {'code': '0x600356'}}),
    'stackunder': ({'from': F, 'to': T, 'gas': '0x100000'}, {T: {'code': '0x01'}}),
    'lowgas': ({'from': F, 'to': T, 'gas': '0x1'}, {T: {'code': '0x00'}}),
}


def raw(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'rpc-survey/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode()[:400]
    except Exception as e:
        return 'ERR ' + str(e)[:150]


out = {}
for url in sys.argv[2:]:
    rows = []
    for k in range(int(__import__('os').environ.get('ROUNDS', '1'))):
        row = {'cvBefore': raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []})}
        for name, (tx, ov) in PROBES.items():
            row[name] = raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [tx, 'latest', ov]})
            time.sleep(0.2)
        rows.append(row)
    out[url] = rows
    print(url)
    for r in rows[:1]:
        for k, v in r.items():
            print('  ', k, v)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
