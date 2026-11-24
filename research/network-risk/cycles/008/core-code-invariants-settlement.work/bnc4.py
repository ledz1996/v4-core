# BNB Smart Chain: four pooled tokens pay BNC4 to the sender when they are transferred. Can an ordinary account book that
# inflow at the deployed PoolManager? One unlock by eth_call with state overrides, nothing is sent.
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'core-code-loose-guards.work'))
from lib import *
from tests import E, B, SINK, FROM, overrides, tl, bal
from show import dump
HERE2 = os.path.dirname(os.path.abspath(__file__))
X = '0x7c8d5502b544ddaf8852fc46d1174e34876d545c'
TS = {'xiaogudong': '0x026c029ac3395a893784fe6f3aece2bfc613ffff', 'build': '0x489ce5fb31523516f3fb4aacd597508c80edffff', '4cat': '0xa5b977667117877d06e0e74bd6d85cf7e241ffff', '4Stock': '0xd270d4e1ec6e6e0d28c0ecb8be966ec75997ffff'}
def run(url=None):
    n = net(56); u = url or n['rpc']; pm = n['poolManager']
    items = [item(X, cd('balanceOf(address)', pm))]
    for nm, T in TS.items():
        items += [item(pm, cd('sync(address)', X)),
                  item(pm, cd('take(address,address,uint256)', T, E, 0)),      # zero amount transfer of T by the PoolManager
                  item(X, cd('balanceOf(address)', pm)),
                  item(pm, cd('settle()')),                                    # credit under BNC4 if the balance rose
                  item(pm, cd('sync(address)', X)),
                  item(pm, cd('take(address,address,uint256)', T, E, 1)),      # one base unit of T, owed by the caller
                  item(X, cd('balanceOf(address)', pm)),
                  item(pm, cd('settle()')),
                  tl(pm, delta_slot(E, T)), tl(pm, delta_slot(E, X))]
    items += [item(X, cd('balanceOf(address)', E)), tl(pm, delta_slot(E, X)), tl(pm, NONZERO)]
    inner = script(1, items)
    outer = script(0, [item(pm, unlock(inner))])
    blk = rpc(u, 'eth_blockNumber', [])['result']
    r = rpc(u, 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + outer, 'gas': hex(30_000_000)}, blk, overrides(pm, True)])
    return {'block': blk, 'res': r}
if __name__ == '__main__':
    o = run(sys.argv[1] if len(sys.argv) > 1 else None); json.dump(o, open(os.path.join(HERE2, 'raw', 'bnc4.json'), 'w'), indent=1)
    print('block', int(o['block'], 16))
    print('\n'.join(dump(o['res']['result'])) if 'result' in o['res'] else json.dumps(o['res'])[:600])
