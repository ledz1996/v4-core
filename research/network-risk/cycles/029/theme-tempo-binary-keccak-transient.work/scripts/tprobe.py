"""Read-only eth_call probes of transient storage on keccak-derived slots on Tempo (and Ethereum for comparison).

Part A runs the deployed PoolManager of the network (real code, real state) under a driver placed by state
override: in one unlock callback it mints ERC-6909 ids for two currencies, which books two CurrencyDelta
slots for (driver, C0) and (driver, C1), reads both with exttload, reads NonzeroDeltaCount, reads the slot of
another target for the same currency, burns one id and reads again. The callback then reverts with the buffer.

Part B is a probe contract with no PoolManager: it writes keccak(t1,c1) and keccak(t2,c2) for pairs that are
swapped or differ in one bit, runs a child frame that overwrites them and reverts, a child frame that writes
and returns, and reads everything back.

usage: python3 -I tprobe.py <out.json> <chainId> [...]
"""
import json, sys, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, keccak, rpc, MASK
import pmdiff as P

OUT = sys.argv[1]
CHAINS = [int(x) for x in sys.argv[2:]]
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
DRV = 0x00000000000000000000000000000000d21fe001
OTHER = 0x00000000000000000000000000000000d21fe002
C0, C1 = P.C0, P.C1
def w(x): return (x & MASK).to_bytes(32, 'big')
def dslot(t, c): return int.from_bytes(keccak(w(t) + w(c)), 'big')


def driver_for(pm):
    P.PM = pm
    return P.driver()


def part_a_script():
    calls = [P.S_MINT + w(DRV) + w(C0) + w(5),
             P.S_MINT + w(DRV) + w(C1) + w(7),
             P.S_EXTTLOAD + w(dslot(DRV, C0)),
             P.S_EXTTLOAD + w(dslot(DRV, C1)),
             P.S_EXTTLOAD + w(NZDC),
             P.S_EXTTLOAD + w(dslot(OTHER, C0)),
             P.S_EXTTLOAD + w(dslot(C0, DRV)),
             P.S_BURN + w(DRV) + w(C0) + w(5),
             P.S_EXTTLOAD + w(dslot(DRV, C0)),
             P.S_EXTTLOAD + w(dslot(DRV, C1)),
             P.S_EXTTLOAD + w(NZDC)]
    body = b''.join(len(c).to_bytes(2, 'big') + c for c in calls) + b'\0\0'
    return body


def part_a_expect():
    vals = [None, None, -5, -7, 2, 0, 0, None, 0, -7, 1]
    return vals


def parse_buffer(buf):
    out, p = [], 0
    while p + 64 <= len(buf):
        ok = int.from_bytes(buf[p:p + 32], 'big'); n = int.from_bytes(buf[p + 32:p + 64], 'big')
        out.append((ok, buf[p + 64:p + 64 + n])); p += 64 + n
    return out


# Part B probe. calldata word 0 = mode: 0 top, 1 child that writes and reverts, 2 child that writes and returns
T1, C1b = 0x1111111111111111111111111111111111111111, 0x2222222222222222222222222222222222222222
PAIRS = [(T1, C1b), (C1b, T1), (T1 ^ 1, C1b), (T1, C1b ^ (1 << 159))]
SL = [dslot(t, c) for t, c in PAIRS]


def probe():
    def kslot(t, c):  # mstore(0,t) mstore(32,c) keccak256(0,64), as CurrencyDelta._computeSlot does
        return [('PUSHN', 20, t), ('PUSH', 0), 'MSTORE', ('PUSHN', 20, c), ('PUSH', 32), 'MSTORE', ('PUSH', 64), ('PUSH', 0), 'KECCAK256']
    p = [('PUSH', 0), 'CALLDATALOAD', 'DUP1', ('PUSH', 1), 'EQ', ('REF', 'c1'), 'JUMPI', 'DUP1', ('PUSH', 2), 'EQ', ('REF', 'c2'), 'JUMPI', 'POP']
    # top: write v=0xA1.. at slot0 and 0xB2.. at slot1 (computed in-code)
    p += [('PUSHN', 32, 0xA1 << 248 | 1)] + kslot(*PAIRS[0]) + ['TSTORE']
    p += [('PUSHN', 32, 0xB2 << 248 | 2)] + kslot(*PAIRS[1]) + ['TSTORE']
    # child 1 (reverts)
    p += [('PUSH', 1), ('PUSH', 0), 'MSTORE', ('PUSH', 0), ('PUSH', 0), ('PUSH', 32), ('PUSH', 0), ('PUSH', 0), 'ADDRESS', 'GAS', 'CALL', ('PUSH', 0x300), 'MSTORE']
    # child 2 (returns)
    p += [('PUSH', 2), ('PUSH', 0), 'MSTORE', ('PUSH', 0), ('PUSH', 0), ('PUSH', 32), ('PUSH', 0), ('PUSH', 0), 'ADDRESS', 'GAS', 'CALL', ('PUSH', 0x320), 'MSTORE']
    for i, s in enumerate(SL):
        p += [('PUSHN', 32, s), 'TLOAD', ('PUSH', 0x100 + 32 * i), 'MSTORE']
    p += [('PUSH', 0xC0), ('PUSH', 0x100), 'RETURN'] if False else [('PUSH', 0x240), ('PUSH', 0x100), 'RETURN']
    # child 1: overwrite slot0, slot1, write slot2, then revert
    p += [('LABEL', 'c1'), 'POP', ('PUSHN', 32, 0xC3)] + kslot(*PAIRS[0]) + ['TSTORE', ('PUSH', 0)] + kslot(*PAIRS[1]) + ['TSTORE',
          ('PUSHN', 32, 0xC4)] + kslot(*PAIRS[2]) + ['TSTORE', ('PUSH', 0), ('PUSH', 0), 'REVERT']
    # child 2: write slot3 and zero nothing, return
    p += [('LABEL', 'c2'), 'POP', ('PUSHN', 32, 0xD5)] + kslot(*PAIRS[3]) + ['TSTORE', 'STOP']
    return assemble(p)


def expect_b():
    # words at 0x100..: slot0..3, then 0x300 is at offset 0x200 (child1 ok=0), 0x320 at 0x220 (child2 ok=1)
    return {'slot0': 0xA1 << 248 | 1, 'slot1': 0xB2 << 248 | 2, 'slot2': 0, 'slot3': 0xD5, 'child1ok': 0, 'child2ok': 1}


def eth_call(url, to, data, code_over, frm=None):
    tx = {'to': to, 'data': '0x' + data.hex(), 'gas': hex(30_000_000)}
    if frm: tx['from'] = frm
    return rpc(url, 'eth_call', [tx, 'latest', code_over])


res = {'runs': [], 'pairs': [[hex(t), hex(c)] for t, c in PAIRS], 'slots': [hex(s) for s in SL]}
for cid in CHAINS:
    n = nets[cid]; url = n['rpc']; pm = n['poolManager']
    r = {'chainId': cid, 'rpc': url, 'clientVersionStart': None}
    try:
        r['clientVersionStart'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e:
        r['clientVersionStart'] = 'error: ' + str(e)[:200]
    r['block'] = int(rpc(url, 'eth_blockNumber', []), 16)
    drv = driver_for(pm)
    over = {'0x%040x' % DRV: {'code': '0x' + drv.hex()}}
    try:
        out = eth_call(url, '0x%040x' % DRV, part_a_script(), over)
        buf = bytes.fromhex(out[2:])
        items = parse_buffer(buf)
        got = []
        for (ok, data), want in zip(items, part_a_expect()):
            v = int.from_bytes(data[:32], 'big') if len(data) >= 32 else None
            sv = v - (1 << 256) if v is not None and v >> 255 else v
            got.append({'ok': ok, 'value': sv, 'want': want, 'match': want is None or sv == want})
        r['partA'] = {'raw': out, 'items': got, 'allMatch': all(g['match'] for g in got) and len(got) == len(part_a_expect()) and all(g['ok'] == 1 for g in got)}
    except Exception as e:
        r['partA'] = {'error': str(e)[:400]}
    PROBE = 0x00000000000000000000000000000000abcd0029
    try:
        out = eth_call(url, '0x%040x' % PROBE, w(0), {'0x%040x' % PROBE: {'code': '0x' + probe().hex()}})
        b = bytes.fromhex(out[2:])
        wd = [int.from_bytes(b[32 * i:32 * i + 32], 'big') for i in range(len(b) // 32)]
        got = {'slot0': wd[0], 'slot1': wd[1], 'slot2': wd[2], 'slot3': wd[3], 'child1ok': wd[16], 'child2ok': wd[17]}
        r['partB'] = {'raw': out, 'got': {k: hex(v) for k, v in got.items()}, 'allMatch': got == expect_b()}
    except Exception as e:
        r['partB'] = {'error': str(e)[:400]}
    try:
        r['clientVersionEnd'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e:
        r['clientVersionEnd'] = 'error: ' + str(e)[:200]
    r['timeUtc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    res['runs'].append(r)
    print(cid, r['clientVersionStart'], 'A', r['partA'].get('allMatch', r['partA']), 'B', r['partB'].get('allMatch', r['partB']))
json.dump(res, open(OUT, 'w'), indent=1)
