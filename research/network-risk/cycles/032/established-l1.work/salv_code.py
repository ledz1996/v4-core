"""Extract the Salvador BlockAlloc code from bor develop params/config.go and probe the five targets on Polygon. Read-only."""
import re, json, sys, urllib.request
src = open('raw/bor-develop/params_config.go').read()
i = src.index('"98688600": map[string]interface{}{', src.index('SalvadorBlock:     big.NewInt(98688600)'))
blk = src[i:src.index('},\n\t\t\t},\n\t\t},', i)]
targets = re.findall(r'"([0-9a-fA-F]{40})": map\[string\]interface\{\}\{\s*"balance": "(0x[0-9a-f]+)",\s*"code":\s*"(0x[0-9a-f]+)"', blk)
URL = 'https://polygon-bor-rpc.publicnode.com'
def rpc(m, p):
    r = urllib.request.Request(URL, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=30))
PM = '0x67366782805870060151383f4bbff9dab53e5cd6'
out = []
for a, bal, code in targets:
    a = '0x' + a.lower()
    rec = {'addr': a, 'allocBalance': bal, 'codeLen': len(code) // 2 - 1, 'codeHead': code[:20]}
    rec['recovery'] = re.findall(r'7f000000000000000000000000([0-9a-f]{40})', code)[:1]
    rec['nowCode'] = rpc('eth_getCode', [a, 'latest']).get('result')
    rec['nowBal'] = rpc('eth_getBalance', [a, 'latest']).get('result')
    rec['nowNonce'] = rpc('eth_getTransactionCount', [a, 'latest']).get('result')
    ov = {a: {'code': code}}
    # native value sent from the PoolManager with empty calldata, as Currency.transfer would do
    rec['pmValueEmpty'] = rpc('eth_call', [{'from': PM, 'to': a, 'value': '0x1', 'gas': '0x1000000'}, 'latest', ov])
    rec['pmValueSweep'] = rpc('eth_call', [{'from': PM, 'to': a, 'value': '0x1', 'data': '0x35faa416', 'gas': '0x1000000'}, 'latest', ov])
    rec['strangerSweep'] = rpc('eth_call', [{'from': '0x000000000000000000000000000000000000dEaD', 'to': a, 'data': '0x35faa416', 'gas': '0x1000000'}, 'latest', ov])
    rec['recoveryGetter'] = rpc('eth_call', [{'to': a, 'data': '0x78ed5d81'}, 'latest', ov])
    out.append(rec)
json.dump({'targets': out, 'code': {('0x' + a.lower()): c for a, _, c in targets}}, open('out/salvador_targets.json', 'w'), indent=1)
for r in out:
    print(json.dumps({k: v for k, v in r.items()})[:900])
