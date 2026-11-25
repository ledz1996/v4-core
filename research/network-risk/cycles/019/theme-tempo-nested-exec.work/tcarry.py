#!/usr/bin/env python3
"""Read-only: does a synced currency left in the PoolManager's transient storage at the end of one
transaction survive into the next transaction of the same simulated block on Tempo?
Call 1 (from account A): a stub calls PoolManager.sync(pathUSD) outside unlock and returns the
exttload of the currency and reserves slots. Call 2 (from account B): a reader returns the same
slots and the lock and count slots. eth_simulateV1, one block, at latest rules and at T14 time.
Usage: tcarry.py <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tprobe import evm, assemble, sel, PM, PATHUSD, LOCK, NZ, CUR, RES, URL, T14

SYNCER = '0x00000000000000000000000000000000000c0de7'
READER = '0x00000000000000000000000000000000000c0de8'


def reads(slots):
    p = []
    for i, slot in enumerate(slots):
        p += [('PUSH', sel('exttload(bytes32)') << 224), ('PUSH', 0), 'MSTORE', ('PUSHN', 32, slot), ('PUSH', 4), 'MSTORE',
              ('PUSH', 32), ('PUSH', 0x100 + 32 * i), ('PUSH', 36), ('PUSH', 0), ('PUSHN', 20, PM), 'GAS', 'STATICCALL', 'POP']
    return p + [('PUSH', 32 * len(slots)), ('PUSH', 0x100), 'RETURN']


syncer = assemble([('PUSH', sel('sync(address)') << 224), ('PUSH', 0), 'MSTORE', ('PUSHN', 32, PATHUSD), ('PUSH', 4), 'MSTORE',
                   ('PUSH', 0), ('PUSH', 0), ('PUSH', 36), ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PM), 'GAS', 'CALL', 'POP']
                  + reads([CUR, RES]))
reader = assemble(reads([LOCK, NZ, CUR, RES]))
ov = {SYNCER: {'code': '0x' + syncer.hex()}, READER: {'code': '0x' + reader.hex()}}
calls = [{'from': '0x000000000000000000000000000000000000a11c', 'to': SYNCER, 'gas': hex(2_000_000)},
         {'from': '0x0000000000000000000000000000000000000b0b', 'to': READER, 'gas': hex(2_000_000)}]
res = {'endpoint': URL, 'clientVersionBefore': evm.rpc(URL, 'web3_clientVersion', []), 'syncer': syncer.hex(), 'reader': reader.hex(), 'runs': []}
for label, bo in (('latest rules', {}), ('T14 time', {'time': hex(T14)})):
    bsc = {'calls': calls, 'stateOverrides': ov}
    if bo: bsc['blockOverrides'] = bo
    r = evm.rpc(URL, 'eth_simulateV1', [{'blockStateCalls': [bsc], 'validation': False}, 'latest'])
    b = r[0]
    res['runs'].append({'label': label, 'blockTime': int(b['timestamp'], 16), 'block': int(b['number'], 16),
                        'calls': [{'status': c.get('status'), 'returnData': c.get('returnData')} for c in b['calls']]})
res['clientVersionAfter'] = evm.rpc(URL, 'web3_clientVersion', [])
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(res['runs'], indent=1))
