"""Third script set: the parts of the bytecode that pmdiff.py and pmdiff2.py never run.
It adds the owner and fee controller functions, protocol fees inside swaps and their
collection, the ERC-6909 transfer, approval and operator functions, the array forms
of extsload and exttload, settleFor, non-empty hook data, updateDynamicLPFee called by
a hook, and callbacks that return normally so that unlock finishes and its events
and storage writes stand.

Both currencies are token doubles here, so a script can pay what it owes. Scripts
that are meant to return are completed by the reference interpreter: it runs the
script, reads the two deltas it leaves, and the generator appends the payments and
claims that bring them to zero.

Every network's answer is compared with the reference interpreter's answer, not with
another node. Usage: python3 pmdiff3.py <out.json> [nScripts] [chainId ...]
"""
import sys, os, json, random, hashlib, time, concurrent.futures as cf
from evm import assemble, keccak, rpc, networks, MASK, u, s
import v4math as m
import pmdiff as P, pmdiff2 as Q
from pyevm import World, NAMES

T0, T1 = P.C0, Q.TOKEN  # both currencies carry the token double
HOOKS = [Q.HOOK_BASE | f for f in Q.HOOK_FLAGS]
PMI, DRV = int(P.PM, 16), int(P.DRV, 16)
OTHER = 0x000000000000000000000000000000000000A11CE
sel = P.sel
S = {k: sel(v) for k, v in {
    'owner': 'owner()', 'transferOwnership': 'transferOwnership(address)', 'pfc': 'protocolFeeController()',
    'setPfc': 'setProtocolFeeController(address)', 'setFee': f'setProtocolFee({P.KEY},uint24)',
    'collect': 'collectProtocolFees(address,address,uint256)', 'accrued': 'protocolFeesAccrued(address)',
    'transfer': 'transfer(address,uint256,uint256)', 'transferFrom': 'transferFrom(address,address,uint256,uint256)',
    'approve': 'approve(address,uint256,uint256)', 'setOperator': 'setOperator(address,bool)', 'allowance': 'allowance(address,address,uint256)',
    'isOperator': 'isOperator(address,address)', 'supports': 'supportsInterface(bytes4)', 'settleFor': 'settleFor(address)',
    'dyn': f'updateDynamicLPFee({P.KEY},uint24)', 'extN': 'extsload(bytes32,uint256)', 'extA': 'extsload(bytes32[])', 'exttA': 'exttload(bytes32[])'}.items()}
TSET = b'\x00\x00\x00\x02'
AUTO = 0xA0A0
BEFORE_SWAP = int.from_bytes(sel(f'beforeSwap(address,{P.KEY},(bool,int256,uint160),bytes)'), 'big')


def driver():
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(P.S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(P.S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PMI), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x2000), ('PUSH', 68),
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 96), 'SHR',
         'DUP2', ('PUSH', 20), 'ADD', 'CALLDATALOAD', ('PUSH', 240), 'SHR',
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP4', ('PUSH', 22), 'ADD', ('PUSH', 0), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), 'DUP7', 'GAS', 'CALL',
         'DUP5', 'MSTORE', 'RETURNDATASIZE', 'DUP5', ('PUSH', 32), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP6', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',
         'SWAP3', ('PUSH', 64), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP3',
         'SWAP1', 'POP', ('PUSH', 22), 'ADD', 'ADD', ('REF', 'loop'), 'JUMP',
         # the terminator names address 1 to return the record as abi encoded bytes, anything else to revert with it
         ('LABEL', 'end'), 'POP', ('PUSH', 1), 'EQ', ('REF', 'ret'), 'JUMPI',
         'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'REVERT',
         ('LABEL', 'ret'), 'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB',
         'DUP1', ('PUSH', 0x1fe0), 'MSTORE', ('PUSH', 0x20), ('PUSH', 0x1fc0), 'MSTORE',
         ('PUSH', 0x5f), 'ADD', ('PUSH', 0x1f), 'NOT', 'AND', ('PUSH', 0x1fc0), 'RETURN']
    return assemble(p)


def hook():
    """As pmdiff2's hook double, plus selector 3: forward the rest of the calldata to the PoolManager."""
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', 'DUP1', ('PUSH', 1), 'EQ', ('REF', 'set'), 'JUMPI',
         ('PUSH', 3), 'EQ', ('REF', 'fwd'), 'JUMPI',
         ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSH', 224), 'SHL', ('PUSH', 5), 'TLOAD', 'XOR', ('PUSH', 0), 'MSTORE',
         ('PUSH', 1), 'TLOAD', ('PUSH', 32), 'MSTORE', ('PUSH', 2), 'TLOAD', ('PUSH', 64), 'MSTORE',
         ('PUSH', 4), 'TLOAD', ('REF', 'rev'), 'JUMPI', ('PUSH', 3), 'TLOAD',
         # a configured length of AUTO means: the length the PoolManager expects, 96 bytes for beforeSwap and 64 for the others
         'DUP1', ('PUSHN', 2, AUTO), 'EQ', 'ISZERO', ('REF', 'plain'), 'JUMPI',
         'POP', ('PUSH', 64), ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, BEFORE_SWAP), 'EQ', ('PUSH', 32), 'MUL', 'ADD',
         ('LABEL', 'plain'), ('PUSH', 0), 'RETURN',
         ('LABEL', 'rev'), ('PUSH', 3), 'TLOAD', ('PUSH', 0), 'REVERT',
         ('LABEL', 'fwd'), ('PUSH', 4), 'CALLDATASIZE', 'SUB', 'DUP1', ('PUSH', 4), ('PUSH', 0), 'CALLDATACOPY',  # n
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PMI), 'GAS', 'CALL',  # ok, n
         'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'fok'), 'JUMPI', 'RETURNDATASIZE', ('PUSH', 0), 'REVERT',
         ('LABEL', 'fok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'set'), 'POP']
    for k in range(1, 6): p += [('PUSH', 4 + 32 * (k - 1)), 'CALLDATALOAD', ('PUSH', k), 'TSTORE']
    return assemble(p + ['STOP'])


def w(x): return (x & MASK).to_bytes(32, 'big')
def item(target, data): return target.to_bytes(20, 'big') + len(data).to_bytes(2, 'big') + data
def tail(b): return w(len(b)) + b + bytes(-len(b) % 32)


def codes(code):
    c = {PMI: code, DRV: driver(), T0: Q.token(), T1: Q.token()}
    for h in HOOKS: c[h] = hook()
    return c


def world(code):
    wd = World(codes(code), {PMI: 10 ** 19}); wd.storage[(PMI, 0)] = DRV  # the driver is the owner
    return wd


def overrides(code):
    ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19), 'stateDiff': {'0x' + '00' * 32: '0x' + DRV.to_bytes(32, 'big').hex()}}}
    for a, c in codes(code).items():
        if a != PMI: ov['0x' + a.to_bytes(20, 'big').hex()] = {'code': '0x' + c.hex()}
    return ov


def build(rnd, idx, code):
    hk = rnd.choice(HOOKS + [0, 0]); dynamic = hk and rnd.random() < 0.5
    fee = Q.DYNAMIC if dynamic else rnd.choice([0, 100, 3000, 10000]); sp = rnd.choice([1, 10, 60])
    key = w(T0) + w(T1) + w(fee) + w(sp) + w(hk); pid = keccak(key); base = int.from_bytes(keccak(pid + w(6)), 'big')
    want_return = idx % 3 != 0
    items = []; kinds = []

    def add(kind, target, data): items.append(item(target, data)); kinds.append(kind)

    def cfg():
        if not hk: return
        small = lambda: u(rnd.choice([0, 0, 0, 0, 1, -1, rnd.getrandbits(10), -rnd.getrandbits(10)]))
        w1 = ((small() & ((1 << 128) - 1)) << 128) | (small() & ((1 << 128) - 1)) if rnd.random() < 0.25 else 0
        w2 = rnd.choice([0, 0, 0x400000 | rnd.choice([0, 500, 3000])])
        add('cfg', hk, Q.S_SET + w(w1) + w(w2) + w(AUTO) + w(0) + w(0))

    def hd(): return rnd.randbytes(rnd.choice([0, 1, 31, 32, 33, 64, 100])) if hk else rnd.randbytes(rnd.choice([0, 0, 5, 64]))

    cfg()
    add('owner', PMI, S['owner']); add('setPfc', PMI, S['setPfc'] + w(DRV)); add('pfc', PMI, S['pfc'])
    t0 = rnd.randrange(-20000, 20000); price = m.get_sqrt_price_at_tick(t0)
    add('init', PMI, P.S_INIT + key + w(price))
    pf = rnd.choice([0, 1, 500, 1000, 1001, 4095]) | (rnd.choice([0, 1, 777, 1000, 1001]) << 12)
    add('setFee', PMI, S['setFee'] + key + w(pf)); add('ext', PMI, P.S_EXTSLOAD + w(base & MASK))
    lo, hi = (t0 - 2000) // sp * sp, (t0 + 2000) // sp * sp + sp
    h = hd(); add('mod', PMI, P.S_MOD + key + w(lo) + w(hi) + w(rnd.choice([10 ** 18, rnd.getrandbits(80) or 1])) + w(0) + w(0x140) + tail(h))
    if dynamic:
        add('dyn', hk, b'\x00\x00\x00\x03' + S['dyn'] + key + w(rnd.choice([0, 500, 1000000, 1000001])))
        add('dyn', PMI, S['dyn'] + key + w(500))  # not the hook: must be refused
    for _ in range(rnd.randrange(2, 6)):
        r = rnd.random()
        if rnd.random() < 0.3: cfg()
        if r < 0.45:
            zfo = rnd.random() < 0.5; mag = rnd.choice([1, rnd.getrandbits(30), rnd.getrandbits(60), 10 ** 15]); amt = -mag if rnd.random() < 0.7 else mag
            limit = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            lim2 = m.get_sqrt_price_at_tick(t0 - 1500 if zfo else t0 + 1500)
            h = hd(); add('swap', PMI, P.S_SWAP + key + w(int(zfo)) + w(amt) + w(rnd.choice([limit, lim2])) + w(0x120) + tail(h))
            add('accrued', PMI, S['accrued'] + w(T0)); add('accrued', PMI, S['accrued'] + w(T1))
        elif r < 0.6:
            h = hd(); add('donate', PMI, P.S_DONATE + key + w(rnd.getrandbits(30)) + w(rnd.getrandbits(30)) + w(0x100) + tail(h))
        elif r < 0.75:
            cur = rnd.choice([T0, T1]); add('collect', PMI, S['collect'] + w(rnd.choice([OTHER, DRV])) + w(cur) + w(rnd.choice([0, 0, 0, 1, rnd.getrandbits(20) << 8])))
        else:
            amt = rnd.getrandbits(40)
            add('mint', PMI, P.S_MINT + w(DRV) + w(T1) + w(amt))
            add('transfer', PMI, S['transfer'] + w(OTHER) + w(T1) + w(amt // 3))
            add('approve', PMI, S['approve'] + w(OTHER) + w(T1) + w(rnd.choice([amt, MASK, 0])))
            add('setOperator', PMI, S['setOperator'] + w(OTHER) + w(rnd.choice([0, 1])))
            add('transferFrom', PMI, S['transferFrom'] + w(DRV) + w(OTHER) + w(T1) + w(amt // 3))
            add('transferFrom', PMI, S['transferFrom'] + w(OTHER) + w(DRV) + w(T1) + w(1))  # the driver is not approved by OTHER
            add('view', PMI, S['allowance'] + w(DRV) + w(OTHER) + w(T1)); add('view', PMI, S['isOperator'] + w(DRV) + w(OTHER))
            add('view', PMI, P.S_BALANCEOF + w(OTHER) + w(T1))
            add('burn', PMI, P.S_BURN + w(DRV) + w(T1) + w(amt - 2 * (amt // 3)))
    for iface in (0x01ffc9a7, 0x0f632fb3, 0xffffffff, rnd.getrandbits(32)):
        add('view', PMI, S['supports'] + w(iface << 224))
    add('view', PMI, S['extN'] + w(base & MASK) + w(rnd.choice([0, 1, 4, 7])))
    slots = [(base + k) & MASK for k in range(rnd.randrange(0, 5))]
    add('view', PMI, S['extA'] + w(0x20) + w(len(slots)) + b''.join(w(x) for x in slots))
    dslots = [P.delta_slot(DRV, T0), P.delta_slot(DRV, T1)] + ([P.delta_slot(hk, T1)] if hk else [])
    add('view', PMI, S['exttA'] + w(0x20) + w(len(dslots)) + b''.join(w(x) for x in dslots))
    if rnd.random() < 0.3: add('settleFor', PMI, S['settleFor'] + w(OTHER))
    if rnd.random() < 0.2: add('owner', PMI, S['transferOwnership'] + w(OTHER)); add('owner', PMI, S['setPfc'] + w(OTHER))
    if not want_return:
        return b''.join(items) + b'\0' * 22, kinds, {'returns': False}
    # read the deltas the script leaves, then append what brings them to zero
    probe = items + [item(PMI, P.S_EXTTLOAD + w(P.delta_slot(DRV, T0))), item(PMI, P.S_EXTTLOAD + w(P.delta_slot(DRV, T1)))]
    wd = world(code); ok, ret = wd.call(0, DRV, 0, b''.join(probe) + b'\0' * 22, False, 0)
    rec = P.parse(ret); d0, d1 = s(int.from_bytes(rec[-2][1], 'big')), s(int.from_bytes(rec[-1][1], 'big'))
    for cur, d in ((T0, d0), (T1, d1)):
        if d > 0: add('mint', PMI, P.S_MINT + w(DRV) + w(cur) + w(d))
        elif d < 0:
            add('tset', cur, TSET + w(1000)); add('sync', PMI, Q.S_SYNC + w(cur)); add('tset', cur, TSET + w(1000 - d)); add('settle', PMI, P.S_SETTLE)
    return b''.join(items) + (1).to_bytes(20, 'big') + b'\0\0', kinds, {'returns': True}


def unwrap(ret):
    """A returning script comes back as abi encoded bytes; a reverting one as the bare record."""
    if len(ret) >= 64 and int.from_bytes(ret[:32], 'big') == 0x20 and int.from_bytes(ret[32:64], 'big') <= len(ret) - 64:
        return ret[64:64 + int.from_bytes(ret[32:64], 'big')]
    return ret


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 200; only = set(map(int, sys.argv[3:]))
    code = P.fetch_code(); rnd = random.Random(3_2026_11_24)
    scripts = [build(rnd, i, code) for i in range(n)]
    # reference answers and coverage
    ref = []; cover = set(); branches = {}; ops = {}; stats = {'calls': 0, 'ok': 0, 'failed': 0, 'returned': 0, 'notSettled': 0, 'byKind': {}}
    for data, kinds, meta in scripts:
        wd = world(code); ok, ret = wd.call(0, DRV, 0, data, False, 0); ref.append(ret)
        cover |= wd.cover.get(PMI, set())
        for (a, pc), o in wd.branches.items():
            if a == PMI: branches.setdefault(pc, set()).update(o)
        for o, c in wd.ops.items(): ops[o] = ops.get(o, 0) + c
        if meta['returns']:
            if ret[:4] == keccak(b'CurrencyNotSettled()')[:4]: stats['notSettled'] += 1; continue
            stats['returned'] += 1
        for kind, (k, r) in zip(kinds, P.parse(unwrap(ret))):
            stats['calls'] += 1; stats['ok' if k else 'failed'] += 1; b = stats['byKind'].setdefault(kind, [0, 0]); b[0 if k else 1] += 1
    json.dump({'cover': sorted(cover), 'branches': {str(k): sorted(v) for k, v in branches.items()}, 'ops': {NAMES.get(o, hex(o)): c for o, c in ops.items()}},
              open(out.replace('.json', '-coverage.json'), 'w'))
    print(n, 'scripts; reference:', stats)
    refh = [hashlib.sha256(r).hexdigest() for r in ref]
    ov = overrides(code)

    def ask(url, data, gas):
        last = None
        for k in range(5):
            try:
                return hashlib.sha256(bytes.fromhex(rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=120)[2:])).hexdigest()
            except Exception as e:  # noqa
                last = str(e)[:120]
                if 'gas' in last.lower() and 'limit' in last.lower(): break
                time.sleep(3 * (k + 1))
        return 'ERR ' + last

    def run_net(nw):
        cid, name, url = nw; res = []
        for i, (data, _, _) in enumerate(scripts):
            h = ask(url, data, 25_000_000)
            if h != refh[i] and not h.startswith('ERR'):
                # the reference has no gas limit: a script that walks many ticks can run out of gas on a node, so ask again with more
                for gas in (2_000_000_000, 150_000_000):
                    h2 = ask(url, data, gas)
                    if not h2.startswith('ERR'): h = h2 if h2 == refh[i] else h; break
            res.append(h)
        return cid, name, res

    nets = [x for x in networks() if not only or x[0] in only]
    summary = []
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(run_net, nets):
            diff = [i for i, (a, b) in enumerate(zip(res, refh)) if a != b and not a.startswith('ERR')]
            same = sum(1 for a, b in zip(res, refh) if a == b); err = [a for a in res if a.startswith('ERR')]
            print(f'{cid:>8} {name:16} equal to the reference {same}/{n} different {len(diff)} errors {len(err)} {err[:1]}', flush=True)
            summary.append({'chainId': cid, 'name': name, 'identical': same, 'different': diff, 'errors': len(err)})
    json.dump({'scripts': n, 'reference': stats, 'results': summary, 'referenceHashes': refh}, open(out, 'w'), indent=1)
