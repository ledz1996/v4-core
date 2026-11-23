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
