# Native faces: Celo CELO token, Arc USDC token, Polygon 0x1010. One unlock on the deployed PoolManager, eth_call with state overrides.
import json, os, sys
from lib import *
from tests import E, B, SINK, FROM, overrides, tl, bal
from show import dump
FACES = {42220: '0x471EcE3750Da237f93B8E339c536989b8978a438', 5042: '0x3600000000000000000000000000000000000000', 137: '0x0000000000000000000000000000000000001010'}
def run(cid):
    n = net(cid); u = n['rpc']; pm = n['poolManager']; F = FACES[cid]
    a = 1 if cid == 5042 else 1000                 # face units paid through the face
    wei = a * 10 ** 12 if cid == 5042 else a       # what that costs in native base units
    inner = script(1, [
        item(pm, cd('settle()'), 1000),                                   # 0 expect NonzeroNativeValue: the face was synced before the unlock
        item(pm, cd('settle()')),                                         # 1 pays 0 and resets the synced currency
        item(pm, cd('settle()'), 1000),                                   # 2 native credit 1000
        item(pm, cd('sync(address)', F)), tl(pm, RESERVES),               # 3 4
        item(pm, cd('settle()')),                                         # 5 expect 0: the same payment is not credited under the face
        tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)),               # 6 7
        item(pm, cd('sync(address)', F)),                                 # 8
        item(F, cd('transfer(address,uint256)', pm, a), a if cid == 137 else 0),   # 9 pay through the face (0x1010 wants the amount as value)
        tl(pm, RESERVES), item(F, cd('balanceOf(address)', pm)), bal(pm), # 10 11 12
        item(pm, cd('settle()')),                                         # 13 credit under the face id
        tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)),               # 14 15
        bal(SINK),                                                        # 16
        item(pm, cd('take(address,address,uint256)', F, SINK, a)),        # 17 payout under the face id
        bal(SINK),                                                        # 18
        item(pm, cd('take(address,address,uint256)', 0, SINK, 1000)),     # 19 payout of the native credit
        bal(SINK), bal(pm),                                               # 20 21
        tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)), tl(pm, NONZERO),   # 22 23 24
        # a native payout while the face is synced lowers what the settler is credited
        item(pm, cd('sync(address)', F)),                                 # 25
        item(pm, cd('take(address,address,uint256)', 0, SINK, wei)),      # 26
        item(pm, cd('settle()')),                                         # 27 expect Panic (balance below the synced reserves)
    ])
    outer = script(0, [
        item(pm, cd('sync(address)', F)), tl(pm, CURRENCY), tl(pm, RESERVES), bal(pm), item(F, cd('balanceOf(address)', pm)),   # 0-4
        item(pm, unlock(inner)),                                          # 5
    ])
    blk = rpc(u, 'eth_blockNumber', [])['result']
    r = rpc(u, 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + outer}, blk, overrides(pm, True)])
    return {'chainId': cid, 'face': F, 'block': blk, 'res': r}
if __name__ == '__main__':
    for cid in FACES:
        o = run(cid); json.dump(o, open(os.path.join(HERE, 'raw', 'faces_%d.json' % cid), 'w'), indent=1)
        print('==', cid, o['face'], int(o['block'], 16))
        print('\n'.join(dump(o['res']['result'])) if 'result' in o['res'] else o['res'])
