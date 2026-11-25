"""theme-blind-read Step 4 probes, read-only (eth_simulateV1 and eth_call with state overrides; nothing is sent).

Probe A (assumption T3, ranked 1): do the PoolManager's transient slots written in one transaction survive into the
next transaction of the same simulated block, after a transaction that (1) succeeds with a synced currency left set,
(2) halts with INVALID inside and outside the callback, (3) reverts, (4) completes unlock and then halts with INVALID?
Runs against the real PoolManager code at its real address. A driver D (state override) calls unlock; in the callback
it calls sync(X) where X is a stub token answering 7, which writes CURRENCY_SLOT and RESERVES_OF_SLOT.
Probe B (assumption C5, ranked 3): does a top-level call with value from an account with zero balance fail.
No randomness is used (no seed).
Usage: python3 xtx.py <out.json> [chainId ...]
"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, rpc, keccak

NET = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'state', 'networks.json')))['networks']
D = 0x00000000000000000000000000000000b11d0d01
X = 0x00000000000000000000000000000000b11d0d02
FROM = 0x00000000000000000000000000000000b11d0e01   # never used on chain, zero balance
EMPTY = 0x00000000000000000000000000000000b11d0e02
A = lambda x: '0x%040x' % x
sel = lambda s: int.from_bytes(keccak(s.encode())[:4], 'big')
SLOTS = {'IS_UNLOCKED': 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23,   # src/libraries/Lock.sol:8
         'NONZERO_DELTA_COUNT': 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b,  # NonzeroDeltaCount.sol:9-10
         'RESERVES_OF': 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95,  # CurrencyReserves.sol:11
         'CURRENCY': 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9}     # CurrencyReserves.sol:13
assert keccak(b'Unlocked') and int.from_bytes(keccak(b'Unlocked'), 'big') - 1 == SLOTS['IS_UNLOCKED']
assert int.from_bytes(keccak(b'Currency'), 'big') - 1 == SLOTS['CURRENCY']


def driver(pm):
    P = lambda v: ('PUSH', v)
    return assemble([
        'CALLER', ('PUSHN', 20, pm), 'EQ', ('REF', 'cb'), 'JUMPI',
        P(0), 'CALLDATALOAD', 'DUP1', 'ISZERO', ('REF', 'm0'), 'JUMPI',
        'DUP1', P(0), 'TSTORE',
        P(sel('unlock(bytes)') << 224), P(0), 'MSTORE', P(0x20), P(4), 'MSTORE', P(0), P(0x24), 'MSTORE',
        P(0), P(0), P(0x44), P(0), P(0), ('PUSHN', 20, pm), 'GAS', 'CALL',
        'ISZERO', ('REF', 'fail'), 'JUMPI',
        'DUP1', P(4), 'EQ', ('REF', 'inv'), 'JUMPI',
        P(sel('exttload(bytes32)') << 224), P(0), 'MSTORE', P(SLOTS['CURRENCY']), P(4), 'MSTORE',
        P(0x20), P(0), P(0x24), P(0), ('PUSHN', 20, pm), 'GAS', 'STATICCALL', 'POP', P(0x20), P(0), 'RETURN',
        ('LABEL', 'fail'), 'DUP1', P(3), 'EQ', ('REF', 'rev'), 'JUMPI', 'INVALID',
        ('LABEL', 'm0'), P(0), 'TLOAD', P(0), 'MSTORE', P(0x20), P(0), 'RETURN',
        ('LABEL', 'cb'),
        P(sel('sync(address)') << 224), P(0), 'MSTORE', ('PUSHN', 20, X), P(4), 'MSTORE',
        P(0), P(0), P(0x24), P(0), P(0), ('PUSHN', 20, pm), 'GAS', 'CALL', 'POP',
        P(0), 'TLOAD', 'DUP1', P(2), 'EQ', ('REF', 'inv'), 'JUMPI', 'DUP1', P(3), 'EQ', ('REF', 'rev'), 'JUMPI',
        P(0x20), P(0), 'MSTORE', P(0), P(0x20), 'MSTORE', P(0x40), P(0), 'RETURN',
        ('LABEL', 'inv'), 'INVALID',
        ('LABEL', 'rev'), P(0), P(0), 'REVERT'])


TOKEN = bytes.fromhex('6007600052602060' + '00f3')
READ = (sel('exttload(bytes32[])').to_bytes(4, 'big') + (0x20).to_bytes(32, 'big') + len(SLOTS).to_bytes(32, 'big')
        + b''.join(v.to_bytes(32, 'big') for v in SLOTS.values())).hex()


def mode(m): return '0x' + m.to_bytes(32, 'big').hex()


def run(n):
    cid, pm = n['chainId'], int(n['poolManager'], 16)
    url = json.loads(os.environ.get('XTX_RPC', '{}')).get(str(cid), n['rpc'])
    rec = {'name': n['name'], 'poolManager': n['poolManager'], 'rpc': url}
    try: rec['clientBefore'] = rpc(url, 'web3_clientVersion', [], timeout=30)
    except Exception as e: rec['clientBefore'] = 'ERR ' + str(e)[:150]
    ov = {A(D): {'code': '0x' + driver(pm).hex()}, A(X): {'code': '0x' + TOKEN.hex()}}
    plan = [('D mode1: unlock, sync(X) in callback, success', 'D', 1), ('read PM transient', 'R', 0), ('read D tload(0)', 'D', 0),
            ('D mode2: sync then INVALID in callback and at top', 'D', 2), ('read PM transient', 'R', 0), ('read D tload(0)', 'D', 0),
            ('D mode3: sync then REVERT in callback and at top', 'D', 3), ('read PM transient', 'R', 0), ('read D tload(0)', 'D', 0),
            ('D mode4: unlock completes, then INVALID at top', 'D', 4), ('read PM transient', 'R', 0), ('read D tload(0)', 'D', 0)]
    calls = []
    for lab, k, m in plan:
        if k == 'D': calls.append({'from': A(FROM), 'to': A(D), 'data': mode(m), 'gas': hex(2_000_000)})
        else: calls.append({'from': A(FROM), 'to': n['poolManager'], 'data': '0x' + READ, 'gas': hex(500_000)})
    blocks = [{'stateOverrides': ov, 'calls': calls},
              {'calls': [{'from': A(FROM), 'to': n['poolManager'], 'data': '0x' + READ, 'gas': hex(500_000)}, {'from': A(FROM), 'to': A(D), 'data': mode(0), 'gas': hex(500_000)}]}]
    res = None
    for k in range(3):
        try:
            res = rpc(url, 'eth_simulateV1', [{'blockStateCalls': blocks, 'validation': False}, 'latest'], timeout=90); break
        except Exception as e:
            res = 'ERR ' + str(e)[:300]; time.sleep(2 * (k + 1))
    rec['simulateRaw'] = res
    if isinstance(res, list):
        labs = [p[0] for p in plan] + ['next block: read PM transient', 'next block: read D tload(0)']
        cs = res[0]['calls'] + res[1]['calls']
        rec['simulate'] = [{'step': labs[i], 'status': c.get('status'), 'returnData': c.get('returnData'), 'error': c.get('error')} for i, c in enumerate(cs)]
        bad = []
        for i, c in enumerate(cs):
            l = labs[i]; rd = c.get('returnData') or '0x'
            if l.startswith('D mode1'):
                ok = c.get('status') == '0x1' and int(rd, 16) == X
            elif l.startswith('D mode'):
                ok = c.get('status') == '0x0'
            elif 'read PM' in l:
                ok = c.get('status') == '0x1' and int(rd[2 + 128:] or '0', 16) == 0 and len(rd) == 2 + 64 * 6
            else:
                ok = c.get('status') == '0x1' and int(rd, 16) == 0
            if not ok: bad.append(l)
        rec['simulateUnexpected'] = bad
    # Probe B: top-level value from a zero-balance sender
    for lab, tx in [('value 1 wei from zero balance', {'from': A(FROM), 'to': A(EMPTY), 'value': '0x1'}),
                    ('value 1e18 from zero balance', {'from': A(FROM), 'to': A(EMPTY), 'value': hex(10 ** 18)})]:
        try:
            r = rpc(url, 'eth_call', [tx, 'latest'], timeout=30); rec[lab] = {'result': r, 'accepted': True}
        except Exception as e:
            rec[lab] = {'error': str(e)[:300], 'accepted': False}
    try: rec['balanceOfSender'] = rpc(url, 'eth_getBalance', [A(FROM), 'latest'], timeout=30)
    except Exception as e: rec['balanceOfSender'] = 'ERR ' + str(e)[:100]
    try: rec['clientAfter'] = rpc(url, 'web3_clientVersion', [], timeout=30)
    except Exception as e: rec['clientAfter'] = 'ERR ' + str(e)[:150]
    return cid, rec


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    results = {}
    with cf.ThreadPoolExecutor(7) as ex:
        for cid, rec in ex.map(run, [n for n in NET if not only or n['chainId'] in only]):
            results[cid] = rec
            s = rec.get('simulateUnexpected'); sr = rec['simulateRaw']
            print(f"{cid:>8} {rec['name']:16} sim={'ERR' if isinstance(sr, str) else ('ok' if not s else 'UNEXPECTED ' + str(s))}"
                  f" | v1wei={'accepted' if rec['value 1 wei from zero balance']['accepted'] else 'rejected'}"
                  f" v1e18={'accepted' if rec['value 1e18 from zero balance']['accepted'] else 'rejected'} | {rec['clientBefore'][:40]}", flush=True)
            if isinstance(sr, str): print('          ', sr[:200])
    json.dump(results, open(out, 'w'), indent=1)
