"""theme-blind-read Step 4 probe C, read-only (one eth_call with a state override per network; nothing is sent).

Against the real PoolManager code at its real address:
 1. STATICCALL PoolManager.sync(X) must fail, because sync only writes transient storage (src/PoolManager.sol:279-288,
    src/libraries/CurrencyReserves.sol:27-31) and TSTORE is forbidden in a static context (EIP-1153). The CURRENCY slot
    must still read 0 afterwards. Earlier call tests wrote TSTORE and SSTORE together, so they could not show TSTORE alone.
 2. A plain CALL to sync(X) outside unlock succeeds and the slot reads X; sync(address(0)) resets it.
 3. A sub-frame that runs unlock, syncs inside the callback and then reverts (mode 3) or halts with INVALID (mode 2)
    must leave CURRENCY and IS_UNLOCKED at 0 for the rest of the same transaction.
This also reaches the five networks whose endpoints have no eth_simulateV1. No randomness (no seed).
Usage: python3 static_rollback.py <out.json> [chainId ...]
"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, rpc
from xtx import driver, TOKEN, SLOTS, sel, D, X, FROM, A, NET

PR = 0x00000000000000000000000000000000b11d0d03


def probe(pm):
    P = lambda v: ('PUSH', v); p = []; labels = []; exp = []
    def out(l, e): p.extend([P(0x400 + 32 * len(labels)), 'MSTORE']); labels.append(l); exp.append(e)
    def sync(addr, op):
        p.extend([P(sel('sync(address)') << 224), P(0), 'MSTORE', ('PUSHN', 20, addr), P(4), 'MSTORE', P(0), P(0), P(0x24), P(0)])
        if op == 'CALL': p.append(P(0))
        p.extend([('PUSHN', 20, pm), P(500_000), op])   # fixed allowance: a failing static frame burns what it is given
    def tl(slot):
        p.extend([P(0), P(0x20), 'MSTORE', P(sel('exttload(bytes32)') << 224), P(0), 'MSTORE', P(slot), P(4), 'MSTORE',
                  P(0x20), P(0x20), P(0x24), P(0), ('PUSHN', 20, pm), P(200_000), 'STATICCALL', 'POP', P(0x20), 'MLOAD'])
    def drv(m):
        p.extend([P(m), P(0), 'MSTORE', P(0), P(0), P(0x20), P(0), P(0), ('PUSHN', 20, D), P(1_500_000), 'CALL'])
    sync(X, 'STATICCALL'); out('staticcall sync(X) fails', 0); tl(SLOTS['CURRENCY']); out('CURRENCY after static sync', 0)
    tl(SLOTS['RESERVES_OF']); out('RESERVES_OF after static sync', 0)
    sync(X, 'CALL'); out('call sync(X) succeeds', 1); tl(SLOTS['CURRENCY']); out('CURRENCY after sync(X)', X)
    tl(SLOTS['RESERVES_OF']); out('RESERVES_OF after sync(X)', 7)
    sync(0, 'CALL'); out('call sync(0) succeeds', 1); tl(SLOTS['CURRENCY']); out('CURRENCY after sync(0)', 0)
    drv(3); out('sub-frame unlock, sync in callback, REVERT: fails', 0)
    tl(SLOTS['CURRENCY']); out('CURRENCY after reverted frame', 0); tl(SLOTS['IS_UNLOCKED']); out('IS_UNLOCKED after reverted frame', 0)
    drv(2); out('sub-frame unlock, sync in callback, INVALID: fails', 0)
    tl(SLOTS['CURRENCY']); out('CURRENCY after INVALID frame', 0); tl(SLOTS['IS_UNLOCKED']); out('IS_UNLOCKED after INVALID frame', 0)
    tl(SLOTS['NONZERO_DELTA_COUNT']); out('NONZERO_DELTA_COUNT at end', 0)
    drv(1); out('sub-frame unlock with sync in callback completes', 1)
    tl(SLOTS['CURRENCY']); out('CURRENCY after completed unlock (sync left set, by design)', X); tl(SLOTS['IS_UNLOCKED']); out('IS_UNLOCKED after completed unlock', 0)
    p.extend([P(32 * len(labels)), P(0x400), 'RETURN'])
    return assemble(p), labels, exp


def run(n):
    cid, pm = n['chainId'], int(n['poolManager'], 16)
    url = json.loads(os.environ.get('XTX_RPC', '{}')).get(str(cid), n['rpc'])
    code, labels, exp = probe(pm); rec = {'name': n['name'], 'rpc': url, 'poolManager': n['poolManager']}
    try: rec['clientBefore'] = rpc(url, 'web3_clientVersion', [], timeout=30)
    except Exception as e: rec['clientBefore'] = 'ERR ' + str(e)[:150]
    ov = {A(PR): {'code': '0x' + code.hex()}, A(D): {'code': '0x' + driver(pm).hex()}, A(X): {'code': '0x' + TOKEN.hex()}}
    got = None
    for k in range(4):
        try:
            r = bytes.fromhex(rpc(url, 'eth_call', [{'from': A(FROM), 'to': A(PR), 'gas': hex(10_000_000)}, 'latest', ov], timeout=60)[2:])
            got = [int.from_bytes(r[32 * i:32 * i + 32], 'big') for i in range(len(labels))]; break
        except Exception as e:
            rec['error'] = str(e)[:300]; time.sleep(3 * (k + 1))
    rec['got'] = None if got is None else [hex(g) for g in got]
    rec['different'] = None if got is None else [{'test': labels[i], 'expected': hex(exp[i]), 'got': hex(got[i])} for i in range(len(labels)) if got[i] != exp[i]]
    try: rec['clientAfter'] = rpc(url, 'web3_clientVersion', [], timeout=30)
    except Exception as e: rec['clientAfter'] = 'ERR ' + str(e)[:150]
    return cid, rec, labels, exp


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:])); res = {}; L = E = None
    with cf.ThreadPoolExecutor(7) as ex:
        for cid, rec, L, E in ex.map(run, [n for n in NET if not only or n['chainId'] in only]):
            res[cid] = rec; d = rec['different']
            print(f"{cid:>8} {rec['name']:16} {'ERR ' + rec.get('error', '') if d is None else str(len(L) - len(d)) + '/' + str(len(L)) + ' as specified'} | {rec['clientBefore'][:40]}", flush=True)
            for x in d or []: print('            ', x)
    json.dump({'tests': L, 'expected': [hex(e) for e in E], 'results': res}, open(out, 'w'), indent=1)
