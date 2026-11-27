"""eth_call of code that returns GAS, BASEFEE, GASPRICE, COINBASE, NUMBER, TIMESTAMP, GASLIMIT,
ORIGIN, CALLER, BLOBBASEFEE, PREVRANDAO, SELFBALANCE with gas, from and gasPrice omitted, to find a
block-context default that differs by client. Read-only. usage: python3 -I ctxprobe.py out.json rounds url..."""
import json, sys, time, urllib.request
OPS = [('GAS', '5a'), ('BASEFEE', '48'), ('GASPRICE', '3a'), ('COINBASE', '41'), ('NUMBER', '43'), ('TIMESTAMP', '42'),
       ('GASLIMIT', '45'), ('ORIGIN', '32'), ('CALLER', '33'), ('BLOBBASEFEE', '4a'), ('PREVRANDAO', '44'), ('SELFBALANCE', '47')]
code = ''
for i, (n, op) in enumerate(OPS):
    code += op + '61' + format(32 * i, '04x') + '52'   # op; PUSH2 off; MSTORE
code += '61' + format(32 * len(OPS), '04x') + '6000f3'  # PUSH2 len PUSH1 0 RETURN
T = '0x00000000000000000000000000000000000c0de2'
def raw(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'rpc-survey/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.loads(r.read())
    except Exception as e: return {'transport': str(e)[:150]}
out = {}
for url in sys.argv[3:]:
    rows = []
    for k in range(int(sys.argv[2])):
        cv = raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).get('result')
        j = raw(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': T}, 'latest', {T: {'code': '0x' + code}}]})
        res = j.get('result')
        vals = {n: int(res[2 + 64 * i: 66 + 64 * i], 16) for i, (n, _) in enumerate(OPS)} if res and len(res) > 2 else j
        rows.append({'cvSeparate': cv, 'vals': vals})
        time.sleep(0.3)
    out[url] = rows
    for r in rows[:3]:
        v = r['vals']
        print(url[:40], r['cvSeparate'], {k: (hex(x) if k in ('COINBASE', 'ORIGIN', 'CALLER') else x) for k, x in v.items() if k not in ('PREVRANDAO', 'TIMESTAMP')} if 'GAS' in v else v)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
