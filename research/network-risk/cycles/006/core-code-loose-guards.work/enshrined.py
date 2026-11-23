# What do addresses in the enshrined token ranges answer to the two call shapes of take and sync, with the PoolManager as caller?
import json, os
from lib import *
SINK = '0x7e57000000000000000000000000000000000505'
CASES = [
 (8453, None, ['0xb20f000000000000000000000000000000000000', '0xb2000000000000000000002feb517dfec7415344', '0xb200000000000000000001000000000000000001', '0xb2000000000000000000000d8ce462e99ee7a47b', '0xb200000000000000000000000000000000abcdef', '0xb2000000000000000000000000000000deadbeef']),
 (4217, None, ['0x20c0000000000000000000000000000000000000', '0x20c000000000000000000000030a4c7f7b8f3586', '0x20c00000000000000000000000000000deadbeef', '0x20c0000000000000000000000000000000abcdef', '0x20c0ffffffffffffffffffffffffffffffffffff']),
 (56, None, ['0xca52000000000000000001217954ab5467577565', '0xca5200000000000000000069e5bbadfec8b9075a', '0xca52000000000000000000000000000000abcdef']),
 (97, 'https://bsc-testnet-dataseed.bnbchain.org', ['0xca52000000000000000001217954ab5467577565', '0xca5200000000000000000069e5bbadfec8b9075a', '0xca52000000000000000000000000000000abcdef', '0xca52ffffffffffffffffffffffffffffffffffff']),
]
out = []
for cid, url, addrs in CASES:
    if url is None: n = net(cid); url = n['rpc']; pm = n['poolManager']
    else: pm = net(56)['poolManager']
    blk = rpc(url, 'eth_blockNumber', []).get('result')
    for a in addrs:
        row = {'chainId': cid, 'block': blk, 'address': a, 'code': rpc(url, 'eth_getCode', [a, blk]).get('result')}
        for name, data in (('balanceOf', cd('balanceOf(address)', pm)), ('transfer0', cd('transfer(address,uint256)', SINK, 0)), ('transfer1', cd('transfer(address,uint256)', SINK, 1)), ('empty', '')):
            r = rpc(url, 'eth_call', [{'from': pm, 'to': a, 'data': '0x' + data}, blk])
            row[name] = r['result'] if 'result' in r else 'ERR ' + json.dumps(r.get('error'))[:160]
        out.append(row); print(json.dumps(row))
json.dump(out, open(os.path.join(HERE, 'raw', 'enshrined.json'), 'w'), indent=1)
