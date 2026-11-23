# An account whose EIP-7702 designator names an enshrined token: what do the take and sync call shapes get from it, with the PoolManager as caller?
import json, os
from lib import *
from stubs import RUNNER, designator
A = '0x7e57000000000000000000000000000000000d07'; SINK = '0x7e57000000000000000000000000000000000505'; FROM = '0x7e57000000000000000000000000000000000a00'
CASES = [(4217, None, '0x20c0000000000000000000000000000000000000'), (8453, None, '0xb2000000000000000000002feb517dfec7415344'),
         (97, 'https://bsc-testnet-dataseed.bnbchain.org', '0xca5200000000000000000069e5bbadfec8b9075a'),
         (5042, None, '0x3600000000000000000000000000000000000000'), (42220, None, '0x471EcE3750Da237f93B8E339c536989b8978a438'), (137, None, '0x0000000000000000000000000000000000001010'),
         (4217, None, '0xdec0000000000000000000000000000000000000'), (4217, None, '0xfeec000000000000000000000000000000000000')]
out = []
for cid, url, T in CASES:
    if url is None: n = net(cid); url = n['rpc']; pm = n['poolManager']
    else: pm = net(56)['poolManager']
    b = lambda t, a: item(t, cd('balanceOf(address)', a))
    x = cd('transfer(address,uint256)', SINK, 1); x0 = cd('transfer(address,uint256)', SINK, 0)
    sc = script(0, [b(T, pm), b(A, pm), item(A, x0), item(A, x), b(T, pm), b(T, SINK), item(A, '')])
    blk = rpc(url, 'eth_blockNumber', [])['result']
    r = rpc(url, 'eth_call', [{'from': FROM, 'to': pm, 'data': '0x' + sc}, blk, {pm: {'code': RUNNER}, A: {'code': designator(T)}}])
    recs = [short(ok, d) for ok, d in records(r['result'])] if 'result' in r else [json.dumps(r)[:300]]
    names = ['token.balanceOf(PM)', 'A.balanceOf(PM)', 'A.transfer(sink,0)', 'A.transfer(sink,1)', 'token.balanceOf(PM) after', 'token.balanceOf(sink) after', 'A with empty calldata']
    row = {'chainId': cid, 'token': T, 'tokenCode': rpc(url, 'eth_getCode', [T, blk]).get('result', '')[:12], 'block': int(blk, 16), 'records': dict(zip(names, recs)) if len(recs) == len(names) else recs}
    out.append(row); print(json.dumps(row, indent=1))
json.dump(out, open(os.path.join(HERE, 'raw', 'deleg_token.json'), 'w'), indent=1)
