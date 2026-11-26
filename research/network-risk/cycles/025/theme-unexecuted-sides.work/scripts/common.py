"""Shared pieces for theme-unexecuted-sides (cycle 25): codes, case encoding, output decoding.

The driver (src/Driver.sol, compiled by compile_driver.js into build/driver.json) runs inside one eth_call. The
PoolManager code is the build of this checkout (research/network-risk/build/PoolManager.json) with its immutable set
to the real PoolManager address of the network, placed by override at that address. Token doubles: one Tok
implementation at IMPL and a 30 byte delegating forwarder at every currency address.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
NR = os.path.abspath(os.path.join(WORK, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import assemble, keccak  # noqa: E402

M = (1 << 256) - 1
D = 0x00000000000000000000000000000000d0d04000   # driver; low 14 bits zero so it can be a no-flag dynamic fee hook
S = 0x0000000000000000000000000000000055550000   # second actor (same code)
IMPL = 0x0000000000000000000000000000000000007070
EOA = 0x00000000000000000000000000000000000a11ce
B_ = 0xB0B
R_ = 0xC0C
PLACEHOLDER = bytes.fromhex('a11ce5a11ce5a11ce5a11ce5a11ce5a11ce5a11c')
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342
MIN_TICK, MAX_TICK = -887272, 887272

_b = json.load(open(os.path.join(WORK, 'build', 'driver.json')))
DRIVER_RAW = bytes.fromhex(_b['driver'])
TOK = bytes.fromhex(_b['tok'])
SEL_RUN = bytes.fromhex(_b['methods']['run(bytes[])'])
assert DRIVER_RAW.count(PLACEHOLDER) >= 1


def driver(pm):
    return DRIVER_RAW.replace(PLACEHOLDER, pm.to_bytes(20, 'big'))


def pm_build(pm):
    b = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))
    code = bytearray.fromhex(b['runtime'])
    refs = [r for v in b['immutableReferences'].values() for r in v]
    assert len(refs) == 1 and refs[0]['length'] == 32
    code[refs[0]['start']:refs[0]['start'] + 32] = pm.to_bytes(32, 'big')
    return bytes(code)


FWD = assemble(['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', IMPL), 'GAS', 'DELEGATECALL',
                'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'ok'), 'JUMPI',
                'RETURNDATASIZE', ('PUSH', 0), 'REVERT', ('LABEL', 'ok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN'])


def w(x):
    return (x & M).to_bytes(32, 'big')


def enc_case(c):
    """abi.encode(C) for the struct of Driver.sol."""
    p = c.get('p', [])
    head = [c['kind'], c.get('t0', 0), c.get('t1', 0), c.get('fee', 0), c.get('ts', 0), c.get('hooks', 0), c.get('sqrtP', 0),
            c.get('tl', 0), c.get('tu', 0), c.get('liq', 0), int(bool(c.get('zfo', False))), c.get('amt', 0), c.get('lim', 0)]
    body = b''.join(w(x) for x in head) + w(14 * 32) + w(len(p)) + b''.join(w(x) for x in p)
    return w(0x20) + body


def enc_run(cases):
    blobs = [enc_case(c) for c in cases]
    offs = []; tail = b''; base = 32 * len(blobs)
    for bl in blobs:
        offs.append(base + len(tail))
        pad = bl + b'\0' * ((-len(bl)) % 32)
        tail += w(len(bl)) + pad
    return SEL_RUN + w(0x20) + w(len(blobs)) + b''.join(w(o) for o in offs) + tail


def _word(b, i):
    return int.from_bytes(b[i:i + 32], 'big')


def dec_run(ret):
    """Returns list of (ok, words or None, raw revert bytes)."""
    off = _word(ret, 0); n = _word(ret, off); arr = off + 32
    out = []
    for k in range(n):
        o = arr + _word(ret, arr + 32 * k)
        ln = _word(ret, o); blob = ret[o + 32:o + 32 + ln]
        ok = _word(blob, 0); boff = _word(blob, 32); bl = _word(blob, boff); inner = blob[boff + 32:boff + 32 + bl]
        if ok:
            # unlock returns abi.encode(bytes) of the callback's abi.encode(uint256[])
            o2 = _word(inner, 0); l2 = _word(inner, o2); cb = inner[o2 + 32:o2 + 32 + l2]
            o3 = _word(cb, 0); n3 = _word(cb, o3)
            out.append((1, [_word(cb, o3 + 32 + 32 * i) for i in range(n3)], b''))
        else:
            out.append((0, None, inner))
    return out


def codes_for(pm, cases):
    codes = {pm: pm_build(pm), D: driver(pm), S: driver(pm), IMPL: TOK}
    for c in cases:
        for t in (c.get('t0'), c.get('t1')):
            if t: codes[t] = FWD
    return codes


def overrides(pm, cases, with_pm=True):
    ov = {}
    for a, code in codes_for(pm, cases).items():
        if a == pm and not with_pm:
            continue
        ov['0x%040x' % a] = {'code': '0x' + code.hex()}
    return ov


# ---- PoolManager calldata (own encoder; static tuples are inlined, one trailing empty bytes argument) ----
_PMB = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))['methodIdentifiers']


def sel(sig):
    return bytes.fromhex(_PMB[sig])


def key_words(c):
    return [c['t0'], c['t1'], c['fee'], c['ts'], c.get('hooks', 0)]


def pm_call(sig, words, with_bytes=False):
    """words: the static head words; with_bytes appends an empty bytes argument at the end."""
    if with_bytes:
        n = len(words) + 1
        return sel(sig) + b''.join(w(x) for x in words) + w(32 * n) + w(0)
    return sel(sig) + b''.join(w(x) for x in words)


KEY = '(address,address,uint24,int24,address)'


def c_init(c, sqrtP): return pm_call(f'initialize({KEY},uint160)', key_words(c) + [sqrtP])
def c_mlp(c, tl, tu, liq, salt=0): return pm_call(f'modifyLiquidity({KEY},(int24,int24,int256,bytes32),bytes)', key_words(c) + [tl, tu, liq, salt], True)
def c_swap(c, zfo, amt, lim): return pm_call(f'swap({KEY},(bool,int256,uint160),bytes)', key_words(c) + [int(zfo), amt, lim], True)
def c_donate(c, a0, a1): return pm_call(f'donate({KEY},uint256,uint256,bytes)', key_words(c) + [a0, a1], True)
def c_simple(sig, *args): return pm_call(sig, list(args))


def raw_p(mint0, mint1, settle, calls):
    p = [mint0, mint1, int(settle), len(calls)]
    for data in calls:
        p.append(len(data)); pad = data + b'\0' * ((-len(data)) % 32)
        p += [int.from_bytes(pad[i:i + 32], 'big') for i in range(0, len(pad), 32)]
    return p


def pool_id(c):
    return int.from_bytes(keccak(b''.join(w(x) for x in key_words(c))), 'big')


def pool_slot(c):
    return int.from_bytes(keccak(w(pool_id(c)) + w(6)), 'big')


def slot0_word(sqrtP, tick, protocolFee=0, lpFee=0):
    return (sqrtP & ((1 << 160) - 1)) | ((tick & 0xffffff) << 160) | (protocolFee << 184) | (lpFee << 208)


def enc_bytes_array(sel4, blobs):
    offs = []; tail = b''; base = 32 * len(blobs)
    for bl in blobs:
        offs.append(base + len(tail)); tail += w(len(bl)) + bl + b'\0' * ((-len(bl)) % 32)
    return sel4 + w(0x20) + w(len(blobs)) + b''.join(w(o) for o in offs) + tail


SEL_OUTSIDE = bytes.fromhex(_b['methods']['outside(bytes[])'])


def dec_outside(ret):
    off = _word(ret, 0); n = _word(ret, off); arr = off + 32; out = []
    for k in range(n):
        o = arr + _word(ret, arr + 32 * k); ln = _word(ret, o); blob = ret[o + 32:o + 32 + ln]
        ok = _word(blob, 0); boff = _word(blob, 32); bl = _word(blob, boff)
        out.append((ok, blob[boff + 32:boff + 32 + bl].hex()))
    return out
