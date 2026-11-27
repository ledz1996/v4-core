"""Read-only: place TokenRollbackProbe (cycle 16 build) at the Base PoolManager address by state override and run it
for OUSD (B20) through eth_call. Kinds 1 revert, 2 invalid, 3 stack overflow, 4 out of gas, 9 STATICCALL, 0 control.
Each record: kind, frame success, [probe token bal, recipient token bal, probe eth, recipient eth] before and after.
usage: python3 -I b20_probe.py <rpc> <out.json>"""
import json, sys, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
RPC, OUT = sys.argv[1:3]
PM = '0x498581ff718922c3f8e6a244956af099b2652b2b'; OUSD = '0xb2000000000000000000002feb517dfec7415344'
TO = '0x000000000000000000000000000000000000b0b0'
probe = json.load(open('/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/build/TokenRollbackProbe.json'))['runtime']
if not probe.startswith('0x'): probe = '0x' + probe
def rpc(m, p):
    r = urllib.request.Request(RPC, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(),
                               {'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=60))
def kb(s): return keccak(s.encode()) if isinstance(keccak(b'')[:1], bytes) else keccak(s.encode())
k = keccak(b'run(address,address,uint256,uint256)')
sel = (k.hex() if isinstance(k, (bytes, bytearray)) else '%064x' % k)[:8]
def w(x): return '%064x' % x
res = {'rpc': RPC, 'clientVersionBefore': rpc('web3_clientVersion', []).get('result'), 'selector': sel, 'runs': []}
blk = rpc('eth_blockNumber', [])['result']; res['block'] = int(blk, 16)
bal0 = rpc('eth_call', [{'to': OUSD, 'data': '0x70a08231' + w(int(PM, 16))}, blk])
res['ousdBalanceOfPoolManager'] = bal0
for amt in (1, 10 ** 6, 12345678901234567):
    data = '0x' + sel + w(int(OUSD, 16)) + w(int(TO, 16)) + w(amt) + w(0)
    r = rpc('eth_call', [{'from': PM, 'to': PM, 'data': data, 'gas': hex(30_000_000)}, blk, {PM: {'code': probe}}])
    rec = {'amount': amt, 'raw': r}
    if 'result' in r:
        h = r['result'][2:]; words = [int(h[i:i + 64], 16) for i in range(0, len(h), 64)][2:]
        rows = [words[i * 10:(i + 1) * 10] for i in range(6)]
        rec['rows'] = rows; chk = []
        for row in rows:
            kind, ok, a, b = row[0], row[1], row[2:6], row[6:10]
            if kind == 0: good = ok == 1 and b[0] == a[0] - amt and b[1] == a[1] + amt
            else: good = a == b and (ok == 0)
            chk.append({'kind': kind, 'ok': ok, 'unchanged' if kind else 'movedExactly': good})
        rec['checks'] = chk
    res['runs'].append(rec)
res['clientVersionAfter'] = rpc('web3_clientVersion', []).get('result')
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'runs'}), json.dumps([r.get('checks', r['raw']) for r in res['runs']]))
