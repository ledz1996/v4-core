"""Second same-bytecode differential: the call paths of the PoolManager. pmdiff.py
covers the pool math with no hook and no token. This script adds a hook double and a
token double, both placed by state override, so that the assembly in Hooks.callHook,
Currency.transfer, CustomRevert.bubbleUpAndRevertWith and the return data parsing run
on every network with the same inputs:

  hook   answers every callback with [selector word][word 1][word 2] cut to a
         configured length, optionally with a flipped selector or as a revert
  token  balanceOf returns a configured number; transfer answers in one of nine
         shapes chosen by the low byte of the amount (true, nothing, false, 31 bytes,
         revert with data, 64 bytes, the number 2, empty revert, one byte)
  native a take of address(0) to an account without code and to the identity
         precompile, from a PoolManager balance set by state override

The driver takes items of [20 byte target][2 byte length][calldata], so a script can
configure the doubles between PoolManager calls. As in pmdiff.py every network must
return the same bytes as Ethereum.

Usage: python3 pmdiff2.py <out.json> [nScripts] [chainId ...]
"""
import sys, json, random, hashlib, time, concurrent.futures as cf
from evm import assemble, keccak, rpc, networks, MASK, u
import v4math as m
import pmdiff as P

TOKEN = 0x00000000000000000000000000000000C0FFEE02  # currency1 of the pools
HOOK_BASE = 0x00000000000000000000000000000000486B0000
HOOK_FLAGS = [0x3FFF, 0x00CC, 0x0F03, 0x3030, 0x0080, 0x0044]
SINK = 0x000000000000000000000000000000000000BEEF
S_SYNC = P.sel('sync(address)')
S_SET = b'\x00\x00\x00\x01'
DYNAMIC = 0x800000


def driver():
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(P.S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(P.S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, int(P.PM, 16)), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x2000), ('PUSH', 68),  # ptr, outp
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 96), 'SHR',  # addr, ptr, outp
         'DUP2', ('PUSH', 20), 'ADD', 'CALLDATALOAD', ('PUSH', 240), 'SHR',  # len, addr, ptr, outp
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP4', ('PUSH', 22), 'ADD', ('PUSH', 0), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), 'DUP7', 'GAS', 'CALL',  # ok, len, addr, ptr, outp
         'DUP5', 'MSTORE',
         'RETURNDATASIZE', 'DUP5', ('PUSH', 32), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP6', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',
         'SWAP3', ('PUSH', 64), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP3',
         'SWAP1', 'POP', ('PUSH', 22), 'ADD', 'ADD',
         ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP', 'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'REVERT']
    return assemble(p)


def token():
    def ret(word, size): return [('PUSH', word), ('PUSH', 0), 'MSTORE', ('PUSH', size), ('PUSH', 0), 'RETURN']
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR',
         'DUP1', ('PUSHN', 4, 0x70a08231), 'EQ', ('REF', 'bal'), 'JUMPI',
         'DUP1', ('PUSHN', 4, 0xa9059cbb), 'EQ', ('REF', 'xfer'), 'JUMPI',
         ('PUSH', 4), 'CALLDATALOAD', ('PUSH', 0), 'TSTORE', 'STOP',
         ('LABEL', 'bal'), ('PUSH', 0), 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
         ('LABEL', 'xfer'), ('PUSH', 36), 'CALLDATALOAD', ('PUSH', 0xff), 'AND']
    for mode in range(1, 9):
        p += ['DUP1', ('PUSH', mode), 'EQ', ('REF', f'm{mode}'), 'JUMPI']
    p += ret(1, 32)
    p += [('LABEL', 'm1'), ('PUSH', 0), ('PUSH', 0), 'RETURN']
    p += [('LABEL', 'm2')] + ret(0, 32)
    p += [('LABEL', 'm3')] + ret(1, 31)
    p += [('LABEL', 'm4'), ('PUSH', 0xdeadbeef << 224 | 0x1234), ('PUSH', 0), 'MSTORE', ('PUSH', 77), ('PUSH', 32), 'MSTORE', ('PUSH', 36), ('PUSH', 0), 'REVERT']
    p += [('LABEL', 'm5')] + ret(1, 64)
    p += [('LABEL', 'm6')] + ret(2, 32)
    p += [('LABEL', 'm7'), ('PUSH', 0), ('PUSH', 0), 'REVERT']
    p += [('LABEL', 'm8'), ('PUSH', 1), ('PUSH', 0), 'MSTORE8', ('PUSH', 1), ('PUSH', 0), 'RETURN']
    return assemble(p)


def hook():
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSH', 1), 'EQ', ('REF', 'set'), 'JUMPI',
         ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSH', 224), 'SHL', ('PUSH', 5), 'TLOAD', 'XOR', ('PUSH', 0), 'MSTORE',
         ('PUSH', 1), 'TLOAD', ('PUSH', 32), 'MSTORE', ('PUSH', 2), 'TLOAD', ('PUSH', 64), 'MSTORE',
         ('PUSH', 4), 'TLOAD', ('REF', 'rev'), 'JUMPI',
         ('PUSH', 3), 'TLOAD', ('PUSH', 0), 'RETURN',
         ('LABEL', 'rev'), ('PUSH', 3), 'TLOAD', ('PUSH', 0), 'REVERT',
         ('LABEL', 'set')]
    for k in range(1, 6):
        p += [('PUSH', 4 + 32 * (k - 1)), 'CALLDATALOAD', ('PUSH', k), 'TSTORE']
    p += ['STOP']
    return assemble(p)


def w(x): return (x & MASK).to_bytes(32, 'big')
def item(target, data): return target.to_bytes(20, 'big') + len(data).to_bytes(2, 'big') + data


def script(rnd, idx):
    flags = rnd.choice(HOOK_FLAGS); hk = HOOK_BASE | flags
    dynamic = rnd.random() < 0.4
    fee = DYNAMIC if dynamic else rnd.choice([0, 100, 3000, 10000, 999999])
    sp = rnd.choice([1, 10, 60, 200])
    key = w(P.C0) + w(TOKEN) + w(fee) + w(sp) + w(hk)
    pid = keccak(key); base = int.from_bytes(keccak(pid + w(6)), 'big')
    pm = int(P.PM, 16); drv = int(P.DRV, 16)
    items = []; kinds = []

    def add(kind, target, data): items.append(item(target, data)); kinds.append(kind)

    def cfg(normal=False):
        if normal:
            w1, w2, size, rev, flip = 0, 0, 96, 0, 0
        else:
            small = lambda: u(rnd.choice([0, 0, 1, -1, rnd.getrandbits(20), -rnd.getrandbits(20), rnd.getrandbits(100), -rnd.getrandbits(100), (1 << 127) - 1, -(1 << 127)]))
            w1 = ((small() & ((1 << 128) - 1)) << 128) | (small() & ((1 << 128) - 1))
            if rnd.random() < 0.15: w1 = rnd.getrandbits(256)
            w2 = rnd.choice([0, 0x400000 | rnd.choice([0, 500, 1000000, 1000001]), rnd.getrandbits(24), rnd.getrandbits(256), 3000])
            size = rnd.choice([96, 96, 96, 64, 32, 0, 4, 31, 63, 95, 128, 1000])
            rev = int(rnd.random() < 0.12); flip = (1 << 224) if rnd.random() < 0.1 else 0
        add('cfg', hk, S_SET + w(w1) + w(w2) + w(size) + w(rev) + w(flip))

    def state():
        for k in (0, 3): add('ext', pm, P.S_EXTSLOAD + w((base + k) & MASK))
        add('ext', pm, P.S_EXTTLOAD + w(P.delta_slot(drv, P.C0))); add('ext', pm, P.S_EXTTLOAD + w(P.delta_slot(drv, TOKEN))); add('ext', pm, P.S_EXTTLOAD + w(P.delta_slot(hk, TOKEN)))

    cfg(normal=rnd.random() < 0.8)
    t0 = rnd.randrange(-50000, 50000); price = m.get_sqrt_price_at_tick(t0)
    add('init', pm, P.S_INIT + key + w(price))
    lo, hi = (t0 - 3000) // sp * sp, (t0 + 3000) // sp * sp + sp
    for _ in range(rnd.randrange(1, 4)):
        cfg(normal=rnd.random() < 0.6)
        add('mod', pm, P.S_MOD + key + w(lo + sp * rnd.randrange(0, 20)) + w(hi - sp * rnd.randrange(0, 20)) + w(rnd.choice([10 ** 18, rnd.getrandbits(70) or 1, rnd.getrandbits(100) or 1])) + w(0) + w(0x140) + w(0))
    state()
    for _ in range(rnd.randrange(4, 9)):
        r = rnd.random()
        if r < 0.5:
            cfg(normal=rnd.random() < 0.35)
            zfo = rnd.random() < 0.5; mag = rnd.choice([1, rnd.getrandbits(30), rnd.getrandbits(64), rnd.getrandbits(90), 10 ** 18])
            amt = -mag if rnd.random() < 0.6 else mag
            limit = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            add('swap', pm, P.S_SWAP + key + w(int(zfo)) + w(amt) + w(limit) + w(0x120) + w(0))
        elif r < 0.62:
            cfg(normal=rnd.random() < 0.4)
            add('mod', pm, P.S_MOD + key + w(lo) + w(hi) + w(rnd.choice([-1, 1, -(10 ** 6), 10 ** 6, 0])) + w(0) + w(0x140) + w(0))
        elif r < 0.7:
            cfg(normal=rnd.random() < 0.4)
            add('donate', pm, P.S_DONATE + key + w(rnd.getrandbits(40)) + w(rnd.getrandbits(40)) + w(0x100) + w(0))
        elif r < 0.85:
            start = rnd.getrandbits(rnd.choice((0, 64, 200))); gain = rnd.choice([0, 1, rnd.getrandbits(64), rnd.getrandbits(126), 1 << 127, (1 << 128) - 1, -1])
            add('tset', TOKEN, b'\x00\x00\x00\x02' + w(start)); add('sync', pm, S_SYNC + w(TOKEN))
            add('tset', TOKEN, b'\x00\x00\x00\x02' + w(start + gain)); add('settle', pm, P.S_SETTLE)
        else:
            mode = rnd.randrange(0, 10)
            add('take', pm, P.S_TAKE + w(TOKEN) + w(rnd.choice([drv, SINK, 4, pm])) + w((rnd.getrandbits(48) << 8) | mode))
        state()
    if idx % 10 == 9:  # native payouts, kept to a tenth of the scripts because Tempo has no native asset
        for to in (SINK, 4, 1):
            add('native', pm, P.S_TAKE + w(0) + w(to) + w(rnd.choice([0, 1, 10 ** 15])))
        state()
    return b''.join(items) + b'\0' * 22, kinds, {'flags': flags, 'fee': fee, 'native': idx % 10 == 9}


def parse(buf): return P.parse(buf)


def run_net(n, ov, scripts):
    cid, name, url = n; res = []
    for data, _, _ in scripts:
        last = None
        for k in range(5):
            try:
                r = rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest', ov], timeout=90)
                res.append(r if cid == 1 else hashlib.sha256(bytes.fromhex(r[2:])).hexdigest()); last = None; break
            except Exception as e:  # noqa
                last = str(e)[:120]; time.sleep(3 * (k + 1))
        if last is not None: res.append('ERR ' + last)
    return cid, name, res


if __name__ == '__main__':
    out = sys.argv[1]; n_scripts = int(sys.argv[2]) if len(sys.argv) > 2 else 200; only = set(map(int, sys.argv[3:]))
    rnd = random.Random(11_2026_11_24)
    scripts = [script(rnd, i) for i in range(n_scripts)]
    code = P.fetch_code(); drv = driver(); tok = token(); hk = hook()
    ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + drv.hex()},
          '0x' + TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + tok.hex()}}
    for f in HOOK_FLAGS: ov['0x' + (HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + hk.hex()}
    print('driver', len(drv), 'token', len(tok), 'hook', len(hk), 'bytes;', n_scripts, 'scripts,', sum(len(k) for _, k, _ in scripts), 'calls')
    nets = [n for n in networks() if not only or n[0] in only or n[0] == 1]
    results = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(lambda n: run_net(n, ov, scripts), nets): results[cid] = (name, res)
    ref = results[1][1]; stats = {'calls': 0, 'ok': 0, 'failed': 0, 'byKind': {}, 'revertSelectors': {}}
    for (data, kinds, meta), r in zip(scripts, ref):
        if r.startswith('ERR'): continue
        for kind, (ok, ret) in zip(kinds, parse(bytes.fromhex(r[2:]))):
            stats['calls'] += 1; stats['ok' if ok else 'failed'] += 1
            b = stats['byKind'].setdefault(kind, [0, 0]); b[0 if ok else 1] += 1
            if not ok and kind not in ('cfg', 'tset'):
                s4 = ret[:4].hex() or 'empty'; stats['revertSelectors'][s4] = stats['revertSelectors'].get(s4, 0) + 1
    print('Ethereum reference:', {k: v for k, v in stats.items() if k != 'revertSelectors'}); print('revert selectors seen:', stats['revertSelectors'])
    refh = [hashlib.sha256(bytes.fromhex(r[2:])).hexdigest() if not r.startswith('ERR') else r for r in ref]
    summary = []
    for cid, (name, res) in results.items():
        if cid == 1: continue
        diff = [i for i, (a, b) in enumerate(zip(res, refh)) if a != b and not a.startswith('ERR') and not b.startswith('ERR')]
        same = sum(1 for a, b in zip(res, refh) if a == b and not a.startswith('ERR')); err = sum(1 for a in res if a.startswith('ERR'))
        nat = sum(1 for i in diff if scripts[i][2]['native'])
        print(f'{cid:>8} {name:16} identical {same}/{len(res)} different {len(diff)} (with native payouts: {nat}) errors {err}')
        summary.append({'chainId': cid, 'name': name, 'identical': same, 'different': diff, 'differentWithNative': nat, 'errors': err})
    json.dump({'scripts': n_scripts, 'reference': stats, 'results': summary, 'referenceHashes': refh}, open(out, 'w'), indent=1)
