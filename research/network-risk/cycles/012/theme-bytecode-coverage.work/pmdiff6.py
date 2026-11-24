"""Sixth script set (cycle 12, unit theme-bytecode-coverage): scripts written to take the side of each
conditional jump that the first five sets never took, on the bytecode built from this checkout.

What it adds over pmdiff3.py:
  driver   items are [20 byte target][1 byte kind][16 byte value][2 byte length][calldata]; kind 0 is CALL
           with the given value, 1 is DELEGATECALL, 2 is STATICCALL. A script whose first byte is 0xff runs
           in the outer frame without unlock (the lock checks). The terminator names address 1 to return the
           record as abi encoded bytes from the callback, 2 to return 31 bytes that are not abi encoded, and
           anything else to revert with the record.
  hooks    one hook double per permission bit and per return-delta combination, at base 0x486C0000; the
           double from pmdiff3.py, which can also forward a call to the PoolManager (hook self-calls) and
           serves as a native recipient that reverts with return data of a configured length.
  btoken   a token double whose balanceOf reverts, returns 31 bytes, returns nothing or returns 64 bytes.
Groups: hook permission paths, ERC-6909 spender and operator paths, clear, native value and settle,
calls outside unlock, delegatecalls, failing native payouts, failing balanceOf, bounds of initialize,
modifyLiquidity and swap, the large-number branches of SqrtPriceMath and FullMath, protocol fee
collection, malformed callback return data, extsload and exttload ranges, mint and burn with odd ids.

Every network's answer is compared with the reference interpreter's answer (pyevm.py).
Usage: python3 pmdiff6.py <out.json> [chainId ...]
"""
import sys, os, json, random, hashlib, time, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, keccak, rpc, networks, MASK, u, s
import v4math as m
import pmdiff as P, pmdiff2 as Q, pmdiff3 as R
from pyevm import World, NAMES

PMI = int(P.PM, 16)
DRV = 0x00000000000000000000000000000000D21FE006
T0, T1 = P.C0, Q.TOKEN
BT = 0x00000000000000000000000000000000C0FFEE05
OTHER = R.OTHER
HB = 0x00000000000000000000000000000000486C0000
sel = P.sel
S = dict(R.S)
S.update({k: sel(v) for k, v in {'settle': 'settle()', 'sync': 'sync(address)', 'take': 'take(address,address,uint256)',
                                  'clear': 'clear(address,uint256)', 'mint': 'mint(address,uint256,uint256)',
                                  'burn': 'burn(address,uint256,uint256)', 'unlock': 'unlock(bytes)',
                                  'exttload': 'exttload(bytes32)', 'extsload': 'extsload(bytes32)',
                                  'balanceOf': 'balanceOf(address,uint256)'}.items()})
TSET = R.TSET
FWD = b'\x00\x00\x00\x03'
AUTO = R.AUTO
DYN = Q.DYNAMIC
MINP, MAXP = m.MIN_SQRT_PRICE, m.MAX_SQRT_PRICE
w = P.w


def loop(pfx, locked):
    L = lambda n: pfx + n
    p = [('LABEL', L('loop')), 'DUP1', 'CALLDATALOAD', ('PUSH', 96), 'SHR',
         'DUP2', ('PUSH', 37), 'ADD', 'CALLDATALOAD', ('PUSH', 240), 'SHR',
         'DUP1', 'ISZERO', ('REF', L('end')), 'JUMPI',
         'DUP1', 'DUP4', ('PUSH', 39), 'ADD', ('PUSH', 0), 'CALLDATACOPY',
         'DUP3', ('PUSH', 20), 'ADD', 'CALLDATALOAD', ('PUSH', 248), 'SHR',
         'DUP1', ('PUSH', 1), 'EQ', ('REF', L('dc')), 'JUMPI',
         'DUP1', ('PUSH', 2), 'EQ', ('REF', L('sc')), 'JUMPI',
         'POP', 'DUP3', ('PUSH', 21), 'ADD', 'CALLDATALOAD', ('PUSH', 128), 'SHR',
         ('PUSH', 0), ('PUSH', 0), 'DUP4', ('PUSH', 0), 'DUP5', 'DUP8', 'GAS', 'CALL', 'SWAP1', 'POP', ('REF', L('rec')), 'JUMP',
         ('LABEL', L('dc')), 'POP', ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), 'DUP6', 'GAS', 'DELEGATECALL', ('REF', L('rec')), 'JUMP',
         ('LABEL', L('sc')), 'POP', ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), 'DUP6', 'GAS', 'STATICCALL',
         ('LABEL', L('rec')),
         'DUP5', 'MSTORE', 'RETURNDATASIZE', 'DUP5', ('PUSH', 32), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP6', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',
         'SWAP3', ('PUSH', 64), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP3',
         'SWAP1', 'POP', ('PUSH', 39), 'ADD', 'ADD', ('REF', L('loop')), 'JUMP',
         ('LABEL', L('end')), 'POP']
    if locked:
        p += ['POP', 'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'RETURN']
    else:
        p += ['DUP1', ('PUSH', 1), 'EQ', ('REF', L('ret')), 'JUMPI', 'DUP1', ('PUSH', 2), 'EQ', ('REF', L('junk')), 'JUMPI',
              'DUP1', ('PUSH', 3), 'EQ', ('REF', L('raw')), 'JUMPI',
              'POP', 'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'REVERT',
              ('LABEL', L('ret')), 'POP', 'POP', ('PUSH', 0x2000), 'SWAP1', 'SUB',
              'DUP1', ('PUSH', 0x1fe0), 'MSTORE', ('PUSH', 0x20), ('PUSH', 0x1fc0), 'MSTORE',
              ('PUSH', 0x5f), 'ADD', ('PUSH', 0x1f), 'NOT', 'AND', ('PUSH', 0x1fc0), 'RETURN',
              ('LABEL', L('junk')), ('PUSH', 0), 'NOT', ('PUSH', 0), 'MSTORE', ('PUSH', 31), ('PUSH', 0), 'RETURN',
              # terminator 3: return the [2 byte length][bytes] that follow it, verbatim
              ('LABEL', L('raw')), 'POP', 'DUP1', ('PUSH', 39), 'ADD', 'CALLDATALOAD', ('PUSH', 240), 'SHR',  # n, ptr, outp
              'DUP1', 'DUP3', ('PUSH', 41), 'ADD', ('PUSH', 0), 'CALLDATACOPY', ('PUSH', 0), 'RETURN']
    return p


def driver():
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(P.S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 248), 'SHR', ('PUSH', 0xff), 'EQ', ('REF', 'locked'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(P.S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PMI), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'locked'), ('PUSH', 0x2000), ('PUSH', 1)] + loop('L', True) + [
         ('LABEL', 'cb'), ('PUSH', 0x2000), ('PUSH', 68)] + loop('C', False)
    return assemble(p)


def btoken():
    """balanceOf answers by mode (transient slot 1): 0 the balance in slot 0, 1 a revert with 40 bytes, 2 31 bytes,
    3 nothing, 4 64 bytes. Selector 2 sets the balance, selector 5 the mode. transfer returns true."""
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR',
         'DUP1', ('PUSHN', 4, 0x70a08231), 'EQ', ('REF', 'bal'), 'JUMPI',
         'DUP1', ('PUSH', 5), 'EQ', ('REF', 'mode'), 'JUMPI',
         'DUP1', ('PUSH', 2), 'EQ', ('REF', 'set'), 'JUMPI',
         ('PUSH', 1), ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
         ('LABEL', 'set'), ('PUSH', 4), 'CALLDATALOAD', ('PUSH', 0), 'TSTORE', 'STOP',
         ('LABEL', 'mode'), ('PUSH', 4), 'CALLDATALOAD', ('PUSH', 1), 'TSTORE', 'STOP',
         ('LABEL', 'bal'), ('PUSH', 0), 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSHN', 4, 0xabcdef01), ('PUSH', 32), 'MSTORE',
         ('PUSH', 1), 'TLOAD',
         'DUP1', ('PUSH', 1), 'EQ', ('REF', 'm1'), 'JUMPI', 'DUP1', ('PUSH', 2), 'EQ', ('REF', 'm2'), 'JUMPI',
         'DUP1', ('PUSH', 3), 'EQ', ('REF', 'm3'), 'JUMPI', 'DUP1', ('PUSH', 4), 'EQ', ('REF', 'm4'), 'JUMPI',
         ('PUSH', 32), ('PUSH', 0), 'RETURN',
         ('LABEL', 'm1'), ('PUSH', 40), ('PUSH', 0), 'REVERT',
         ('LABEL', 'm2'), ('PUSH', 31), ('PUSH', 0), 'RETURN',
         ('LABEL', 'm3'), ('PUSH', 0), ('PUSH', 0), 'RETURN',
         ('LABEL', 'm4'), ('PUSH', 64), ('PUSH', 0), 'RETURN']
    return assemble(p)


FLAGS = [1 << b for b in range(14)] + [0, 0x0044, 0x0088, 0x00CC, 0x00C0, 0x0101, 0x0102, 0x0303, 0x0402, 0x0C03, 0x0F03,
                                       0x0F00, 0x0030, 0x3000, 0x3FFF, 0x3FF0, 0x0005, 0x000A]
HOOKS = sorted({HB | f for f in FLAGS})


def codes(code):
    c = {PMI: code, DRV: driver(), T0: Q.token(), T1: Q.token(), BT: btoken()}
    for h in HOOKS: c[h] = R.hook()
    return c


BAL = {PMI: 10 ** 19, DRV: 10 ** 21}


def world(code):
    wd = World(codes(code), dict(BAL)); wd.storage[(PMI, 0)] = DRV
    return wd


def overrides(code):
    ov = {}
    for a, c in codes(code).items():
        e = {'code': '0x' + c.hex()}
        if a in BAL: e['balance'] = hex(BAL[a])
        if a == PMI: e['stateDiff'] = {'0x' + '00' * 32: '0x' + DRV.to_bytes(32, 'big').hex()}
        ov['0x' + a.to_bytes(20, 'big').hex()] = e
    return ov


def raw_end(b): return (3).to_bytes(20, 'big') + bytes(17) + b'\0\0' + len(b).to_bytes(2, 'big') + b


def it(target, data, kind=0, value=0): return target.to_bytes(20, 'big') + bytes([kind]) + value.to_bytes(16, 'big') + len(data).to_bytes(2, 'big') + data
def end(mode=0): return mode.to_bytes(20, 'big') + bytes(17) + b'\0\0'
def tail(b): return w(len(b)) + b + bytes(-len(b) % 32)
def key(c0, c1, fee, sp, hk): return w(c0) + w(c1) + w(fee) + w(sp) + w(hk)
def init(k, price): return P.S_INIT + k + w(price)
def mod(k, lo, hi, d, salt=0, hd=b''): return P.S_MOD + k + w(lo) + w(hi) + w(d) + w(salt) + w(0x140) + tail(hd)
def swap(k, zfo, amt, limit, hd=b''): return P.S_SWAP + k + w(int(zfo)) + w(amt) + w(limit) + w(0x120) + tail(hd)
def donate(k, a0, a1, hd=b''): return P.S_DONATE + k + w(a0) + w(a1) + w(0x100) + tail(hd)
def cfg(hk, w1=0, w2=0, size=AUTO, rev=0, flip=0): return it(hk, Q.S_SET + w(w1) + w(w2) + w(size) + w(rev) + w(flip))
def pid(k): return keccak(k)
def pslot(k, j): return (int.from_bytes(keccak(pid(k) + w(6)), 'big') + j) & MASK
def dslot(t, c): return P.delta_slot(t, c)
def ext(slot): return it(PMI, S['extsload'] + w(slot))
def text(slot): return it(PMI, S['exttload'] + w(slot))


def state(k, who=(DRV,), curs=(T0, T1)):
    out = [ext(pslot(k, j)) for j in (0, 1, 2, 3)]
    for t in who:
        for c in curs: out.append(text(dslot(t, c)))
    return out


def max_liq(sp):
    # the formula of Pool.tickSpacingToMaxLiquidityPerTick (src/libraries/Pool.sol:565-582)
    q = lambda a, b: abs(a) // abs(b) * (1 if (a < 0) == (b < 0) else -1)
    mn = q(-887272, sp) - (1 if (-887272 - q(-887272, sp) * sp) < 0 else 0); mx = q(887272, sp)
    return ((1 << 128) - 1) // (mx - mn + 1)


def d128(a, b): return ((u(a) & ((1 << 128) - 1)) << 128) | (u(b) & ((1 << 128) - 1))


def scripts():
    rnd = random.Random(6_2026_11_24); out = []

    def add(name, items, mode=0, locked=False):
        out.append((name, (b'\xff' if locked else b'') + b''.join(items) + end(mode)))

    # 1. hook permission paths: one pool per hook, add, swap both ways, remove, donate, with and without deltas
    for f in FLAGS:
        hk = HB | f
        for dyn in (False, True):
            if f == 0 and not dyn: continue
            fee = DYN if dyn else 3000
            k = key(T0, T1, fee, 60, hk); t0 = rnd.randrange(-3000, 3000)
            for variant in range(3):
                its = []
                if variant == 1: its.append(cfg(hk, d128(rnd.choice([7, -7, 1000]), rnd.choice([3, -3, 0])), 0x400000 | 500 if dyn else 0))
                elif variant == 2: its.append(cfg(hk, d128(0, rnd.choice([5, -5])), 0x400000 | 1000001 if dyn else 0, AUTO))
                else: its.append(cfg(hk))
                its.append(it(PMI, init(k, m.get_sqrt_price_at_tick(t0))))
                hd = rnd.randbytes(rnd.choice([0, 33]))
                its.append(it(PMI, mod(k, (t0 - 600) // 60 * 60, (t0 + 600) // 60 * 60 + 60, 10 ** 18, 0, hd)))
                its += state(k, (DRV, hk))
                for zfo, amt in ((True, -10 ** 15), (False, 10 ** 14), (False, -10 ** 15), (True, 10 ** 14)):
                    lim = MINP + 1 if zfo else MAXP - 1
                    its.append(it(PMI, swap(k, zfo, amt, lim, hd))); its += state(k, (DRV, hk))
                its.append(it(PMI, mod(k, (t0 - 600) // 60 * 60, (t0 + 600) // 60 * 60 + 60, -(10 ** 17), 0, hd))); its += state(k, (DRV, hk))
                its.append(it(PMI, donate(k, 12345, 6789, hd))); its += state(k, (DRV, hk))
                its.append(it(PMI, mod(k, (t0 - 600) // 60 * 60, (t0 + 600) // 60 * 60 + 60, -(9 * 10 ** 17), 0, hd))); its += state(k, (DRV, hk))
                its.append(it(PMI, mod(k, (t0 - 600) // 60 * 60, (t0 + 600) // 60 * 60 + 60, 0, 0, hd)))
                if dyn:
                    its.append(it(hk, FWD + S['dyn'] + k + w(rnd.choice([0, 3000, 1000000, 1000001]))))
                    its.append(it(PMI, S['dyn'] + k + w(500)))
                else:
                    its.append(it(hk, FWD + S['dyn'] + k + w(500)))
                add(f'hook {f:#06x} dyn={dyn} v{variant}', its)
    # 1b. hooks calling the PoolManager themselves (noSelfCall and the msg.sender == hook returns)
    for f in (0x3FFF, 0x0F03, 0x00CC, 0x3000, 0x0044, 0x0101, 0x0402):
        hk = HB | f if (HB | f) in HOOKS else HB | 0x3FFF
        k = key(T0, T1, 3000, 10, hk)
        its = [cfg(hk, d128(9, 9)), it(hk, FWD + init(k, m.get_sqrt_price_at_tick(100))),
               it(hk, FWD + mod(k, -1000, 1000, 10 ** 18)), it(hk, FWD + swap(k, True, -10 ** 12, MINP + 1)),
               it(hk, FWD + swap(k, False, 10 ** 12, MAXP - 1)), it(hk, FWD + donate(k, 5, 5)),
               it(hk, FWD + mod(k, -1000, 1000, -(10 ** 18)))] + state(k, (DRV, hk))
        its += [it(PMI, mod(k, -1000, 1000, 10 ** 15)), it(PMI, swap(k, True, -10 ** 9, MINP + 1))] + state(k, (DRV, hk))
        add(f'hook self-call {f:#06x}', its)
    # 1c. hook addresses that are not valid
    for hk, fee in [(HB | 0x0008, 3000), (HB | 0x0004, 3000), (HB | 0x0002, 3000), (HB | 0x0001, 3000), (HB | 0x0005, 3000),
                    (HB | 0x000A, 3000), (HB, 3000), (0, DYN), (HB, DYN), (HB | 0x0102, 500), (HB | 0x0303, DYN), (0, 1000001), (HB | 0x40, 1000001)]:
        add(f'invalid hook {hk:#x} fee {fee:#x}', [it(PMI, init(key(T0, T1, fee, 60, hk), 1 << 96))])
    # 2. ERC-6909: the hook double owns claims and approves or appoints the driver
    hk = HB | 0x0080
    for amt in (1000, 7, 1 << 100):
        for appr in (amt, amt - 1, MASK, 0):
            for op in (0, 1):
                its = [it(PMI, S['mint'] + w(hk) + w(T1) + w(amt)), it(PMI, S['mint'] + w(hk) + w(T0 | (1 << 200)) + w(amt))]
                its.append(it(hk, FWD + S['approve'] + w(DRV) + w(T1) + w(appr)))
                its.append(it(hk, FWD + S['approve'] + w(DRV) + w(T0) + w(appr)))
                if op: its.append(it(hk, FWD + S['setOperator'] + w(DRV) + w(1)))
                its += [it(PMI, S['allowance'] + w(hk) + w(DRV) + w(T1)), it(PMI, S['isOperator'] + w(hk) + w(DRV))]
                its.append(it(PMI, S['transferFrom'] + w(hk) + w(OTHER) + w(T1) + w(amt // 2)))
                its.append(it(PMI, S['allowance'] + w(hk) + w(DRV) + w(T1)))
                its.append(it(PMI, S['burn'] + w(hk) + w(T0 | (7 << 180)) + w(amt // 3)))
                its.append(it(PMI, S['allowance'] + w(hk) + w(DRV) + w(T0)))
                its.append(it(PMI, S['transferFrom'] + w(hk) + w(DRV) + w(T1) + w(amt - amt // 2)))
                its.append(it(PMI, S['burn'] + w(hk) + w(T0) + w(amt)))
                its += [it(PMI, S['balanceOf'] + w(x) + w(c)) for x in (hk, OTHER, DRV) for c in (T0, T1)]
                if op: its.append(it(hk, FWD + S['setOperator'] + w(DRV) + w(0)))
                its.append(it(PMI, S['transferFrom'] + w(hk) + w(DRV) + w(T1) + w(1)))
                its += [text(dslot(DRV, T0)), text(dslot(DRV, T1)), text(dslot(hk, T0))]
                add(f'erc6909 amt={amt} appr={appr} op={op}', its)
    # 3. clear: exact positive delta, off by one, above int128
    for x in (1, 50, 10 ** 18, (1 << 127) - 2000):
        its = [it(T1, TSET + w(1000)), it(PMI, S['sync'] + w(T1)), it(T1, TSET + w(1000 + x)), it(PMI, S['settle']),
               text(dslot(DRV, T1)), it(PMI, S['clear'] + w(T1) + w(x + 1)), it(PMI, S['clear'] + w(T1) + w(x - 1)),
               it(PMI, S['clear'] + w(T1) + w(1 << 127)), it(PMI, S['clear'] + w(T1) + w(x)), text(dslot(DRV, T1)),
               text(0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b), it(PMI, S['clear'] + w(T1) + w(0))]
        add(f'clear {x}', its, mode=1 if x < 10 ** 6 else 0)
    for x in (5, 10 ** 6):  # native: pay with value, then clear
        add(f'clear native {x}', [it(PMI, S['settle'], value=x), text(dslot(DRV, 0)), it(PMI, S['clear'] + w(0) + w(x)), text(dslot(DRV, 0))], mode=1)
    # 4. native value
    for v in (1, 10 ** 18):
        its = [it(T1, TSET + w(77)), it(PMI, S['sync'] + w(T1)), it(PMI, S['settle'], value=v), it(PMI, S['settleFor'] + w(OTHER), value=v),
               it(PMI, S['sync'] + w(0)), it(PMI, S['settle'], value=v), it(PMI, S['settleFor'] + w(OTHER), value=v),
               text(dslot(DRV, 0)), text(dslot(OTHER, 0)), it(PMI, S['take'] + w(0) + w(DRV) + w(2 * v)), text(dslot(DRV, 0)),
               it(PMI, S['take'] + w(0) + w(OTHER) + w(v))]
        add(f'native settle {v}', its)
        nonpay = [S['take'] + w(0) + w(DRV) + w(0), S['clear'] + w(T1) + w(0), S['mint'] + w(DRV) + w(T1) + w(0), S['burn'] + w(DRV) + w(T1) + w(0),
                  S['sync'] + w(T1), init(key(T0, T1, 500, 1, 0), 1 << 96), mod(key(T0, T1, 500, 1, 0), -10, 10, 1),
                  swap(key(T0, T1, 500, 1, 0), True, -5, MINP + 1), donate(key(T0, T1, 500, 1, 0), 1, 1),
                  S['dyn'] + key(T0, T1, DYN, 1, HB) + w(1), S['extsload'] + w(0), S['extN'] + w(0) + w(2), S['extA'] + w(0x20) + w(1) + w(0),
                  S['exttload'] + w(0), S['exttA'] + w(0x20) + w(1) + w(0), S['owner'], S['pfc'], S['setPfc'] + w(DRV),
                  S['setFee'] + key(T0, T1, 500, 1, 0) + w(0), S['collect'] + w(DRV) + w(0) + w(0), S['accrued'] + w(0),
                  S['transfer'] + w(OTHER) + w(T1) + w(0), S['transferFrom'] + w(DRV) + w(OTHER) + w(T1) + w(0),
                  S['approve'] + w(OTHER) + w(T1) + w(0), S['setOperator'] + w(OTHER) + w(0), S['allowance'] + w(DRV) + w(OTHER) + w(T1),
                  S['isOperator'] + w(DRV) + w(OTHER), S['balanceOf'] + w(DRV) + w(T1), S['supports'] + w(0x01ffc9a7 << 224),
                  S['transferOwnership'] + w(DRV), S['unlock'] + w(0x20) + w(0), sel('protocolFeesAccrued(address)') + w(T0)]
        add(f'value to non-payable {v}', [it(PMI, c, value=v) for c in nonpay])
    # 5. outside unlock
    k = key(T0, T1, 500, 1, 0)
    locked = [S['take'] + w(T1) + w(DRV) + w(0), S['settle'], S['settleFor'] + w(OTHER), S['clear'] + w(T1) + w(0),
              S['mint'] + w(DRV) + w(T1) + w(0), S['burn'] + w(DRV) + w(T1) + w(0), mod(k, -10, 10, 1), swap(k, True, -5, MINP + 1),
              donate(k, 1, 1), S['sync'] + w(T1), init(k, 1 << 96), mod(k, -10, 10, 1), swap(k, True, -5, MINP + 1), donate(k, 1, 1),
              S['exttload'] + w(0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23)]
    add('outside unlock', [it(PMI, c) for c in locked], locked=True)
    add('outside unlock, value', [it(PMI, S['settle'], value=3), it(PMI, S['settleFor'] + w(OTHER), value=3)], locked=True)
    add('nested unlock', [it(PMI, S['unlock'] + w(0x20) + w(0)), it(HB | 0x0080, FWD + S['unlock'] + w(0x20) + w(0))])
    # 6. delegatecall into the PoolManager
    dk = key(T0, T1, 3000, 60, 0)
    add('delegatecall', [it(PMI, init(dk, 1 << 96), kind=1), it(PMI, mod(dk, -60, 60, 10), kind=1), it(PMI, swap(dk, True, -5, MINP + 1), kind=1),
                         it(PMI, donate(dk, 1, 1), kind=1), it(PMI, S['extsload'] + w(0), kind=1), it(PMI, S['exttload'] + w(0), kind=1),
                         it(PMI, S['owner'], kind=1), it(PMI, S['sync'] + w(T1), kind=1), it(PMI, init(dk, 1 << 96), kind=2),
                         it(PMI, S['extsload'] + w(0), kind=2), it(PMI, S['sync'] + w(T1), kind=2)])
    add('delegatecall outside unlock', [it(PMI, init(dk, 1 << 96), kind=1), it(PMI, S['take'] + w(T1) + w(DRV) + w(0), kind=1)], locked=True)
    # 7. native payouts that fail, with revert data of many lengths
    rk = HB | 0x0080
    for size in (0, 1, 4, 31, 32, 33, 64, 95, 96, 100, 257, 1000):
        add(f'native take revert {size}', [cfg(rk, 0x1234, 0x5678, size, 1), it(PMI, S['take'] + w(0) + w(rk) + w(1000)),
                                           it(PMI, S['take'] + w(0) + w(rk) + w(0)), cfg(rk, 0, 0, size, 0), it(PMI, S['take'] + w(0) + w(rk) + w(1000)),
                                           text(dslot(DRV, 0))])
    add('native take to the PoolManager and to the driver', [it(PMI, S['take'] + w(0) + w(PMI) + w(10)), it(PMI, S['take'] + w(0) + w(DRV) + w(10 ** 19 + 1)),
                                                              it(PMI, S['take'] + w(0) + w(DRV) + w(10 ** 19)), text(dslot(DRV, 0))])
    # 8. balanceOf that misbehaves
    for mode in range(5):
        add(f'btoken mode {mode}', [it(BT, b'\x00\x00\x00\x02' + w(555)), it(BT, b'\x00\x00\x00\x05' + w(mode)), it(PMI, S['sync'] + w(BT)),
                                    it(BT, b'\x00\x00\x00\x02' + w(999)), it(PMI, S['settle']), text(dslot(DRV, BT)),
                                    it(BT, b'\x00\x00\x00\x05' + w(0)), it(PMI, S['settle'])])
    add('balance falls between sync and settle', [it(T1, TSET + w(1000)), it(PMI, S['sync'] + w(T1)), it(T1, TSET + w(999)), it(PMI, S['settle']),
                                                  it(T1, TSET + w(1000)), it(PMI, S['settle']), text(dslot(DRV, T1)), text(dslot(DRV, 0))])
    # 9. bounds of initialize, modifyLiquidity and swap
    for sp in (0, -1, 1, 32767, 32768, -32768, 1 << 23):
        add(f'init spacing {sp}', [it(PMI, init(key(T0, T1, 500, sp, 0), 1 << 96)), it(PMI, init(key(T0, T1, 500, sp, 0), 1 << 96))])
    for price in (MINP - 1, MINP, MINP + 1, MAXP - 1, MAXP, 1 << 159, 0, 1):
        k = key(T0, T1, 3000, 1, 0)
        its = [it(PMI, init(k, price)), ext(pslot(k, 0)), it(PMI, mod(k, -887272, 887272, 10 ** 12)), it(PMI, mod(k, -887273, 887272, 1)),
               it(PMI, mod(k, -887272, 887273, 1)), it(PMI, mod(k, 887272, 887272, 1))] + state(k)
        for zfo, amt, lim in ((True, -1000, MINP), (True, -1000, MINP + 1), (False, -1000, MAXP), (False, -1000, MAXP - 1), (True, 1000, price), (False, 1000, price),
                              (True, -(1 << 120), MINP + 1), (False, -(1 << 120), MAXP - 1)):
            its.append(it(PMI, swap(k, zfo, amt, lim))); its += state(k)
        add(f'init price {price}', its)
    for sp in (1, 60, 32767):
        k = key(T0, T1, 500, sp, 0)
        lo_t, hi_t = -(887272 // sp) * sp, (887272 // sp) * sp
        cap = max_liq(sp)
        a = max(lo_t, -10 * sp); b = min(hi_t, 10 * sp)
        its = [it(PMI, init(k, 1 << 96)), it(PMI, mod(k, a, b, cap // 2)), it(PMI, mod(k, b, min(hi_t, b + sp), cap // 2)),
               it(PMI, mod(k, a - sp, b, cap // 2 + 1)), it(PMI, mod(k, a - sp, b, cap // 2)), it(PMI, mod(k, a, b + sp, cap // 2 + 1)),
               it(PMI, mod(k, a, a + sp // 2 + 1 if sp > 1 else a + 1, 1)), it(PMI, mod(k, b, a, 1)), it(PMI, mod(k, a, b, -(1 << 127))),
               it(PMI, mod(k, a, b, 1 << 127)), it(PMI, mod(k, a, b, (1 << 255))), it(PMI, mod(k, a, b, -(cap // 2) - 1))] + state(k)
        add(f'tick liquidity bounds sp={sp}', its)
    # 10. large numbers. A position is capped by the int128 cast of what it deposits (src/libraries/Pool.sol:212-235), so near the
    # ends of the price range the full-range liquidity is about 2^62. Exact-input swaps of currency0 are not capped by reserves, which
    # reaches the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp (src/libraries/SqrtPriceMath.sol:42-52).
    for sp in (200, 16383, 32767):
        hi_t = (887272 // sp) * sp
        for t in (hi_t - 2 * sp, 800000 // sp * sp, 700000 // sp * sp, -(hi_t - 2 * sp)):
            for L in (1 << 40, 1 << 62):
                price = m.get_sqrt_price_at_tick(t) + 12345
                k = key(T0, T1, 0, sp, 0); num1 = L << 96  # fee 0: the step gets the whole amount
                amts = [((1 << 256) - 1) // price + d for d in (-1, 0, 1, 2)]
                amts += [((1 << 256) - num1) // price + d for d in (0, 1, 2, 3)] + [1 << 100, 1 << 110, 1 << 120, (1 << 126) + 7]
                for amt in amts:
                    its = [it(PMI, init(k, price)), it(PMI, mod(k, -hi_t, hi_t, L)), it(PMI, swap(k, True, -amt, MINP + 1))] + state(k)
                    its += [it(PMI, swap(k, False, amt, MAXP - 1)), it(PMI, swap(k, False, -(amt >> 64), MAXP - 1))] + state(k)
                    add(f'fallback sp={sp} t={t} L=2^{L.bit_length() - 1} amt={amt}', its)
                its = [it(PMI, init(k, price)), it(PMI, mod(k, -hi_t, hi_t, L))] + state(k)
                for e in (127, 140, 159, 160, 161, 170):
                    its += [it(PMI, swap(k, True, (1 << e) + 3, MINP + 1)), it(PMI, swap(k, False, (1 << e) + 3, MAXP - 1))] + state(k)
                add(f'exact output large sp={sp} t={t} L=2^{L.bit_length() - 1}', its)
    # The fallback is reached only when one swap step from a price below 2^96 runs to the bottom of the range: the
    # amount is then at least 2^256 / price, above 2^160, and the swap must end in the int128 cast of Pool.sol:455-459.
    for sp in (16383, 32767):
        hi_t = (887272 // sp) * sp
        for t, L in ((-60000, 1 << 121), (-100000, 1 << 119), (-150000, 1 << 116)):
            t = t // sp * sp if t // sp * sp > -hi_t else -hi_t + sp
            price = m.get_sqrt_price_at_tick(t) + 999; k = key(T0, T1, 0, sp, 0); num1 = L << 96
            for amt in [((1 << 256) - 1) // price + d for d in (-1, 0, 1)] + [((1 << 256) - num1) // price + d for d in (0, 1, 1000)]:
                its = [it(PMI, init(k, price)), it(PMI, mod(k, -hi_t, hi_t, L)), it(PMI, swap(k, True, -amt, MINP + 1))] + state(k)
                add(f'fallback low sp={sp} t={t} L=2^{L.bit_length() - 1} amt={amt}', its)
    # fee growth above 2^256 / liquidity: the 512 bit branch of mulDiv by 2^128 in Position.update
    for L in (1, 2, 3, 5, 1 << 20):
        k = key(T0, T1, 500, 60, 0)
        its = [it(PMI, init(k, 1 << 96)), it(PMI, mod(k, -600, 600, L)), it(PMI, donate(k, (1 << 127) - 1, (1 << 126)))]
        for _ in range(3):
            its += state(k) + [it(PMI, donate(k, (1 << 127) - 1, (1 << 127) - 1)), it(PMI, mod(k, -600, 600, 0))]
        its += [it(PMI, mod(k, -600, 600, -L)), it(PMI, mod(k, -600, 600, 1, 1))] + state(k)
        add(f'fee growth wrap L={L}', its)
    # amountRemainingLessFee of zero with a nonzero step input (SqrtPriceMath.sol:37)
    for fee in (999999, 999000, 1000000):
        k = key(T0, T1, fee, 10, 0)
        its = [it(PMI, init(k, 1 << 96)), it(PMI, mod(k, -1000, 1000, 10 ** 20))]
        for amt in (-1, -2, -999, 1, -10 ** 6):
            for zfo in (True, False): its.append(it(PMI, swap(k, zfo, amt, MINP + 1 if zfo else MAXP - 1))); its += state(k)
        add(f'fee {fee} tiny swaps', its)
    # 11. protocol fees and their collection, with the driver as owner and controller
    for cur in (0, T0, T1):
        k = key(cur, T1 if cur != T1 else BT, 3000, 60, 0)
        c1 = T1 if cur != T1 else BT
        its = [it(PMI, S['setPfc'] + w(DRV)), it(PMI, init(k, 1 << 96)), it(PMI, S['setFee'] + k + w(1000 | (1000 << 12))),
               it(PMI, S['setFee'] + k + w(1001)), it(PMI, S['setFee'] + k + w(1001 << 12)), it(PMI, S['setFee'] + k + w(0xffffff)),
               it(PMI, mod(k, -6000, 6000, 10 ** 20)), it(PMI, swap(k, True, -10 ** 18, MINP + 1)), it(PMI, swap(k, False, -10 ** 18, MAXP - 1)),
               it(PMI, swap(k, True, 10 ** 17, MINP + 1)), it(PMI, S['accrued'] + w(cur)), it(PMI, S['accrued'] + w(c1)),
               it(T1, TSET + w(10 ** 30)), it(BT, b'\x00\x00\x00\x02' + w(10 ** 30)), it(PMI, S['sync'] + w(c1)),
               it(PMI, S['collect'] + w(OTHER) + w(c1) + w(0)), it(PMI, S['collect'] + w(OTHER) + w(cur) + w(0)),
               it(PMI, S['collect'] + w(OTHER) + w(cur) + w(1)), it(PMI, S['sync'] + w(0)),
               it(PMI, S['collect'] + w(OTHER) + w(c1) + w(0)), it(PMI, S['collect'] + w(OTHER) + w(c1) + w(MASK)),
               it(PMI, S['accrued'] + w(cur)), it(PMI, S['accrued'] + w(c1)), it(PMI, S['transferOwnership'] + w(OTHER)),
               it(PMI, S['setPfc'] + w(OTHER)), it(PMI, S['collect'] + w(OTHER) + w(cur) + w(0))]
        add(f'protocol fees {cur:#x}', its)
    # 12. callback that returns data that is not abi encoded bytes
    add('callback returns 31 bytes', [it(PMI, S['owner'])], mode=2)
    for nm_, b in (('length above 2^64', w(0x20) + w(1 << 70)), ('offset above 2^64', w(1 << 70) + w(0)), ('length past the end', w(0x20) + w(0x40) + w(7)),
                   ('offset past the end', w(0x60) + w(1)), ('offset 0x20 length 0', w(0x20) + w(0)), ('offset 0x40', w(0x40) + w(0) + w(3) + b'abc'),
                   ('length 2^64 - 1', w(0x20) + w((1 << 64) - 1)), ('offset 2^64 - 1', w((1 << 64) - 1) + w(0)), ('empty', b''), ('32 bytes', w(0x20))):
        out.append((f'callback returns {nm_}', it(PMI, S['owner']) + raw_end(b)))
    # 12b. calldata of every function cut short or with offsets that point outside it
    import json as _j
    mids = _j.load(open(os.path.join(HERE, 'build-srcmap.json')))['methodIdentifiers'] if os.path.exists(os.path.join(HERE, 'build-srcmap.json')) else {}
    for sig, sh in sorted(mids.items()):
        sl = bytes.fromhex(sh)
        its = [it(PMI, sl + bytes(n)) for n in (0, 1, 31, 32, 33, 63, 64, 95, 96, 127, 128, 159, 160, 191, 192, 223, 255, 287, 319)]
        its += [it(PMI, sl + w(MASK) * k) for k in (1, 2, 3, 6, 7, 9, 10, 11)]
        its += [it(PMI, sl + w(1 << 64) * k) for k in (1, 3, 6, 7, 9, 10)]
        its += [it(PMI, sl + w(0x20) + w(1 << 64)), it(PMI, sl + w(0x20) + w((1 << 64) - 1)), it(PMI, sl + w(0x20) + w(5))]
        its += [it(PMI, sl + w(v) * k) for v in (0x1000, 0x40) for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)]
        its += [it(PMI, sl + w(32 * k - 1) * k) for k in (2, 3, 6, 7, 9, 10, 11)] + [it(PMI, sl + w(32 * k) * k) for k in (2, 3, 6, 7, 9, 10, 11)]
        add(f'short calldata {sig}', its)
    # 12c. the checked addition of the hook's specified delta (src/libraries/Hooks.sol:275)
    hk = HB | 0x0088; k = key(T0, T1, 3000, 60, hk)
    for spec, amt in ((-1, -(1 << 255)), (1, (1 << 255) - 1), (-(1 << 127), -(1 << 255) + 5), ((1 << 127) - 1, (1 << 255) - 10), (2, -1), (-2, 1), (5, -5), (-5, 5)):
        add(f'hook specified delta {spec} amount {amt}', [cfg(hk, d128(spec, 0)), it(PMI, init(k, 1 << 96)), it(PMI, mod(k, -600, 600, 10 ** 18)),
                                                          it(PMI, swap(k, True, amt, MINP + 1)), it(PMI, swap(k, False, amt, MAXP - 1))] + state(k, (DRV, hk)))
    add('callback returns record', [it(PMI, S['owner'])], mode=1)
    # 13. extsload and exttload of ranges
    for n in (0, 1, 2, 7, 64, 200):
        its = [it(PMI, S['extN'] + w(0) + w(n)), it(PMI, S['extN'] + w(MASK - 1) + w(n)),
               it(PMI, S['extA'] + w(0x20) + w(n) + b''.join(w(rnd.getrandbits(256)) for _ in range(n))),
               it(PMI, S['exttA'] + w(0x20) + w(n) + b''.join(w(x) for x in ([0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23] * n)))]
        add(f'ext ranges {n}', its)
    # 14. mint and burn with ids whose high bits are set, to and from address zero
    for idhi in (0, 1 << 160, MASK ^ ((1 << 160) - 1)):
        its = [it(PMI, S['mint'] + w(DRV) + w(T1 | idhi) + w(100)), it(PMI, S['mint'] + w(0) + w(T1 | idhi) + w(5)), it(PMI, S['mint'] + w(OTHER) + w(idhi) + w(9)),
               it(PMI, S['balanceOf'] + w(DRV) + w(T1)), it(PMI, S['balanceOf'] + w(DRV) + w(T1 | idhi)), it(PMI, S['balanceOf'] + w(0) + w(T1)),
               it(PMI, S['burn'] + w(DRV) + w(T1 | idhi) + w(60)), it(PMI, S['burn'] + w(0) + w(T1) + w(1)), it(PMI, S['burn'] + w(DRV) + w(T1) + w(41)),
               it(PMI, S['mint'] + w(DRV) + w(T1) + w((1 << 127) - 1)), it(PMI, S['mint'] + w(DRV) + w(T1) + w(1 << 127)),
               text(dslot(DRV, T1)), text(dslot(DRV, 0))]
        add(f'odd ids {idhi:#x}', its)
    return out


def unwrap(ret): return R.unwrap(ret)


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = P.fetch_code(); SC = scripts()
    ref = []; cover = set(); branches = {}; ops = {}; stats = {'scripts': len(SC), 'calls': 0, 'ok': 0, 'failed': 0, 'selectors': {}}
    for name, data in SC:
        wd = world(code); wd.max_steps = 20_000_000
        try:
            ok, ret = wd.call(0, DRV, 0, data, False, 0)
        except TimeoutError:
            ref.append(None); continue
        ref.append(ret); cover |= wd.cover.get(PMI, set())
        for (a, pc), o in wd.branches.items():
            if a == PMI: branches.setdefault(pc, set()).update(o)
        for o, c in wd.ops.items(): ops[o] = ops.get(o, 0) + c
        for k, r in P.parse(unwrap(ret) if data[:1] != b'\xff' else ret):
            stats['calls'] += 1; stats['ok' if k else 'failed'] += 1
            if not k: stats['selectors'][r[:4].hex() or 'empty'] = stats['selectors'].get(r[:4].hex() or 'empty', 0) + 1
    json.dump({'cover': sorted(cover), 'branches': {str(k): sorted(v) for k, v in branches.items()}, 'ops': {NAMES.get(o, hex(o)): c for o, c in ops.items()}},
              open(out.replace('.json', '-coverage.json'), 'w'))
    print('reference:', {k: v for k, v in stats.items() if k != 'selectors'}, 'too long:', sum(1 for r in ref if r is None), flush=True)
    refh = [hashlib.sha256(r).hexdigest() if r is not None else 'heavy' for r in ref]
    json.dump({'names': [n for n, _ in SC], 'reference': [r.hex() if r is not None else None for r in ref]}, open(out.replace('.json', '-reference.json'), 'w'))
    if os.environ.get('REF_ONLY'): sys.exit(0)
    ov = overrides(code)

    def ask(url, data, gas):
        last = None
        for k in range(5):
            try:
                return rpc(url, 'eth_call', [{'to': '0x' + DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=120)
            except Exception as e:  # noqa
                last = str(e)[:160]
                if 'gas' in last.lower() and ('limit' in last.lower() or 'cap' in last.lower()): break
                if 'revert' in last.lower() and '"data"' in last: break
                time.sleep(3 * (k + 1))
        return 'ERR ' + last

    def run_net(nw):
        cid, name, url = nw; res = []
        for i, (_, data) in enumerate(SC):
            if refh[i] == 'heavy': res.append('heavy'); continue
            r = ask(url, data, 25_000_000)
            h = hashlib.sha256(bytes.fromhex(r[2:])).hexdigest() if not r.startswith('ERR') else r
            if h != refh[i]:
                for gas in (2_000_000_000, 150_000_000, 50_000_000, 30_000_000):
                    r2 = ask(url, data, gas)
                    if not r2.startswith('ERR'):
                        h2 = hashlib.sha256(bytes.fromhex(r2[2:])).hexdigest()
                        if h2 == refh[i] or h.startswith('ERR'): h, r = h2, r2
                        break
            res.append((h, r if h != refh[i] else ''))
        return cid, name, res

    summary = []
    with cf.ThreadPoolExecutor(7) as ex:
        for cid, name, res in ex.map(run_net, [x for x in networks() if not only or x[0] in only]):
            hs = [x if isinstance(x, str) else x[0] for x in res]
            diff = [i for i, (a, b) in enumerate(zip(hs, refh)) if a != b and not a.startswith('ERR') and a != 'heavy']
            err = [i for i, a in enumerate(hs) if a.startswith('ERR')]
            same = sum(1 for a, b in zip(hs, refh) if a == b and a != 'heavy')
            print(f'{cid:>8} {name:16} equal to the reference {same}/{len(SC)} different {len(diff)} errors {len(err)} {[hs[i][:100] for i in err[:1]]}', flush=True)
            summary.append({'chainId': cid, 'name': name, 'identical': same, 'different': diff, 'errors': err,
                            'differentAnswers': {str(i): res[i][1] for i in diff}, 'errorText': {str(i): hs[i] for i in err}})
    json.dump({'scripts': len(SC), 'names': [n for n, _ in SC], 'reference': stats, 'results': summary, 'referenceHashes': refh}, open(out, 'w'), indent=1)
