"""L-127: for every address 0x4200..00 to 0x4200..ff with code (plus Base registries and
World Chain 4337/WorldID contracts), eth_call with from = the PoolManager:
transfer(0x...dEaD,1), balanceOf(PoolManager), empty calldata value 0, empty calldata value 1 wei.
Read-only. Usage: python3 predeploy_sweep.py <out.json>"""
import sys, json, urllib.request, concurrent.futures as cf
NETS = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
NETS = NETS if isinstance(NETS, list) else NETS.get('networks', NETS)
IDS = [10, 8453, 130, 7777777, 480, 57073, 1868]
EXTRA = {8453: ['0x8453000000000000000000000000000000000001', '0x8453000000000000000000000000000000000002'],
         480: ['0x0000000071727de22e5e9d8baf0edac6f37da032', '0xe177f37af0a862a02edfea4f59c02668e9d0aaa4']}
def rpc(url, m, p):
    req = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(req, timeout=40))
        except Exception as e: err = str(e)
    return {'error': {'message': err}}
def one(url, pm, a):
    code = rpc(url, 'eth_getCode', [a, 'latest']).get('result', '0x')
    if code in ('0x', None): return None
    r = {'addr': a, 'codeLen': (len(code) - 2) // 2}
    shapes = {'transfer': ('0xa9059cbb' + '0' * 24 + '000000000000000000000000000000000000dead' + '%064x' % 1, '0x0'),
              'balanceOf': ('0x70a08231' + '0' * 24 + pm[2:], '0x0'),
              'empty0': ('0x', '0x0'), 'empty1wei': ('0x', '0x1')}
    for k, (d, v) in shapes.items():
        res = rpc(url, 'eth_call', [{'from': pm, 'to': a, 'data': d, 'value': v, 'gas': '0x1c9c380'}, 'latest'])
        r[k] = ('ok:' + res['result'][:138]) if 'result' in res else ('err:' + json.dumps(res.get('error'))[:160])
    return r
def net(n):
    cid, url, pm = n['chainId'], n['rpc'], n['poolManager'].lower()
    addrs = ['0x42000000000000000000000000000000000000%02x' % i for i in range(256)] + EXTRA.get(cid, [])
    with cf.ThreadPoolExecutor(8) as ex:
        rows = [x for x in ex.map(lambda a: one(url, pm, a), addrs) if x]
    return {'chainId': cid, 'poolManager': pm, 'rows': rows}
out = []
for n in NETS:
    if n['chainId'] in IDS:
        r = net(n); out.append(r); print(r['chainId'], len(r['rows']), 'addresses with code', flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
