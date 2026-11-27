"""Which state override shapes each client accepts in eth_call (read-only). The call returns NUMBER.
usage: python3 -I ovprobe.py out.json url..."""
import json, sys, urllib.request, time
T = '0x00000000000000000000000000000000000c0de4'; X = '0x00000000000000000000000000000000000c0de5'
CODE = '0x4360005260206000f3'
CASES = {
    'plain': {},
    'unknownField': {X: {'balance': '0x1', 'fooBar': '0x1'}},
    'stateAndDiff': {X: {'state': {}, 'stateDiff': {}}},
    'movePrecompile': {'0x0000000000000000000000000000000000000002': {'movePrecompileToAddress': X}},
    'moveNonPrecompile': {X: {'movePrecompileToAddress': '0x00000000000000000000000000000000000c0de6'}},
    'nonce65bit': {X: {'nonce': '0x1ffffffffffffffff'}},
    'balance257bit': {X: {'balance': '0x1' + '0' * 64}},
    'shortSlotKey': {X: {'stateDiff': {'0x01': '0x02'}}},
    'shortSlotVal': {X: {'stateDiff': {'0x' + '00' * 32: '0x02'}}},
    'codeOddHex': {X: {'code': '0x600'}},
    'nullCode': {X: {'code': None}},
}
def raw(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'rpc-survey/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return r.read().decode()[:200]
    except Exception as e: return 'ERR ' + str(e)[:120]
out = {}
for url in sys.argv[2:]:
    cv = raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []})
    row = {'cv': cv}
    for name, extra in CASES.items():
        ov = {T: {'code': CODE}}; ov.update(extra)
        r = raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': T}, 'latest', ov]})
        row[name] = 'OK' if '"result"' in r else r[r.find('message'):][:110]
        time.sleep(0.25)
    out[url] = row
    print(url, cv[cv.find('result'):][:40]); [print('   ', k, v) for k, v in row.items() if k != 'cv']
json.dump(out, open(sys.argv[1], 'w'), indent=1)
