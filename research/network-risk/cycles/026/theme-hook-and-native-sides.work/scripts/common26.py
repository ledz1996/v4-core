"""Shared pieces for theme-hook-and-native-sides (cycle 26): addresses, codes, case encoding, output decoding.

The driver (src/Driver26.sol, compiled by compile_driver.js into build/driver.json with solc-js 0.8.26) runs inside one
eth_call. The PoolManager code is the build of this checkout (research/network-risk/build/PoolManager.json) with its
immutable set to the real PoolManager address of the network, placed by override at that address with a fixed native
balance. Token doubles as in cycle 25 (one Tok implementation, a delegating forwarder per currency). The hook double Hk
is placed at every hook address of the batch. The driver D holds a fixed native balance by override.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
NR = os.path.abspath(os.path.join(WORK, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import assemble, keccak  # noqa: E402

M = (1 << 256) - 1
D = 0x00000000000000000000000000000000d0d04000
S = 0x0000000000000000000000000000000055550000
IMPL = 0x0000000000000000000000000000000000007070
EOA = 0x00000000000000000000000000000000000a11ce
REJ = 0x00000000000000000000000000000000dead0001   # code PUSH0 PUSH0 REVERT: rejects every call
PM_BAL = 10 ** 27
D_BAL = 10 ** 30
PLACEHOLDER = bytes.fromhex('a11ce5a11ce5a11ce5a11ce5a11ce5a11ce5a11c')
PH_INT = int.from_bytes(PLACEHOLDER, 'big')
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342

_b = json.load(open(os.path.join(WORK, 'build', 'driver.json')))
DRIVER_RAW = bytes.fromhex(_b['driver'])
HK_RAW = bytes.fromhex(_b['hk'])
TOK = bytes.fromhex(_b['tok'])
SEL_RUN = bytes.fromhex(_b['methods']['run(bytes[])'])
HSEL = {k.split('(')[0]: int(v, 16) for k, v in _b['hooks'].items()}
assert DRIVER_RAW.count(PLACEHOLDER) >= 1 and HK_RAW.count(PLACEHOLDER) >= 1

FWD = assemble(['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', IMPL), 'GAS', 'DELEGATECALL',
                'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'ok'), 'JUMPI',
                'RETURNDATASIZE', ('PUSH', 0), 'REVERT', ('LABEL', 'ok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN'])
REJ_CODE = bytes.fromhex('5f5ffd')


def driver(pm): return DRIVER_RAW.replace(PLACEHOLDER, pm.to_bytes(20, 'big'))
def hk(pm): return HK_RAW.replace(PLACEHOLDER, pm.to_bytes(20, 'big'))


def pm_build(pm):
    b = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))
    code = bytearray.fromhex(b['runtime'])
    refs = [r for v in b['immutableReferences'].values() for r in v]
    assert len(refs) == 1 and refs[0]['length'] == 32
    code[refs[0]['start']:refs[0]['start'] + 32] = pm.to_bytes(32, 'big')
    return bytes(code)


def w(x): return (x & M).to_bytes(32, 'big')


def sub_pm(x, pm): return pm if x == PH_INT else x


def enc_case(c, pm):
    p = [sub_pm(x, pm) for x in c.get('p', [])]
    head = [20, c.get('t0', 0), c.get('t1', 0), c.get('fee', 0), c.get('ts', 0), c.get('hooks', 0), 0, 0, 0, 0, 0, 0, 0]
    return w(0x20) + b''.join(w(x) for x in head) + w(14 * 32) + w(len(p)) + b''.join(w(x) for x in p)


def enc_run(cases, pm):
    blobs = [enc_case(c, pm) for c in cases]
    offs = []; tail = b''; base = 32 * len(blobs)
    for bl in blobs:
        offs.append(base + len(tail)); tail += w(len(bl)) + bl + b'\0' * ((-len(bl)) % 32)
    return SEL_RUN + w(0x20) + w(len(blobs)) + b''.join(w(o) for o in offs) + tail


def _word(b, i): return int.from_bytes(b[i:i + 32], 'big')


def dec_run(ret):
    off = _word(ret, 0); n = _word(ret, off); arr = off + 32; out = []
    for k in range(n):
        o = arr + _word(ret, arr + 32 * k); ln = _word(ret, o); blob = ret[o + 32:o + 32 + ln]
        ok = _word(blob, 0); boff = _word(blob, 32); bl = _word(blob, boff); inner = blob[boff + 32:boff + 32 + bl]
        if ok:
            o2 = _word(inner, 0); l2 = _word(inner, o2); cb = inner[o2 + 32:o2 + 32 + l2]
            o3 = _word(cb, 0); n3 = _word(cb, o3)
            out.append((1, [_word(cb, o3 + 32 + 32 * i) for i in range(n3)], b''))
        elif inner[:4] == bytes.fromhex('deadc0de'):
            cb = inner[4:]; o3 = _word(cb, 0); n3 = _word(cb, o3)
            out.append((0, [_word(cb, o3 + 32 + 32 * i) for i in range(n3)], b'marker'))
        else:
            out.append((0, None, inner))
    return out


def codes_for(pm, cases):
    codes = {pm: pm_build(pm), D: driver(pm), S: driver(pm), IMPL: TOK, REJ: REJ_CODE}
    for c in cases:
        for t in (c.get('t0'), c.get('t1')):
            if t: codes[t] = FWD
        if c.get('hooks'): codes[c['hooks']] = hk(pm)
    return codes


def balances_for(pm):
    return {pm: PM_BAL, D: D_BAL}


def overrides(pm, cases):
    ov = {}
    for a, code in codes_for(pm, cases).items():
        ov['0x%040x' % a] = {'code': '0x' + code.hex()}
    for a, bal in balances_for(pm).items():
        ov.setdefault('0x%040x' % a, {})['balance'] = hex(bal)
    return ov


# ---- PoolManager calldata ----
_PMB = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))['methodIdentifiers']
KEY = '(address,address,uint24,int24,address)'


def sel(sig): return bytes.fromhex(_PMB[sig])


def key_words(c): return [c['t0'], c['t1'], c['fee'], c['ts'], c.get('hooks', 0)]


def pm_call(sig, words, with_bytes=False):
    if with_bytes:
        n = len(words) + 1
        return sel(sig) + b''.join(w(x) for x in words) + w(32 * n) + w(0)
    return sel(sig) + b''.join(w(x) for x in words)


def c_init(c, sqrtP): return pm_call(f'initialize({KEY},uint160)', key_words(c) + [sqrtP])
def c_mlp(c, tl, tu, liq, salt=0): return pm_call(f'modifyLiquidity({KEY},(int24,int24,int256,bytes32),bytes)', key_words(c) + [tl, tu, liq, salt], True)
def c_swap(c, zfo, amt, lim): return pm_call(f'swap({KEY},(bool,int256,uint160),bytes)', key_words(c) + [int(zfo), amt, lim], True)
def c_donate(c, a0, a1): return pm_call(f'donate({KEY},uint256,uint256,bytes)', key_words(c) + [a0, a1], True)
def c_sync(cur): return pm_call('sync(address)', [cur])
def c_take(cur, to, a): return pm_call('take(address,address,uint256)', [cur, to, a])
def c_settle(): return pm_call('settle()', [])
def c_settle_for(r): return pm_call('settleFor(address)', [r])
def c_mint(to, id_, a): return pm_call('mint(address,uint256,uint256)', [to, id_, a])
def c_burn(f, id_, a): return pm_call('burn(address,uint256,uint256)', [f, id_, a])
def c_clear(cur, a): return pm_call('clear(address,uint256)', [cur, a])
def c_unlock(): return sel('unlock(bytes)') + w(0x20) + w(0)
def tok_mint(to, a): return bytes.fromhex('40c10f19') + w(to) + w(a)


def bytes_words(d):
    pad = d + b'\0' * ((-len(d)) % 32)
    return [len(d)] + [int.from_bytes(pad[i:i + 32], 'big') for i in range(0, len(pad), 32)]


def build_p(cfgs, acts, settle=True):
    """cfgs: list of (type, selector int, mode, bytes); acts: list of (to, value, bytes)."""
    p = [len(cfgs)]
    for typ, s, m, d in cfgs: p += [typ, s << 224, m] + bytes_words(d)
    p.append(len(acts))
    for to, v, d in acts: p += [to, v] + bytes_words(d)
    p.append(1 if settle else 0)
    return p


def pool_id(c): return int.from_bytes(keccak(b''.join(w(x) for x in key_words(c))), 'big')


def decode_words(words, nact, settle=True):
    """Split a successful record into its parts (see Driver26.unlockCallback)."""
    i = 0; r = {}
    r['bal0'] = words[i:i + 8]; i += 8
    acts = []
    for _ in range(nact):
        acts.append({'ok': words[i], 'w0': words[i + 1], 'w1': words[i + 2], 'len': words[i + 3], 'count': words[i + 4], 'slot0': words[i + 5]}); i += 6
    r['acts'] = acts
    r['deltas'] = words[i:i + 6]; i += 6
    nh = words[i]; i += 1; r['hres'] = words[i:i + min(nh, 24)]; i += min(nh, 24)
    if settle: r['settleOk'] = words[i:i + 6]; i += 6
    r['countEnd'] = words[i]; r['slot0End'] = words[i + 1]; i += 2
    r['bal1'] = words[i:i + 8]; i += 8
    assert i == len(words), (i, len(words))
    return r
