#!/usr/bin/env python3
"""Read-only probe: does any precompile path that an ordinary call can reach on Tempo change or hide
the PoolManager's transient slots while an unlock is open?

A driver is placed by state override at STUB. Called from outside, it calls PoolManager.unlock with
its own calldata. In unlockCallback it
  1. reads the five transient slots (lock, nonzero delta count, synced currency, synced reserves,
     the driver's pathUSD delta) through PoolManager.exttload            -> words 0..4
  2. calls sync(pathUSD) and mint(driver, id(pathUSD), 1)                 (opens a delta of -1)
  3. reads the five slots again                                          -> words 5..9
  4. calls the probe target with the probe calldata                      -> words 10,11 (success, rds)
  5. reads the five slots again                                          -> words 12..16
  6. reverts with the 17 words; the revert bubbles out of unlock and the driver returns it.
Nothing is sent. Usage: tprobe.py <out.json> [t14]
"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
import evm
from evm import assemble, _keccak256 as K

URL = 'https://rpc.mainnet.tempo.xyz'
PM = 0x33620f62c5b9b2086dd6b62f4a297a9f30347029
STUB = int(evm.STUB, 16)
SSTORER = 0x00000000000000000000000000000000000c0de6
PATHUSD = 0x20C0000000000000000000000000000000000000
T14 = 1796745600


def sel(sig):
    return int.from_bytes(K(sig.encode())[:4], 'big')


LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
NZ = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
RES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
DELTA = int.from_bytes(K(STUB.to_bytes(32, 'big') + PATHUSD.to_bytes(32, 'big')), 'big')
SLOTS = [LOCK, NZ, CUR, RES, DELTA]
# recompute the library constants: bytes32(uint256(keccak256(name)) - 1)
for name, v in (('Unlocked', LOCK), ('NonzeroDeltaCount', NZ), ('Currency', CUR), ('ReservesOf', RES)):
    assert int.from_bytes(K(name.encode()), 'big') - 1 == v, name

RBASE = 0x1000


def ext_reads(first_word):
    p = []
    for i, slot in enumerate(SLOTS):
        p += [('PUSH', sel('exttload(bytes32)') << 224), ('PUSH', 0), 'MSTORE',
              ('PUSHN', 32, slot), ('PUSH', 4), 'MSTORE',
              ('PUSH', 32), ('PUSH', RBASE + 32 * (first_word + i)), ('PUSH', 36), ('PUSH', 0),
              ('PUSHN', 20, PM), 'GAS', 'STATICCALL', 'POP']
    return p


def call_pm(args_words, selector):
    """CALL PM with selector and 32-byte args, ignore output, revert if it fails."""
    p = [('PUSH', selector << 224), ('PUSH', 0), 'MSTORE']
    for i, w in enumerate(args_words):
        p += [('PUSHN', 32, w), ('PUSH', 4 + 32 * i), 'MSTORE']
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 4 + 32 * len(args_words)), ('PUSH', 0), ('PUSH', 0),
          ('PUSHN', 20, PM), 'GAS', 'CALL', 'ISZERO', ('REF', 'fail'), 'JUMPI']
    return p


def driver():
    p = [('PUSHN', 20, PM), 'CALLER', 'EQ', ('REF', 'cb'), 'JUMPI',
         # outer: PM.unlock(bytes(calldata))
         ('PUSH', sel('unlock(bytes)') << 224), ('PUSH', 0x200), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 0x204), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0x224), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0x244), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0x44 + 0x20), 'ADD', ('PUSH', 0x200), ('PUSH', 0),
         ('PUSHN', 20, PM), 'GAS', 'CALL', 'POP',
         'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb')]
    p += ext_reads(0)
    p += call_pm([PATHUSD], sel('sync(address)'))
    p += call_pm([STUB, PATHUSD, 1], sel('mint(address,uint256,uint256)'))
    p += ext_reads(5)
    # probe: target = calldataload(68); data = calldata[100 : 68 + len], len = calldataload(36)
    p += [('PUSH', 32), ('PUSH', 36), 'CALLDATALOAD', 'SUB',          # n = len - 32
          'DUP1', ('PUSH', 100), ('PUSH', 0x400), 'CALLDATACOPY',     # copy n bytes
          ('PUSH', 0), ('PUSH', 0), 'SWAP2', ('PUSH', 0x400), 'SWAP1',  # stack: n,0x400? fix below
          ]
    # stack now (top first): n? recompute cleanly instead
    p = p[:-5]
    p += ['POP',
          ('PUSH', 0), ('PUSH', 0),
          ('PUSH', 32), ('PUSH', 36), 'CALLDATALOAD', 'SUB',
          ('PUSH', 0x400), ('PUSH', 0),
          ('PUSH', 68), 'CALLDATALOAD', 'GAS', 'CALL',
          ('PUSH', RBASE + 32 * 10), 'MSTORE',
          'RETURNDATASIZE', ('PUSH', RBASE + 32 * 11), 'MSTORE']
    p += ext_reads(12)
    p += [('PUSH', 17 * 32), ('PUSH', RBASE), 'REVERT',
          ('LABEL', 'fail'), ('PUSH', 0xdead), ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'REVERT']
    return assemble(p)


def enc_addr(a):
    return a.to_bytes(32, 'big')


def u(v):
    return v.to_bytes(32, 'big')


A1 = 0x1234
PROBES = [
    ('control: call to an empty account', 0xdead00, b''),
    ('control: SSTORE and TSTORE in another contract', SSTORER, b''),
    ('TIP-20 pathUSD balanceOf', PATHUSD, sel('balanceOf(address)').to_bytes(4, 'big') + enc_addr(STUB)),
    ('TIP-20 pathUSD approve (state write)', PATHUSD, sel('approve(address,uint256)').to_bytes(4, 'big') + enc_addr(A1) + u(1)),
    ('TIP-20 pathUSD transfer without balance (precompile revert)', PATHUSD, sel('transfer(address,uint256)').to_bytes(4, 'big') + enc_addr(A1) + u(1)),
    ('TIP-20 pathUSD transfer of 0 (state path, no value)', PATHUSD, sel('transfer(address,uint256)').to_bytes(4, 'big') + enc_addr(A1) + u(0)),
    ('TIP-20 pathUSD transfer of 1 to a zone-style deposit address (bytes 4..12 = 0xFC)', PATHUSD,
     sel('transfer(address,uint256)').to_bytes(4, 'big') + enc_addr(int('11223344' + 'fc' * 8 + '00' * 8, 16)) + u(1)),
    ('fee manager setUserToken(pathUSD)', 0xfeec000000000000000000000000000000000000, sel('setUserToken(address)').to_bytes(4, 'big') + enc_addr(PATHUSD)),
    ('fee manager userTokens', 0xfeec000000000000000000000000000000000000, sel('userTokens(address)').to_bytes(4, 'big') + enc_addr(STUB)),
    ('nonce getNonce', 0x4E4F4E4345000000000000000000000000000000, sel('getNonce(address,uint256)').to_bytes(4, 'big') + enc_addr(STUB) + u(1)),
    ('keychain getTransactionKey', 0xAAAAAAAA00000000000000000000000000000000, sel('getTransactionKey()').to_bytes(4, 'big')),
    ('keychain revokeKey (state path)', 0xAAAAAAAA00000000000000000000000000000000, sel('revokeKey(address)').to_bytes(4, 'big') + enc_addr(A1)),
    ('storage credits setBudget (state write)', 0x1060000000000000000000000000000000000000, sel('setBudget(uint64)').to_bytes(4, 'big') + u(5)),
    ('storage credits balanceOf', 0x1060000000000000000000000000000000000000, sel('balanceOf(address)').to_bytes(4, 'big') + enc_addr(STUB)),
    ('stablecoin DEX withdraw without balance', 0xdec0000000000000000000000000000000000000, sel('withdraw(address,uint128)').to_bytes(4, 'big') + enc_addr(PATHUSD) + u(1)),
    ('stablecoin DEX nextOrderId', 0xdec0000000000000000000000000000000000000, sel('nextOrderId()').to_bytes(4, 'big')),
    ('channel reserve getChannelState', 0x4D50500000000000000000000000000000000000, sel('getChannelState(bytes32)').to_bytes(4, 'big') + u(0)),
    ('TIP-403 registry junk call', 0x403C000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('address registry junk call', 0xFDC0000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('signature verifier junk call', 0x5165300000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('receive policy guard junk call', 0xB10C000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('configurable account junk call', 0xAACC000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('zone factory junk call', 0x5AF2000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('TIP-20 factory junk call', 0x20FC000000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('current committee junk call', 0xC077E00000000000000000000000000000000000, b'\x01\x02\x03\x04'),
    ('validator config v2 junk call', 0xCCCCCCCC00000000000000000000000000000001, b'\x01\x02\x03\x04'),
    ('precompile 0x01 ecrecover', 0x01, b'\x00' * 128),
    ('precompile 0x100 p256verify', 0x100, b'\x00' * 160),
]

SSTORER_CODE = assemble([('PUSH', 1), ('PUSH', 1), 'SSTORE', ('PUSH', 1), ('PUSH', 1), 'TSTORE', 'STOP'])


def run(t14):
    code = driver()
    ov = {evm.STUB: {'code': '0x' + code.hex()}, '0x%040x' % SSTORER: {'code': '0x' + SSTORER_CODE.hex()}}
    out = []
    for name, target, data in PROBES:
        cd = '0x' + (u(target) + data).hex()
        tx = {'from': '0x000000000000000000000000000000000000beef', 'to': evm.STUB, 'data': cd, 'gas': hex(20_000_000)}
        rec = {'probe': name, 'target': hex(target), 'calldata': cd, 'mode': 'T14 simulate' if t14 else 'eth_call latest'}
        try:
            if t14:
                r = evm.rpc(URL, 'eth_simulateV1', [{'blockStateCalls': [{'calls': [tx], 'blockOverrides': {'time': hex(T14)}, 'stateOverrides': ov}], 'validation': False}, 'latest'])
                b = r[0]; rec['blockTime'] = int(b['timestamp'], 16); c = b['calls'][0]
                rec['status'] = c.get('status'); ret = c.get('returnData', '0x')
            else:
                ret = evm.rpc(URL, 'eth_call', [tx, 'latest', ov])
        except Exception as e:
            rec['error'] = str(e)[:400]; out.append(rec); continue
        raw = bytes.fromhex(ret[2:])
        rec['raw'] = ret
        if len(raw) != 17 * 32:
            rec['unexpected'] = True; out.append(rec); continue
        w = [int.from_bytes(raw[i * 32:(i + 1) * 32], 'big') for i in range(17)]
        names = ['lock', 'nonzeroCount', 'syncedCurrency', 'syncedReserves', 'delta']
        rec['atCallbackStart'] = dict(zip(names, [hex(x) for x in w[0:5]]))
        rec['afterOpen'] = dict(zip(names, [hex(x) for x in w[5:10]]))
        rec['probeSuccess'] = w[10]; rec['probeReturnSize'] = w[11]
        rec['afterProbe'] = dict(zip(names, [hex(x) for x in w[12:17]]))
        rec['changedByProbe'] = [n for n, a, b2 in zip(names, w[5:10], w[12:17]) if a != b2]
        out.append(rec)
    return out


if __name__ == '__main__':
    path = sys.argv[1]
    t14 = len(sys.argv) > 2 and sys.argv[2] == 't14'
    cv0 = evm.rpc(URL, 'web3_clientVersion', [])
    bn0 = evm.rpc(URL, 'eth_blockNumber', [])
    res = run(t14)
    cv1 = evm.rpc(URL, 'web3_clientVersion', [])
    json.dump({'endpoint': URL, 'clientVersionBefore': cv0, 'clientVersionAfter': cv1, 'blockAtStart': bn0,
               'driverCode': driver().hex(), 'sstorerCode': SSTORER_CODE.hex(), 'deltaSlot': hex(DELTA),
               'results': res}, open(path, 'w'), indent=1)
    for r in res:
        print(r['probe'][:60].ljust(60), r.get('status', ''), r.get('probeSuccess'), r.get('changedByProbe'), r.get('error', '')[:120], 'UNEXPECTED' if r.get('unexpected') else '')
