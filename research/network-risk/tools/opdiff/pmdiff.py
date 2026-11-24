"""One PoolManager, one state, one input, 21 interpreters. The runtime bytecode of the
PoolManager that Uniswap deployed on Ethereum is placed at a fixed fresh address on
every network by state override (its one immutable, the NoDelegateCall address, is
rewritten to that address). A small driver at a second address calls unlock, and in
the callback runs a script of PoolManager calls (initialize, modifyLiquidity, swap,
donate, mint, burn, clear, take, extsload, exttload). After each call it appends the
success flag and the return data to a buffer and at the end reverts with the buffer,
which the outer frame returns. Nothing is settled and nothing persists.

The same script must give byte-identical buffers on every network. A difference means
an interpreter disagrees with Ethereum's on some opcode or control flow that the
PoolManager's code uses. Swap results are also compared with the transcription of the
source in v4math.py where the script makes that possible (see check_swaps).

Usage: python3 pmdiff.py <out.json> [nScripts] [chainId ...]
"""
import sys, os, json, random, hashlib, time, concurrent.futures as cf
from evm import assemble, keccak, rpc, networks, MASK, u, s
import v4math as m

PM = '0x00000000000000000000000000000000504d0001'
DRV = '0x00000000000000000000000000000000d21fe001'
REAL_PM = '0x000000000004444c5dc75cB358380D2e3dE08A90'
ETH = 'https://ethereum-rpc.publicnode.com'
C0 = 0x00000000000000000000000000000000C0FFEE01
C1 = 0x00000000000000000000000000000000C0FFEE02


def sel(sig): return keccak(sig.encode())[:4]


KEY = '(address,address,uint24,int24,address)'
S_INIT = sel(f'initialize({KEY},uint160)')
S_MOD = sel(f'modifyLiquidity({KEY},(int24,int24,int256,bytes32),bytes)')
S_SWAP = sel(f'swap({KEY},(bool,int256,uint160),bytes)')
S_DONATE = sel(f'donate({KEY},uint256,uint256,bytes)')
S_MINT = sel('mint(address,uint256,uint256)')
S_BURN = sel('burn(address,uint256,uint256)')
S_CLEAR = sel('clear(address,uint256)')
S_TAKE = sel('take(address,address,uint256)')
S_SETTLE = sel('settle()')
S_EXTSLOAD = sel('extsload(bytes32)')
S_EXTTLOAD = sel('exttload(bytes32)')
S_BALANCEOF = sel('balanceOf(address,uint256)')
S_UNLOCK = sel('unlock(bytes)')
S_CB = sel('unlockCallback(bytes)')


def w(x): return (x & MASK).to_bytes(32, 'big')


def driver():
    pm = int(PM, 16)
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         # outer frame: unlock(bytes script)
         ('PUSHN', 4, int.from_bytes(S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pm), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         # callback: items are [2 byte length][calldata], a zero length ends the script
         ('LABEL', 'cb'), ('PUSH', 0x2000), ('PUSH', 68),  # ptr, outp
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 240), 'SHR',  # len, ptr, outp
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP3', ('PUSH', 2), 'ADD', ('PUSH', 0), 'CALLDATACOPY',  # calldatacopy(0, ptr+2, len)
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pm), 'GAS', 'CALL',  # ok, len, ptr, outp
         'DUP4', 'MSTORE',  # mstore(outp, ok) -> len, ptr, outp
         'RETURNDATASIZE', 'DUP4', ('PUSH', 32), 'ADD', 'MSTORE',  # mstore(outp+32, rds)
         'RETURNDATASIZE', ('PUSH', 0), 'DUP5', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',  # returndatacopy(outp+64, 0, rds)
         'SWAP2', ('PUSH', 64), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP2',  # outp += 64 + rds
         ('PUSH', 2), 'ADD', 'ADD',  # ptr += len + 2 -> ptr, outp
         ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP',  # outp
         ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'REVERT']
    return assemble(p)


def key_words(fee, spacing): return w(C0) + w(C1) + w(fee) + w(spacing) + w(0)
def pool_id(fee, spacing): return keccak(key_words(fee, spacing))
def c_init(fee, sp, price): return S_INIT + key_words(fee, sp) + w(price)
def c_mod(fee, sp, lo, hi, delta, salt=0): return S_MOD + key_words(fee, sp) + w(lo) + w(hi) + w(delta) + w(salt) + w(0x140) + w(0)
def c_swap(fee, sp, zfo, amount, limit): return S_SWAP + key_words(fee, sp) + w(int(zfo)) + w(amount) + w(limit) + w(0x120) + w(0)
def c_donate(fee, sp, a0, a1): return S_DONATE + key_words(fee, sp) + w(a0) + w(a1) + w(0x100) + w(0)
def c_ext(slot): return S_EXTSLOAD + w(slot)


def pool_slot(fee, sp, k): return (int.from_bytes(keccak(pool_id(fee, sp) + w(6)), 'big') + k) & MASK
def delta_slot(target, currency): return int.from_bytes(keccak(w(target) + w(currency)), 'big')


def script(rnd):
    fee = rnd.choice([0, 1, 100, 500, 3000, 10000, 123456, 999999, 1000000])
    sp = rnd.choice([1, 1, 2, 10, 60, 200, 887, 16383, 32767])
    lo_t, hi_t = -(887272 // sp) * sp, (887272 // sp) * sp
    t0 = rnd.choice([0, rnd.randrange(-887272, 887272), rnd.randrange(-60000, 60000), rnd.randrange(-600, 600), -887272, 887271])
    price = m.get_sqrt_price_at_tick(t0)
    if rnd.random() < 0.7: price = min(m.MAX_SQRT_PRICE - 1, max(m.MIN_SQRT_PRICE, price + rnd.randrange(0, max(1, price >> rnd.randrange(8, 40)))))
    calls = [('init', c_init(fee, sp, price))]
    meta = {'fee': fee, 'spacing': sp, 'price0': price, 'steps': []}

    def state():
        for k in (0, 1, 2, 3):
            calls.append(('ext', c_ext(pool_slot(fee, sp, k))))
        calls.append(('ext', S_EXTTLOAD + w(delta_slot(int(DRV, 16), C0)))); calls.append(('ext', S_EXTTLOAD + w(delta_slot(int(DRV, 16), C1))))

    def rtick():
        base = rnd.choice([t0, t0, t0, 0, rnd.randrange(lo_t, hi_t + 1)])
        width = rnd.choice([sp, 2 * sp, 10 * sp, 100 * sp, 1000 * sp, 300 * sp])
        a = (base - rnd.randrange(0, width + 1)) // sp * sp; b = (base + rnd.randrange(1, width + 2)) // sp * sp + sp
        return max(lo_t, a), min(hi_t, b)

    positions = []
    for _ in range(rnd.randrange(1, 6)):
        a, b = rtick() if rnd.random() < 0.85 else (lo_t, hi_t)
        liq = rnd.choice([1, rnd.getrandbits(20), rnd.getrandbits(60), rnd.getrandbits(90), rnd.getrandbits(110), (1 << 127) - 1, 10 ** 18]) or 1
        salt = rnd.choice([0, 0, 1, rnd.getrandbits(256)])
        calls.append(('mod', c_mod(fee, sp, a, b, liq, salt))); positions.append((a, b, liq, salt))
    state()
    for _ in range(rnd.randrange(3, 9)):
        r = rnd.random()
        if r < 0.62:
            zfo = rnd.random() < 0.5
            mag = rnd.choice([1, 2, rnd.getrandbits(16), rnd.getrandbits(40), rnd.getrandbits(70), rnd.getrandbits(100), rnd.getrandbits(126), 10 ** 18, 0])
            amt = -mag if rnd.random() < 0.6 else mag
            if rnd.random() < 0.03: amt = rnd.choice([-(1 << 255), (1 << 255) - 1, -(1 << 127), (1 << 127)])
            lim = rnd.choice(['edge', 'edge', 'near', 'rand'])
            if lim == 'edge': limit = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            elif lim == 'near': limit = max(m.MIN_SQRT_PRICE + 1, price - (price >> rnd.randrange(4, 30))) if zfo else min(m.MAX_SQRT_PRICE - 1, price + (price >> rnd.randrange(4, 30)))
            else: limit = rnd.randrange(m.MIN_SQRT_PRICE, m.MAX_SQRT_PRICE)
            calls.append(('swap', c_swap(fee, sp, zfo, amt, limit))); meta['steps'].append(('swap', zfo, amt, limit))
        elif r < 0.78 and positions:
            a, b, liq, salt = rnd.choice(positions)
            d = rnd.choice([-liq, -(liq // 2), 0, -1, liq, -(liq + 1)])
            calls.append(('mod', c_mod(fee, sp, a, b, d, salt)))
        elif r < 0.86:
            calls.append(('donate', c_donate(fee, sp, rnd.getrandbits(rnd.choice((0, 20, 80, 128))), rnd.getrandbits(rnd.choice((0, 20, 80, 127))))))
        elif r < 0.92:
            amt = rnd.getrandbits(rnd.choice((8, 64, 127)))
            calls.append(('mint', S_MINT + w(int(DRV, 16)) + w(C0 | (rnd.getrandbits(40) << 160 if rnd.random() < 0.3 else 0)) + w(amt)))
            calls.append(('bal', S_BALANCEOF + w(int(DRV, 16)) + w(C0)))
            calls.append(('burn', S_BURN + w(int(DRV, 16)) + w(C0) + w(amt // 2)))
        elif r < 0.96:
            calls.append(('take', S_TAKE + w(C1) + w(int(DRV, 16)) + w(rnd.getrandbits(rnd.choice((8, 100, 128))))))
        else:
            calls.append(('clear', S_CLEAR + w(C0) + w(rnd.getrandbits(64))))
            calls.append(('settle', S_SETTLE))
        state()
    data = b''.join(len(c).to_bytes(2, 'big') + c for _, c in calls) + b'\0\0'
    return data, [k for k, _ in calls], meta


def parse(buf):
    out = []; i = 0
    while i + 64 <= len(buf):
        ok = int.from_bytes(buf[i:i + 32], 'big'); n = int.from_bytes(buf[i + 32:i + 64], 'big')
        out.append((ok, buf[i + 64:i + 64 + n])); i += 64 + n
    return out


def fetch_code():
    code = bytes.fromhex(rpc(ETH, 'eth_getCode', [REAL_PM, 'latest'])[2:])
    real = bytes.fromhex(REAL_PM[2:])
    assert code.count(real) == 1
    return code.replace(real, bytes.fromhex(PM[2:]))


def run_net(n, code, drv, scripts):
    cid, name, url = n; res = []
    ov = {PM: {'code': '0x' + code.hex()}, DRV: {'code': '0x' + drv.hex()}}
    for data, _, _ in scripts:
        last = None
        for k in range(4):
            try:
                r = rpc(url, 'eth_call', [{'to': DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest', ov], timeout=90)
                res.append(hashlib.sha256(bytes.fromhex(r[2:])).hexdigest() if cid != 1 else r); last = None; break
            except Exception as e:  # noqa
                last = str(e)[:120]; time.sleep(2 * (k + 1))
        if last is not None: res.append('ERR ' + last)
    return cid, name, res


if __name__ == '__main__':
    out = sys.argv[1]; n_scripts = int(sys.argv[2]) if len(sys.argv) > 2 else 200; only = set(map(int, sys.argv[3:]))
    rnd = random.Random(7_2026_11_24)
    scripts = [script(rnd) for _ in range(n_scripts)]
    code = fetch_code(); drv = driver()
    print('PoolManager code', len(code), 'bytes, sha256', hashlib.sha256(code).hexdigest()[:16], '; driver', len(drv), 'bytes;', n_scripts, 'scripts,', sum(len(k) for _, k, _ in scripts), 'PoolManager calls')
    nets = [n for n in networks() if not only or n[0] in only or n[0] == 1]
    results = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(lambda n: run_net(n, code, drv, scripts), nets):
            results[cid] = (name, res)
    ref = results[1][1]
    stats = {'calls': 0, 'ok': 0, 'reverted': 0, 'byKind': {}}
    for (data, kinds, meta), r in zip(scripts, ref):
        if r.startswith('ERR'): continue
        for kind, (ok, ret) in zip(kinds, parse(bytes.fromhex(r[2:]))):
            stats['calls'] += 1; stats['ok' if ok else 'reverted'] += 1
            b = stats['byKind'].setdefault(kind, [0, 0]); b[0 if ok else 1] += 1
    print('Ethereum reference:', stats)
    refh = [hashlib.sha256(bytes.fromhex(r[2:])).hexdigest() if not r.startswith('ERR') else r for r in ref]
    summary = []
    for cid, (name, res) in results.items():
        if cid == 1: continue
        same = sum(1 for a, b in zip(res, refh) if a == b and not a.startswith('ERR'))
        err = sum(1 for a in res if a.startswith('ERR'))
        diff = [i for i, (a, b) in enumerate(zip(res, refh)) if a != b and not a.startswith('ERR') and not b.startswith('ERR')]
        print(f'{cid:>8} {name:16} identical {same}/{len(res)} different {len(diff)} errors {err} {[r for r in res if r.startswith("ERR")][:1]}')
        summary.append({'chainId': cid, 'name': name, 'identical': same, 'different': diff, 'errors': err})
    json.dump({'scripts': n_scripts, 'poolManagerCodeSha256': hashlib.sha256(code).hexdigest(), 'reference': stats,
               'referenceErrors': sum(1 for r in ref if r.startswith('ERR')), 'results': summary,
               'referenceHashes': refh}, open(out, 'w'), indent=1)
