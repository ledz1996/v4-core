"""Shared pieces for theme-stateful-interpreter (cycle 26): sequence construction, ABI encoding, overrides, decoding.

The driver is src/Seq.sol compiled by compile_seq.js into build/seq.json. The PoolManager is the build of this checkout
(research/network-risk/build/PoolManager.json) with its immutable set to the network's real PoolManager address and
placed there by state override. Nothing is deployed and nothing is sent; eth_call only.
Sequences are deterministic; the only random choice (group G4 liquidities and the mode 6 amounts) uses SEED.
"""
import os, sys, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
NR = os.path.abspath(os.path.join(WORK, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import assemble, keccak  # noqa: E402

SEED = 2026112661
M = (1 << 256) - 1
D = 0xd0d04000
IMPL = 0x7070
HK = 0xbeef0040          # low 14 bits 0x0040 = AFTER_SWAP_FLAG (src/libraries/Hooks.sol:39)
HK2 = 0xbeef0080         # low 14 bits 0x0080 = BEFORE_SWAP_FLAG (src/libraries/Hooks.sol:38)
EOA = 0xa11ce
PLACE = bytes.fromhex('a11ce5a11ce5a11ce5a11ce5a11ce5a11ce5a11c')
B = json.load(open(os.path.join(WORK, 'build', 'seq.json')))
FWD = assemble(['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', IMPL), 'GAS', 'DELEGATECALL',
                'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'ok'), 'JUMPI',
                'RETURNDATASIZE', ('PUSH', 0), 'REVERT', ('LABEL', 'ok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN'])


def pm_build(pm):
    b = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))
    code = bytearray.fromhex(b['runtime'])
    refs = [r for v in b['immutableReferences'].values() for r in v]
    assert len(refs) == 1 and refs[0]['length'] == 32
    code[refs[0]['start']:refs[0]['start'] + 32] = pm.to_bytes(32, 'big')
    return bytes(code)


def rt(name, pm):
    return bytes.fromhex(B[name]['runtime']).replace(PLACE, pm.to_bytes(20, 'big'))


# ---------------- minimal ABI encoder ----------------
def w(x):
    return (x & M).to_bytes(32, 'big')


def enc(types, vals):
    """types: 'u' (any static word), 'b' (bytes), 'a' (dynamic array of words), ('t', n) static tuple of n words."""
    heads = []; tails = b''
    hl = sum(32 * (t[1] if isinstance(t, tuple) else 1) for t in types)
    for t, v in zip(types, vals):
        if isinstance(t, tuple):
            heads.append(b''.join(w(x) for x in v))
        elif t == 'u':
            heads.append(w(v))
        else:
            heads.append(w(hl + len(tails)))
            if t == 'b':
                tails += w(len(v)) + v + b'\0' * ((-len(v)) % 32)
            else:
                tails += w(len(v)) + b''.join(w(x) for x in v)
    return b''.join(heads) + tails


def step(mode, args):
    return enc(['u', 'b'], [mode, args])


def enc_run(steps):
    sel = bytes.fromhex(B['Seq']['methods']['run(bytes[])'])
    offs = []; tail = b''; base = 32 * len(steps)
    for s in steps:
        offs.append(base + len(tail)); tail += w(len(s)) + s + b'\0' * ((-len(s)) % 32)
    return sel + w(0x20) + w(len(steps)) + b''.join(w(o) for o in offs) + tail


def _word(b, i):
    return int.from_bytes(b[i:i + 32], 'big')


def dec_run(ret):
    off = _word(ret, 0); n = _word(ret, off); arr = off + 32; out = []
    for k in range(n):
        o = arr + _word(ret, arr + 32 * k); ln = _word(ret, o); blob = ret[o + 32:o + 32 + ln]
        ok = _word(blob, 0); bo = _word(blob, 32); cnt = _word(blob, bo)
        if ok:
            out.append({'ok': 1, 'w': [hex(_word(blob, bo + 32 + 32 * i)) for i in range(cnt)]})
        else:
            out.append({'ok': 0, 'revert': blob[bo + 32:bo + 32 + cnt].hex()})
    return out


# ---------------- sequences ----------------
def tok(pair):
    return 0xa0000 + 2 * pair, 0xa0001 + 2 * pair


MIN_P = 4295128740
Q96 = 1 << 96


def pools16():
    r = random.Random(SEED)
    fee = [100 + 37 * i for i in range(16)]
    ts = [60] * 16
    L = []
    L += [(1 << 100) + i * (1 << 20) for i in range(4)]            # G1: denominators share limb 3, differ in limb 1
    L += [(1 << 100) + k * (1 << 96) for k in range(1, 5)]          # G2: L<<96 differs only in limb 3 (bit 192 and up)
    L += [(1 << 101) - 1 - i for i in range(4)]                     # G3: differ in the low bits of limb 1
    L += [r.randrange(1 << 96, 1 << 105) for _ in range(4)]         # G4: random
    return fee, ts, L


def setup_step(pair, fee, ts, L, sqrtP=Q96, hooks=0):
    t0, t1 = tok(pair)
    return step(1, enc(['u', 'u', 'a', 'a', 'a', 'u', 'u'], [t0, t1, fee, ts, L, sqrtP, hooks]))


def swaps_step(pair, fee, ts, zfo, amt, rev=False):
    t0, t1 = tok(pair)
    return step(3 if rev else 2, enc(['u', 'u', 'a', 'a', 'a', 'a'], [t0, t1, fee, ts, [int(z) for z in zfo], amt]))


def round_params(r, n=16):
    """Round r of sequence (a): direction alternates per round and per pool; every fourth pair of rounds is exact output."""
    zfo = [((r + i) % 2 == 0) for i in range(n)]
    out = (r // 2) % 4 == 3
    base = (1 << 88) + r * 0x10001
    amt = [(base >> (i % 3)) if out else -(base + (i << 64)) for i in range(n)]
    return zfo, amt


def seq_a(rounds, sub=None):
    fee, ts, L = pools16()
    if sub is not None:  # smaller variant for endpoints whose gas cap cannot hold 16 pools (Tempo)
        fee, ts, L = [fee[i] for i in sub], [ts[i] for i in sub], [L[i] for i in sub]
        steps = [setup_step(0, fee, ts, L)]
        for r in range(rounds):
            z, a = round_params(r, len(fee))
            steps.append(swaps_step(0, fee, ts, z, a))
        return steps
    steps = [setup_step(0, fee[:8], ts[:8], L[:8]), setup_step(0, fee[8:], ts[8:], L[8:])]
    for r in range(rounds):
        z, a = round_params(r)
        steps.append(swaps_step(0, fee, ts, z, a))
    return steps


def key(pair, fee, ts, hooks=0):
    t0, t1 = tok(pair)
    return [t0, t1, fee, ts, hooks]


def seq_b(sub=None):
    fee, ts, L = pools16()
    if sub is not None:
        fee, ts, L = [fee[i] for i in sub], [ts[i] for i in sub], [L[i] for i in sub]
    LA = (1 << 100) + 12345
    steps = [setup_step(0, fee[:8], ts[:8], L[:8]), setup_step(0, fee[8:], ts[8:], L[8:])] if sub is None else [setup_step(0, fee, ts, L)]
    for p in (2, 3, 4, 5):
        steps.append(setup_step(p, [3000], [60], [LA]))
    za, aa = True, -((1 << 88) + 777)
    steps.append(swaps_step(2, [3000], [60], [za], [aa]))                       # reference swap on A
    z, a = round_params(5, len(fee))
    steps.append(swaps_step(0, fee, ts, z, a, rev=True))                        # 16 other denominators, unlock reverted
    steps.append(swaps_step(3, [3000], [60], [za], [aa]))                       # same swap on an identical pool
    zb, ab = False, (1 << 87) + 3                                                # exact output 0 out: line 71 path
    steps.append(step(4, enc([('t', 5), ('t', 5), ('t', 5), 'u', 'u', 'u', 'u'],
                             [key(4, 3000, 60), key(5, 3000, 60), key(0, fee[min(6, len(fee) - 1)], 60), int(za), aa, int(zb), ab])))
    return steps


def seq_c():
    LA = (1 << 70) + 99
    return [setup_step(6, [500], [10], [LA]), setup_step(7, [500], [10], [LA], hooks=HK),
            step(5, enc([('t', 5), ('t', 5)], [key(6, 500, 10), key(7, 500, 10, HK)]))]


def seq_c2():
    LA = (1 << 70) + 99
    return [setup_step(6, [500], [10], [LA]), setup_step(9, [500], [10], [LA], hooks=HK2),
            step(5, enc([('t', 5), ('t', 5)], [key(6, 500, 10), key(9, 500, 10, HK2)]))]


def seq_d(n=300):
    return [step(6, enc(['u', 'u', 'u'], [0x1000000, n, SEED]))]


META_SALT = None


def meta_addr(salt):
    init = bytes.fromhex(B['Meta']['init'])
    h = keccak(b'\xff' + D.to_bytes(20, 'big') + salt.to_bytes(32, 'big') + keccak(init))
    return int.from_bytes(h[12:], 'big')


def mine_salt():
    s = 0
    while (meta_addr(s) & 0x3fff) != 0x0040:
        s += 1
    return s


def seq_e(salt):
    t0, t1 = tok(8)
    return [step(7, enc(['u', 'u', 'b', 'b', 'u'], [t0, t1, bytes.fromhex(B['HkA']['runtime']), bytes.fromhex(B['HkB']['runtime']), salt]))]


def all_tokens():
    return [a for p in range(10) for a in tok(p)]


def codes(pm, direct=False):
    """direct=True places the token double's own code at every currency address instead of a DELEGATECALL forwarder
    (for the Monad harness, which runs the recipient's code for DELEGATECALL)."""
    c = {pm: pm_build(pm), D: rt('Seq', pm), HK: rt('Hk', pm), HK2: rt('Hk2', pm), IMPL: bytes.fromhex(B['Tok']['runtime'])}
    for t in all_tokens():
        c[t] = bytes.fromhex(B['Tok']['runtime']) if direct else FWD
    return c


def overrides(pm):
    return {'0x%040x' % a: {'code': '0x' + v.hex()} for a, v in codes(pm).items()}


def sequences(salt):
    return {'a64': seq_a(4), 'a512': seq_a(32), 'b': seq_b(), 'c': seq_c(), 'c2': seq_c2(), 'd300': seq_d(300), 'e': seq_e(salt),
            'a64t': seq_a(16, [0, 4, 8, 12]), 'bt': seq_b([0, 4, 8, 12]), 'd40': seq_d(40)}
