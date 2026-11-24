# Celo: three currency ids on the native CELO balance (address(0), the CELO token, the wrapped native predeploy).
# One unlock on the deployed PoolManager through eth_call with state overrides. Nothing is sent.
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'core-code-loose-guards.work'))
from lib import *
from tests import E, B, SINK, FROM, overrides, tl, bal
from show import dump
HERE2 = os.path.dirname(os.path.abspath(__file__))
F = '0x471EcE3750Da237f93B8E339c536989b8978a438'
W = '0x4200000000000000000000000000000000000006'
def run():
    n = net(42220); u = n['rpc']; pm = n['poolManager']
    inner = script(0, [
        item(W, cd('balanceOf(address)', pm)), bal(W),                    # 0 1
        item(pm, cd('take(address,address,uint256)', 0, W, 1000)),        # 2 native payout to the wrapper, empty calldata
        item(W, cd('balanceOf(address)', pm)), bal(W),                    # 3 4 wrapper credits the PoolManager
        item(pm, cd('settle()')),                                         # 5 credit under the wrapper id (synced before the unlock)
        tl(pm, delta_slot(E, W)), tl(pm, delta_slot(E, 0)),               # 6 7
        item(pm, cd('take(address,address,uint256)', W, SINK, 1000)),     # 8 wrapper tokens leave, wrapper delta back to 0
        item(W, cd('balanceOf(address)', SINK)),                          # 9
        item(pm, cd('take(address,address,uint256)', F, W, 500)),         # 10 face payout to the wrapper: native moves, no call into the wrapper
        item(W, cd('balanceOf(address)', pm)), bal(W),                    # 11 12 no mint, wrapper native balance up by 500
        tl(pm, delta_slot(E, F)),                                         # 13 -500
        item(pm, cd('sync(address)', 0)),                                 # 14
        item(pm, cd('settle()'), 1000),                                   # 15 repay the native debt
        item(pm, cd('sync(address)', F)), tl(pm, RESERVES), bal(pm),      # 16 17 18
        item(pm, cd('settle()'), 1),                                      # 19 expect NonzeroNativeValue
        item(F, cd('transfer(address,uint256)', pm, 500)),                # 20 pay through the face
        item(pm, cd('settle()')),                                         # 21 credit 500 under the face id
        tl(pm, delta_slot(E, F)), tl(pm, delta_slot(E, 0)), tl(pm, delta_slot(E, W)), tl(pm, NONZERO),   # 22 23 24 25
    ])
    outer = script(0, [
        bal(pm), item(F, cd('balanceOf(address)', pm)), item(W, cd('balanceOf(address)', pm)),   # 0 1 2
        item(pm, cd('sync(address)', W)),                                 # 3
        item(pm, unlock(inner)),                                          # 4
        bal(pm), item(W, cd('balanceOf(address)', pm)), tl(pm, IS_UNLOCKED),   # 5 6 7
    ])
    blk = rpc(u, 'eth_blockNumber', [])['result']
    r = rpc(u, 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + outer}, blk, overrides(pm, True)])
    return {'block': blk, 'client': rpc(u, 'web3_clientVersion', []).get('result'), 'res': r}
if __name__ == '__main__':
    o = run(); json.dump(o, open(os.path.join(HERE2, 'raw', 'celo_triple.json'), 'w'), indent=1)
    print('block', int(o['block'], 16), o['client'])
    print('\n'.join(dump(o['res']['result'])) if 'result' in o['res'] else o['res'])
