# Behaviour tests of the loose places on the deployed PoolManagers. eth_call with state overrides only; nothing is sent.
import sys, json, os
from lib import *
from stubs import RUNNER, proxy, designator, BAL
FROM = '0x7e57000000000000000000000000000000000a00'
E = '0x7e57000000000000000000000000000000000e01'   # runner (the ordinary account that calls unlock)
P = '0x7e57000000000000000000000000000000000d02'   # forwards by DELEGATECALL to the PoolManager
D = '0x7e57000000000000000000000000000000000d03'   # carries an EIP-7702 designator that names the PoolManager
B = '0x7e57000000000000000000000000000000000b04'   # native balance reader
SINK = '0x7e57000000000000000000000000000000000505'
X = '0x7e57000000000000000000000000000000000c06'   # currency address without code
ONE = 10 ** 18
KEY = [w(0), w('0x00000000000000000000000000000000000000ff'), w(3000), w(60), w(0)]
def init_cd(): return sel('initialize((address,address,uint24,int24,address),uint160)') + ''.join(KEY) + w(1 << 96)
def swap_cd(): return sel('swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)') + ''.join(KEY) + w(1) + w(-5) + w(4295128740) + w(0x120) + w(0)
def tl(t, slot): return item(t, cd('exttload(bytes32)', slot))
def bal(a): return item(B, w(a))
def overrides(pm, with_value=True):
    o = {E: {'code': RUNNER}, P: {'code': proxy(pm)}, D: {'code': designator(pm)}, B: {'code': BAL}}
    if with_value:
        for a in (E, P, D): o[a]['balance'] = hex(ONE)
    return o
def deleg_script(pm, T, v):
    """T is the account that runs PoolManager code in its own context (P or D). v is the native amount used (0 where the chain has no native value)."""
    inner = script(0, [
        item(T, cd('take(address,address,uint256)', 0, SINK, v)),                    # 0 T pays out of its own balance
        bal(SINK), bal(T),                                                           # 1 2
        tl(T, delta_slot(E, 0)), tl(pm, delta_slot(E, 0)),                           # 3 4 delta is in T's transient storage, none at the PoolManager
        tl(T, IS_UNLOCKED), tl(pm, IS_UNLOCKED),                                     # 5 6
        item(T, cd('mint(address,uint256,uint256)', E, 0, 7)),                       # 7
        item(T, cd('balanceOf(address,uint256)', E, 0)), item(pm, cd('balanceOf(address,uint256)', E, 0)),  # 8 9
        item(T, cd('burn(address,uint256,uint256)', E, 0, 7)),                       # 10
        item(T, cd('settle()'), v),                                                  # 11
        item(T, swap_cd()),                                                          # 12 expect DelegateCallNotAllowed
        item(T, cd('sync(address)', 0)),                                             # 13
        item(T, cd('clear(address,uint256)', 0, 0)),                                 # 14
    ])
    inner_open = script(0, [item(T, cd('take(address,address,uint256)', X, SINK, 5))])
    outer = script(0, [
        item(T, cd('sync(address)', 0)),                    # 0
        item(T, cd('settle()')),                            # 1 expect ManagerLocked
        item(T, init_cd()),                                 # 2 expect DelegateCallNotAllowed
        item(T, cd('owner()')),                             # 3
        item(T, cd('protocolFeeController()')),             # 4
        bal(pm), bal(T), bal(SINK),                         # 5 6 7
        item(T, unlock(inner)),                             # 8
        bal(pm), bal(T), bal(SINK),                         # 9 10 11
        item(T, unlock(inner_open)),                        # 12 expect CurrencyNotSettled
        item(pm, cd('owner()')),                            # 13 the real owner, for contrast
    ])
    return outer
def real_script(pm, v):
    dirty1 = (0xabc << 160) | int(X, 16); dirty2 = (0xdef << 160) | int(X, 16)
    inner_codeless = script(1, [
        item(pm, cd('take(address,address,uint256)', X, SINK, 5)),                   # 0 succeeds, moves nothing
        tl(pm, delta_slot(E, X)), tl(pm, NONZERO),                                   # 1 2
        item(pm, cd('sync(address)', X)),                                            # 3 expect revert
        item(pm, cd('settle()')),                                                    # 4 pays 0
        item(pm, cd('mint(address,uint256,uint256)', E, X, 7)),                      # 5
        item(pm, cd('balanceOf(address,uint256)', E, X)),                            # 6
        tl(pm, delta_slot(E, X)),                                                    # 7
        item(pm, cd('clear(address,uint256)', X, 0)),                                # 8 expect MustClearExactPositiveDelta
        item(pm, cd('take(address,address,uint256)', '0x0000000000000000000000000000000000000001', SINK, 3)),  # 9
        item(pm, cd('sync(address)', '0x0000000000000000000000000000000000000001')), # 10 expect revert
        item(pm, cd('take(address,address,uint256)', '0x0000000000000000000000000000000000000004', SINK, 3)),  # 11 expect revert
        item(pm, cd('sync(address)', '0x0000000000000000000000000000000000000004')), # 12
        tl(pm, RESERVES),                                                            # 13
        item(pm, cd('settle()')),                                                    # 14 expect 0
        item(pm, cd('sync(address)', 0)),                                            # 15
        item(pm, cd('mint(address,uint256,uint256)', E, dirty1, 1)),                 # 16 id with high bits
        item(pm, cd('balanceOf(address,uint256)', E, X)),                            # 17 expect 8
        item(pm, cd('balanceOf(address,uint256)', E, dirty1)),                       # 18 expect 0
        item(pm, cd('burn(address,uint256,uint256)', E, dirty2, 8)),                 # 19
        item(pm, cd('balanceOf(address,uint256)', E, X)),                            # 20 expect 0
        tl(pm, delta_slot(E, X)),                                                    # 21 expect -5
        tl(pm, delta_slot(E, '0x0000000000000000000000000000000000000001')),         # 22 expect -3
    ])
    inner_value = script(0, [
        item(pm, cd('settle()'), v),                                                 # 0
        tl(pm, delta_slot(E, 0)),                                                    # 1
        item(pm, cd('take(address,address,uint256)', 0, SINK, v)),                   # 2
        bal(SINK),                                                                   # 3
    ])
    inner_guard = script(0, [
        item(pm, cd('sync(address)', B)),                                            # 0
        item(pm, cd('settle()'), 1),                                                 # 1 expect NonzeroNativeValue
        item(pm, cd('settle()')),                                                    # 2 pays 0 and resets
        item(pm, cd('settle()'), 1 if v else 0),                                     # 3
        item(pm, cd('take(address,address,uint256)', 0, SINK, 1 if v else 0)),       # 4
    ])
    outer = script(0, [
        item(pm, cd('sync(address)', B)),                   # 0 sync while locked, B answers balanceOf with 32 bytes
        tl(pm, CURRENCY), tl(pm, RESERVES), tl(pm, IS_UNLOCKED),   # 1 2 3
        item(pm, cd('sync(address)', 0)), tl(pm, CURRENCY), # 4 5
        item(pm, cd('take(address,address,uint256)', X, SINK, 5)),   # 6 expect ManagerLocked
        item(pm, unlock(inner_codeless)),                   # 7 reverts with the inner records
        item(pm, unlock(inner_value)),                      # 8
        item(pm, unlock(inner_guard)),                      # 9
        bal(pm),                                            # 10
    ])
    return outer
def run(cid):
    n = net(cid); u = n['rpc']; pm = n['poolManager']
    out = {'chainId': cid, 'name': n['name'], 'pm': pm}
    out['block'] = rpc(u, 'eth_blockNumber', []).get('result')
    out['client'] = rpc(u, 'web3_clientVersion', []).get('result')
    for a, k in ((FROM, 'from'), (E, 'E'), (X, 'X'), (SINK, 'sink')):
        out['code_' + k] = rpc(u, 'eth_getCode', [a, 'latest']).get('result')
    z = '0x0000000000000000000000000000000000000000'
    out['zero'] = {'code': rpc(u, 'eth_getCode', [z, 'latest']).get('result'), 'nonce': rpc(u, 'eth_getTransactionCount', [z, 'latest']).get('result'), 'balance': rpc(u, 'eth_getBalance', [z, 'latest']).get('result')}
    out['unlock_from_eoa'] = rpc(u, 'eth_call', [{'from': FROM, 'to': pm, 'data': '0x' + unlock('')}, 'latest'])
    for name, builder in (('proxy', lambda v: deleg_script(pm, P, v)), ('designator', lambda v: deleg_script(pm, D, v)), ('real', lambda v: real_script(pm, v))):
        for v, wv in ((1000, True), (0, False)):
            r = rpc(u, 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + builder(v)}, 'latest', overrides(pm, wv)])
            out['%s_v%d' % (name, v)] = r
            if 'result' in r: break
    return out
if __name__ == '__main__':
    cids = [int(a) for a in sys.argv[1:]] or [n['chainId'] for n in NETS]
    for cid in cids:
        try: o = run(cid)
        except Exception as e: o = {'chainId': cid, 'error': repr(e)}
        json.dump(o, open(os.path.join(HERE, 'raw', 'tests_%d.json' % cid), 'w'), indent=1)
        print(cid, {k: (v if not isinstance(v, dict) else ('result' in v and 'ok %d bytes' % (len(v['result']) // 2 - 1)) or v) for k, v in o.items() if k not in ('pm',)})
