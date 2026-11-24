import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'core-code-loose-guards.work'))
from lib import *
n = net(42220); u = n['rpc']; pm = n['poolManager']
F = '0x471EcE3750Da237f93B8E339c536989b8978a438'
blk = rpc(u, 'eth_blockNumber', [])['result']
slot = '0x360894a13ba1a2110667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
impl = rpc(u, 'eth_getStorageAt', [F, slot, blk]); print('block', int(blk,16), 'impl slot', impl)
r = rpc(u, 'eth_call', [{'to': F, 'data': '0x' + sel('_getImplementation()')}, blk]); print('_getImplementation', r)
im = '0x' + (r.get('result') or impl['result'])[-40:]
out = {'block': blk, 'impl': im}
for name, call in [('impl.balanceOf(pm)', {'to': im, 'data': '0x' + cd('balanceOf(address)', pm)}),
                   ('getBalance(pm)', None),
                   ('impl.transfer(sink,1) from pm', {'from': pm, 'to': im, 'data': '0x' + cd('transfer(address,uint256)', '0x7e57000000000000000000000000000000000505', 1)}),
                   ('impl.transfer(sink,0) from pm', {'from': pm, 'to': im, 'data': '0x' + cd('transfer(address,uint256)', '0x7e57000000000000000000000000000000000505', 0)}),
                   ('face.transfer(sink,1) from pm', {'from': pm, 'to': F, 'data': '0x' + cd('transfer(address,uint256)', '0x7e57000000000000000000000000000000000505', 1)}),
                   ('impl code len', None)]:
    if name == 'getBalance(pm)': x = rpc(u, 'eth_getBalance', [pm, blk])
    elif name == 'impl code len': x = rpc(u, 'eth_getCode', [im, blk]); x = {'result': len(x.get('result', '0x')) // 2 - 1}
    else: x = rpc(u, 'eth_call', [call, blk])
    out[name] = x; print(name, json.dumps(x)[:300])
json.dump(out, open('raw/celo_impl.json', 'w'), indent=1)
