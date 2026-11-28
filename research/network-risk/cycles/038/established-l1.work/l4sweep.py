"""L4 refresh: the call shapes the PoolManager can make (P1 value call with empty calldata, P2 transfer, P3 balanceOf,
P5 a hook selector) sent with from = the PoolManager to the special addresses of Polygon, BNB Chain and Avalanche.
Read-only eth_call at latest. Usage: python3 -I l4sweep.py <out.json>"""
import sys, json, urllib.request

def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(),
                               headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=40))

N = {137: ('https://polygon-bor-rpc.publicnode.com', '0x67366782805870060151383f4bbff9dab53e5cd6'),
     56: ('https://bsc-dataseed1.bnbchain.org', '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'),
     43114: ('https://api.avax.network/ext/bc/C/rpc', '0x06380c0e0912312b5150364b9dc4542ba0dbbc85')}
H = lambda n: '0x' + n.to_bytes(20, 'big').hex()
COMMON = [H(i) for i in range(1, 0x12)] + [H(0x100), '0x0000f90827f1c53a10cb7a02335b175320002935', '0x000f3df6d732807ef1319fb7b8bb8522d0beac02',
          '0x00000961ef480eb55e80d19ad83579a64c007002', '0x0000bbddc7ce488642fb579f8b00f3a590007251', '0x000000000000000000000000000000000000dead',
          '0x0000000000000000000000000000000000000000']
EXTRA = {137: [H(0x1000), H(0x1001), H(0x1010), '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270'],
         56: [H(i) for i in range(0x1000, 0x1009)] + [H(i) for i in range(0x2000, 0x2006)] + [H(i) for i in range(0x64, 0x6a)] + [H(0x70), H(0x48),
              '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'],
         43114: ['0x0100000000000000000000000000000000000000', '0x0100000000000000000000000000000000000001', '0x0100000000000000000000000000000000000002',
                 '0x0200000000000000000000000000000000000000', '0x0200000000000000000000000000000000000001', '0x0200000000000000000000000000000000000002',
                 '0x0200000000000000000000000000000000000003', '0x0200000000000000000000000000000000000004', '0x0200000000000000000000000000000000000005',
                 '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7']}
RECIP = '000000000000000000000000000000000000000000000000000000000000beef'

def shapes(pm):
    p = pm[2:].rjust(64, '0')
    return {'P1_value1_empty': ('0x', '0x1'), 'P1_value0_empty': ('0x', '0x0'),
            'P2_transfer_1': ('0xa9059cbb' + RECIP + '1'.rjust(64, '0'), '0x0'),
            'P2_transfer_0': ('0xa9059cbb' + RECIP + '0'.rjust(64, '0'), '0x0'),
            'P3_balanceOf_pm': ('0x70a08231' + p, '0x0'),
            'P5_beforeSwap': ('0x575e24b4' + '0' * 64 * 12, '0x0')}

def main():
    out = {}
    for cid, (u, pm) in N.items():
        bn = rpc(u, 'eth_blockNumber', [])['result']
        rows = {}
        for a in COMMON + EXTRA[cid]:
            code = rpc(u, 'eth_getCode', [a, bn]).get('result', '0x')
            row = {'codeLen': (len(code) - 2) // 2}
            for name, (data, val) in shapes(pm).items():
                r = rpc(u, 'eth_call', [{'from': pm, 'to': a, 'data': data, 'value': val, 'gas': '0x1c9c380'}, bn])
                if 'result' in r:
                    ret = r['result'][2:]
                    rec = {'ok': True, 'retLen': len(ret) // 2}
                    if name.startswith('P2'):
                        rec['acceptedByCurrencyTransfer'] = (len(ret) == 0) or (len(ret) >= 64 and int(ret[:64], 16) == 1)
                    if name.startswith('P3'):
                        rec['word'] = ret[:64] if len(ret) >= 64 else None
                    if name.startswith('P5'):
                        rec['selectorEcho'] = len(ret) >= 64 and ret[:8] == '575e24b4'
                else:
                    rec = {'ok': False, 'err': str(r.get('error', {}).get('message', ''))[:80]}
                row[name] = rec
            rows[a] = row
        out[cid] = {'block': int(bn, 16), 'rows': rows}
        print(cid, 'done', len(rows), flush=True)
    json.dump(out, open(sys.argv[1], 'w'), indent=1)

if __name__ == '__main__':
    main()
