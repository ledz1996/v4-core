"""L-127 follow-up: the PoolManager's own call shapes with msg.sender = PoolManager and
tx.origin = an unrelated account. The PoolManager's code is replaced, inside eth_call only,
by a 34-byte forwarder (target, value, calldata); its balance and the target's state stay real.
Usage: python3 inner_call.py <out.json>"""
import sys, json, urllib.request
FWD = '0x6034360380603 45f375f5f825f6014355f3560601c5af13d5f5f3e602157 3d5ffd5b3d5ff3'.replace(' ', '')
NETS = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
NETS = NETS if isinstance(NETS, list) else NETS.get('networks', NETS)
IDS = [10, 8453, 130, 7777777, 480, 57073, 1868]
ORIGIN = '0x00000000000000000000000000000000000c0ffe'
T = ['0x42000000000000000000000000000000000000%s' % h for h in ('06', '07', '10', '11', '13', '14', '15', '16', '18', '19', '1a', '1b', '20', '21', '42')]
def rpc(url, m, p):
    req = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(req, timeout=60))
out = []
for n in NETS:
    if n['chainId'] not in IDS: continue
    url, pm = n['rpc'], n['poolManager'].lower()
    for a in T:
        for shape, value, data in (('native1wei', 1, ''), ('native0', 0, ''), ('transfer1', 0, 'a9059cbb' + '0' * 24 + '000000000000000000000000000000000000dead' + '%064x' % 1)):
            cd = '0x' + a[2:] + '%064x' % value + data
            try:
                r = rpc(url, 'eth_call', [{'from': ORIGIN, 'to': pm, 'data': cd, 'gas': '0x1c9c380'}, 'latest', {pm: {'code': FWD}}])
                res = ('ok:' + r['result'][:140]) if 'result' in r else ('rev:' + json.dumps(r.get('error'))[:200])
            except Exception as e:
                res = 'exc:' + str(e)[:100]
            out.append({'chainId': n['chainId'], 'target': a, 'shape': shape, 'result': res})
            print(n['chainId'], a[-2:], shape, res[:110], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
