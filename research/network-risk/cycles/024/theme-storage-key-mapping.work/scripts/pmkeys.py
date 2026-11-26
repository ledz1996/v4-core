"""Task 4 of theme-storage-key-mapping: storage and transient key pairs read at the real PoolManager address.

One eth_call per network, read-only. A probe Q (placed by state override at an unused address) calls
PoolManager.unlock with the calldata of exttload(bytes32[] L). In the callback Q calls mint(Q, X, 5) (transient
delta slot and nonzero count, persistent ERC-6909 balance), sync(C) for a stub token C that answers balanceOf with
0x77 (transient currency and reserves slots), then exttload(L) and extsload(L), then burn(Q, X, 5) so the unlock
settles, and returns both arrays. Before the call, a stateDiff override on the PoolManager writes a marker value
into the persistent slot of every index of L except the ERC-6909 balance of Q and the fixed slots 0 and 6, so a
persistent and a transient slot with one index hold different values. L holds the five transient slots the
PoolManager writes, a balance slot, a pool state slot and its +6 offset, slots 0 and 6, and each of these with bit
248 flipped (the Avalanche fold of F-040).

Usage: python3 pmkeys.py <out.json> [chainId ...]
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, keccak, rpc  # noqa: E402

NET = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'state', 'networks.json')
M = (1 << 256) - 1
B248 = 1 << 248
Q = 0x00000000000000000000000000000000c0ffee24
C = 0x00000000000000000000000000000000c0ffee25
X = 0x0000000000000000000000000000000000001234  # ERC-6909 id = currency address 0x1234


def sel(sig):
    return int.from_bytes(keccak(sig.encode())[:4], 'big')


def h(*words):
    return int.from_bytes(keccak(b''.join(w.to_bytes(32, 'big') for w in words)), 'big')


LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
NZ = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
RES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
D = h(Q, X)                      # CurrencyDelta._computeSlot(Q, X)
BAL = h(X, h(Q, 4))              # balanceOf[Q][X], mapping at slot 4
POOLID = h(0xabc)                # synthetic pool id
P0 = h(POOLID, 6)                # _pools[id] slot 0 (slot0 word)
TRANS = [LOCK, NZ, CUR, RES, D]
BASE = TRANS + [BAL, P0, (P0 + 6) & M, 0, 6]
L = []
for s_ in BASE:
    L += [s_, s_ ^ B248]
NOOVR = {BAL, 0, 6}


def marker(i):
    return 0xA0A0 << 128 | i + 1


def probe(pm):
    P = pm
    def call_p(selector, args, gasless=False):
        # mem[0..] = selector ++ args; CALL(gas, P, 0, 0, 4+32n, 0, 0); revert with returndata on failure
        prog = [('PUSH', selector << 224), ('PUSH', 0), 'MSTORE']
        for k, a in enumerate(args):
            prog += a + [('PUSH', 4 + 32 * k), 'MSTORE']
        prog += [('PUSH', 0), ('PUSH', 0), ('PUSH', 4 + 32 * len(args)), ('PUSH', 0), ('PUSH', 0), ('PUSH', P), 'GAS',
                 'CALL', ('REF', f'ok{selector}'), 'JUMPI', ('REF', 'fail'), 'JUMP', ('LABEL', f'ok{selector}')]
        return prog
    lit = lambda v: [('PUSH', v)]
    prog = [('PUSH', P), 'CALLER', 'EQ', ('REF', 'cb'), 'JUMPI']
    # top level: unlock(bytes calldata)
    prog += [('PUSH', sel('unlock(bytes)') << 224), ('PUSH', 0), 'MSTORE', ('PUSH', 0x20), ('PUSH', 4), 'MSTORE',
             'CALLDATASIZE', ('PUSH', 0x24), 'MSTORE', 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0x44), 'CALLDATACOPY',
             ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0x44 + 28), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSH', P),
             'GAS', 'CALL', ('REF', 'topok'), 'JUMPI', ('REF', 'fail'), 'JUMP', ('LABEL', 'topok'),
             'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN']
    prog += [('LABEL', 'fail'), 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE',
             ('PUSH', 0), 'REVERT']
    # callback: unlockCallback(bytes data); data at calldata 0x44, length at 0x24
    prog += [('LABEL', 'cb'), ('PUSH', 0x24), 'CALLDATALOAD', ('PUSH', 0x44), ('PUSH', 0x1000), 'CALLDATACOPY']
    prog += call_p(sel('mint(address,uint256,uint256)'), [lit(Q), lit(X), lit(5)])
    prog += call_p(sel('sync(address)'), [lit(C)])
    n = 0x40 + 32 * len(L)
    R = 0x8000
    for k, newsel in enumerate([None, sel('extsload(bytes32[])')]):
        if newsel is not None:
            prog += [('PUSH', 0x1000), 'MLOAD', ('PUSH', (1 << 224) - 1), 'AND', ('PUSH', newsel << 224), 'OR',
                     ('PUSH', 0x1000), 'MSTORE']
        prog += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0x24), 'CALLDATALOAD', ('PUSH', 0x1000), ('PUSH', P), 'GAS',
                 'STATICCALL', ('REF', f'sok{k}'), 'JUMPI', ('REF', 'fail'), 'JUMP', ('LABEL', f'sok{k}'),
                 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', R + k * n), 'RETURNDATACOPY']
    prog += call_p(sel('burn(address,uint256,uint256)'), [lit(Q), lit(X), lit(5)])
    prog += [('PUSH', 0x20), ('PUSH', R - 0x40), 'MSTORE', ('PUSH', 2 * n), ('PUSH', R - 0x20), 'MSTORE',
             ('PUSH', 0x40 + 2 * n), ('PUSH', R - 0x40), 'RETURN']
    return assemble(prog)


TOKEN = assemble([('PUSH', 0x77), ('PUSH', 0), 'MSTORE', ('PUSH', 0x20), ('PUSH', 0), 'RETURN'])


def run(n):
    pm = int(n['poolManager'], 16)
    code = probe(pm)
    data = sel('exttload(bytes32[])').to_bytes(4, 'big') + (0x20).to_bytes(32, 'big') + len(L).to_bytes(32, 'big') + \
        b''.join(x.to_bytes(32, 'big') for x in L)
    diff = {'0x%064x' % s_: '0x%064x' % marker(i) for i, s_ in enumerate(L) if s_ not in NOOVR}
    ovr = {'0x%040x' % Q: {'code': '0x' + code.hex()}, '0x%040x' % C: {'code': '0x' + TOKEN.hex()},
           n['poolManager']: {'stateDiff': diff}}
    rec = {'chainId': n['chainId'], 'name': n['name'], 'rpc': n['rpc']}
    try:
        rec['clientBefore'] = rpc(n['rpc'], 'web3_clientVersion', [])
    except Exception as e:  # noqa
        rec['clientBefore'] = 'error: ' + str(e)[:200]
    try:
        blk = rpc(n['rpc'], 'eth_blockNumber', [])
        rec['block'] = int(blk, 16)
        out = None
        for k in range(4):
            try:
                out = rpc(n['rpc'], 'eth_call', [{'from': '0x%040x' % 0xa11ce, 'to': '0x%040x' % Q, 'data': '0x' + data.hex(),
                                                   'gas': hex(20_000_000)}, blk, ovr], timeout=90)
                break
            except Exception as e:  # noqa
                last = e; time.sleep(2 * (k + 1))
        if out is None:
            raise last
        raw = bytes.fromhex(out[2:])
        # unlock returns abi.encode(bytes); bytes = exttload result (n) ++ extsload result (n)
        ln = int.from_bytes(raw[32:64], 'big'); body = raw[64:64 + ln]
        nn = 0x40 + 32 * len(L)
        words = lambda b: [int.from_bytes(b[0x40 + 32 * i:0x60 + 32 * i], 'big') for i in range(len(L))]
        t, p = words(body[:nn]), words(body[nn:2 * nn])
        owner = int(rpc(n['rpc'], 'eth_getStorageAt', [n['poolManager'], '0x0', blk]), 16)
        exp_t = {LOCK: 1, NZ: 1, CUR: C, RES: 0x77, D: (-5) & M}
        rows = []; mism = []
        for i, s_ in enumerate(L):
            et = exp_t.get(s_, 0)
            ep = marker(i) if s_ not in NOOVR else {BAL: 5, 0: owner, 6: None}[s_]
            row = {'slot': '0x%064x' % s_, 'tload': hex(t[i]), 'sload': hex(p[i]), 'expectT': hex(et),
                   'expectS': None if ep is None else hex(ep)}
            rows.append(row)
            if t[i] != et or (ep is not None and p[i] != ep):
                mism.append(row)
        rec.update(rows=rows, mismatches=mism, ok=not mism)
    except Exception as e:  # noqa
        rec['error'] = str(e)[:400]
    try:
        rec['clientAfter'] = rpc(n['rpc'], 'web3_clientVersion', [])
    except Exception as e:  # noqa
        rec['clientAfter'] = 'error: ' + str(e)[:200]
    rec['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    return rec


if __name__ == '__main__':
    nets = json.load(open(NET))['networks']
    want = set(int(x) for x in sys.argv[2:])
    res = []
    for n in nets:
        if want and n['chainId'] not in want:
            continue
        r = run(n)
        print(r['chainId'], r['name'], r.get('block'), r.get('ok'), r.get('error', ''), r['clientBefore'][:70],
              [m['slot'][:12] + ' t=' + m['tload'] + ' s=' + m['sload'] for m in r.get('mismatches', [])][:6], flush=True)
        res.append(r)
    json.dump({'slots': ['0x%064x' % x for x in L], 'Q': hex(Q), 'C': hex(C), 'X': hex(X), 'results': res},
              open(sys.argv[1], 'w'), indent=1)
