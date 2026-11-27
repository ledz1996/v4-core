"""Task 5: read-only eth_call on Tempo at the deployed PoolManager with its real code and state, under a driver
placed by state override. In one unlock the callback initializes a pool of two currencies that exist nowhere (no
hook), adds liquidity, swaps, lets a helper contract swap again and then revert, reads every delta slot, the
NonzeroDeltaCount, slot0, liquidity and the fee growth words, and settles by burning and minting ERC-6909 claims
whose balances the override gives the driver. The amounts it settles are the reference amounts, so the call
only succeeds when the node computed the same deltas and undid the reverted frame exactly.

Variants: 'settled' (expects success), 'kept' (the helper returns instead of reverting, so its debt stays and
unlock must revert with CurrencyNotSettled), 'nested' (the helper's frame contains a further helper that swaps and
reverts, then the helper itself reverts).

The same calls run in tools/opdiff/pyevm.py over the PoolManager code fetched with eth_getCode and the storage
the node reports for the slots the call reads (prestateTracer through debug_traceCall), and the returned bytes
are compared. Every batch of calls is bracketed with web3_clientVersion.

usage: python3 -I live_swap_revert.py <out.json> [url]
"""
import json, sys, time, urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, keccak, MASK
import pyevm as PE

OUT = sys.argv[1]
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://rpc.mainnet.tempo.xyz'
import os
TOVER = os.environ.get('TIME_OVERRIDE')  # unix time for a block override, e.g. after T14 activation
PM = 0x33620f62c5b9b2086dd6b62f4a297a9f30347029
DRV = 0x00000000000000000000000000000000d21fe301
H1 = 0x00000000000000000000000000000000d21fe302
H2 = 0x00000000000000000000000000000000d21fe303
EOA = 0x00000000000000000000000000000000000c0de1
C0 = 0x00000000000000000000000000000000C0FFEE31
C1 = 0x00000000000000000000000000000000C0FFEE32
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
M = MASK


def w(x): return (x & M).to_bytes(32, 'big')
def sel(s): return keccak(s.encode())[:4]
def kw(*xs): return int.from_bytes(keccak(b''.join(w(x) for x in xs)), 'big')


KEY = '(address,address,uint24,int24,address)'
S_INIT, S_MOD, S_SWAP = sel(f'initialize({KEY},uint160)'), sel(f'modifyLiquidity({KEY},(int24,int24,int256,bytes32),bytes)'), sel(f'swap({KEY},(bool,int256,uint160),bytes)')
S_MINT, S_BURN, S_UNLOCK, S_CB = sel('mint(address,uint256,uint256)'), sel('burn(address,uint256,uint256)'), sel('unlock(bytes)'), sel('unlockCallback(bytes)')
S_EXT, S_TT = sel('extsload(bytes32[])'), sel('exttload(bytes32[])')
FEE, TS = 3000, 60
KW = w(C0) + w(C1) + w(FEE) + w(TS) + w(0)
POOLID = int.from_bytes(keccak(KW), 'big')
PS = kw(POOLID, 6)
MINP, MAXP = 4295128739 + 1, 1461446703485210103287273052203988822378723970342 - 1


def c_init(p): return S_INIT + KW + w(p)
def c_mod(lo, hi, d): return S_MOD + KW + w(lo) + w(hi) + w(d) + w(0) + w(0x140) + w(0)
def c_swap(zfo, amt, lim): return S_SWAP + KW + w(int(zfo)) + w(amt) + w(lim) + w(0x120) + w(0)
def c_ext(slots): return S_EXT + w(0x20) + w(len(slots)) + b''.join(w(s) for s in slots)
def c_tt(slots): return S_TT + w(0x20) + w(len(slots)) + b''.join(w(s) for s in slots)
def dslot(t, c): return kw(t, c)
def bal_slot(owner, cid): return kw(cid, kw(owner, 4))


def driver():
    """Outer: unlock(script). Callback: items [kind 1][len 2][calldata]; kind 0 calls the PoolManager, kind 1 calls
    helper H1, kind 2 calls helper H2. Appends (ok, rds, data) per item and returns the buffer as bytes."""
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PM), 'GAS', 'CALL',
         'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'okout'), 'JUMPI',
         'RETURNDATASIZE', ('PUSH', 0), 'REVERT',
         ('LABEL', 'okout'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x10040), ('PUSH', 68),  # ptr, outp
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 232), 'SHR',  # kind<<16|len, ptr, outp
         'DUP1', ('PUSH', 0xffff), 'AND',  # len, kl, ptr, outp
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP4', ('PUSH', 3), 'ADD', ('PUSH', 0), 'CALLDATACOPY',  # mem[0:len] = calldata
         'SWAP1', ('PUSH', 16), 'SHR',  # kind, len, ptr, outp
         ('PUSHN', 20, PM), 'DUP2', ('PUSH', 1), 'EQ', ('REF', 'k1'), 'JUMPI', 'DUP2', ('PUSH', 2), 'EQ', ('REF', 'k2'), 'JUMPI', ('REF', 'go'), 'JUMP',
         ('LABEL', 'k1'), 'POP', ('PUSHN', 20, H1), ('REF', 'go'), 'JUMP',
         ('LABEL', 'k2'), 'POP', ('PUSHN', 20, H2),
         ('LABEL', 'go'),  # target, kind, len, ptr, outp
         'SWAP1', 'POP',  # target, len, ptr, outp
         ('PUSH', 0), ('PUSH', 0), 'DUP4', ('PUSH', 0), ('PUSH', 0), 'DUP6', 'GAS', 'CALL',  # ok, target, len, ptr, outp
         'SWAP1', 'POP',  # ok, len, ptr, outp
         'DUP4', 'MSTORE',  # len, ptr, outp
         'RETURNDATASIZE', 'DUP4', ('PUSH', 32), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP5', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',
         'SWAP2', ('PUSH', 64), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP2',  # outp += 64 + rds
         ('PUSH', 3), 'ADD', 'ADD',  # ptr += len + 3
         ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP', 'POP',  # outp
         ('PUSH', 0x10040), 'SWAP1', 'SUB',  # n
         'DUP1', ('PUSH', 0x10020), 'MSTORE', ('PUSH', 0x20), ('PUSH', 0x10000), 'MSTORE',
         ('PUSH', 0x40), 'ADD', ('PUSH', 0x10000), 'RETURN']
    return assemble(p)


def helper(revert, inner=None):
    """Forwards its calldata to the PoolManager. Then, for the nested variant, calls helper H2 with the
    calldata stored after a 0xffff marker... kept simple: inner is a fixed calldata for H2."""
    p = ['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PM), 'GAS', 'CALL', 'POP']
    if inner is not None:
        n = len(inner)
        # copy the inner calldata from code into memory at 0x1000 and call H2 (which swaps and reverts)
        p += [('PUSHN', 2, n), ('PUSHN', 2, 0xfff0), ('PUSH', 0x1000), ('RAW', bytes([0x39])),
              ('PUSH', 0), ('PUSH', 0), ('PUSHN', 2, n), ('PUSH', 0x1000), ('PUSH', 0), ('PUSHN', 20, H2), 'GAS', 'CALL', 'POP']
    p += ['RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'REVERT' if revert else 'RETURN']
    code = assemble(p)
    if inner is not None:
        code = code.ljust(0xfff0, b'\0') + inner
    return code


def item(kind, data): return bytes([kind]) + len(data).to_bytes(2, 'big') + data


def script(variant, settle_amounts):
    s0 = [PS, PS + 1, PS + 2, PS + 3]
    tts = [dslot(DRV, C0), dslot(DRV, C1), dslot(H1, C0), dslot(H1, C1), dslot(H2, C0), dslot(H2, C1), NZDC]
    its = [item(0, c_init(1 << 96)), item(0, c_mod(-600, 600, 10 ** 18)), item(0, c_swap(True, -10 ** 15, MINP)),
           item(0, c_ext(s0)), item(0, c_tt(tts))]
    if variant in ('settled', 'kept'):
        its.append(item(1, c_swap(False, -2 * 10 ** 15, MAXP)))
    else:
        its.append(item(1, c_swap(False, -2 * 10 ** 15, MAXP)))
    its += [item(0, c_ext(s0)), item(0, c_tt(tts))]
    a0, a1 = settle_amounts
    for cur, a in ((C0, a0), (C1, a1)):
        if a < 0: its.append(item(0, S_BURN + w(DRV) + w(cur) + w(-a)))
        elif a > 0: its.append(item(0, S_MINT + w(DRV) + w(cur) + w(a)))
    its += [item(0, c_tt(tts))]
    return b''.join(its) + b'\0\0\0'


def codes_for(variant, pmcode):
    nested_inner = c_swap(True, -5 * 10 ** 14, MINP)
    h1 = helper(revert=(variant != 'kept'), inner=nested_inner if variant == 'nested' else None)
    h2 = helper(revert=True)
    return {DRV: driver(), H1: h1, H2: h2, PM: pmcode}


BIG = 10 ** 30
def overrides():
    return {bal_slot(DRV, C0): BIG, bal_slot(DRV, C1): BIG}


_ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(method, params, timeout=90):
    req = urllib.request.Request(URL, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
        return json.load(r)


def state_override(codes):
    so = {}
    for a, c in codes.items():
        if a == PM: continue
        so['0x%040x' % a] = {'code': '0x' + c.hex()}
    so['0x%040x' % PM] = {'stateDiff': {'0x%064x' % k: '0x%064x' % v for k, v in overrides().items()}}
    return so


def parse_buf(b):
    out, p = [], 0
    while p + 64 <= len(b):
        ok = int.from_bytes(b[p:p + 32], 'big'); n = int.from_bytes(b[p + 32:p + 64], 'big')
        out.append((ok, b[p + 64:p + 64 + n].hex())); p += 64 + n
    return out


def ref_run(codes, storage, data):
    wld = PE.World(codes)
    for k, v in storage.items(): wld.storage[(PM, k)] = v
    for k, v in overrides().items(): wld.storage[(PM, k)] = v
    ok, ret = wld.call(EOA, DRV, 0, data, False, 0)
    return ok, ret


def main():
    res = {'url': URL, 'timeOverride': TOVER, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'clientBefore': rpc('web3_clientVersion', [])}
    blk = rpc('eth_getBlockByNumber', ['latest', False])['result']
    bn = blk['number']; res['block'] = int(bn, 16); res['blockHash'] = blk['hash']
    pmcode = bytes.fromhex(rpc('eth_getCode', ['0x%040x' % PM, bn])['result'][2:])
    res['pmCodeLen'] = len(pmcode)
    import hashlib; res['pmCodeSha256'] = hashlib.sha256(pmcode).hexdigest()
    res['variants'] = {}
    for variant in ('settled', 'kept', 'nested'):
        codes = codes_for(variant, pmcode)
        # pass 1: run the reference without settlement to learn the deltas the driver holds
        probe = script(variant, (0, 0))
        tx = {'from': '0x%040x' % EOA, 'to': '0x%040x' % DRV, 'data': '0x' + probe.hex(), 'gas': hex(40_000_000)}
        # storage the node reads for this call
        tr = rpc('debug_traceCall', [tx, bn, {'tracer': 'prestateTracer', 'stateOverrides': state_override(codes)}])
        pre = tr.get('result', {})
        st = {int(k, 16): int(v, 16) for k, v in pre.get('0x%040x' % PM, {}).get('storage', {}).items()}
        dd = ref_deltas(codes, st, variant)
        amounts = (dd[0], dd[1])
        full = script(variant, amounts)
        tx['data'] = '0x' + full.hex()
        rok, rret = ref_run(codes, st, full)
        node = rpc('eth_call', [tx, bn, state_override(codes)] + ([{'time': hex(int(TOVER))}] if TOVER else []))
        if 'error' in node:
            nok, nret = False, bytes.fromhex((node['error'].get('data') or '0x')[2:])
        else:
            nok, nret = True, bytes.fromhex(node['result'][2:])
        v = {'prestateSlots': len(st), 'deltasSettled': [str(a) for a in amounts], 'ref': {'ok': rok, 'ret': rret.hex()},
             'node': {'ok': nok, 'ret': nret.hex(), 'error': node.get('error')}, 'equal': (rok, rret) == (nok, nret)}
        if rok:
            body = rret[64:]
            v['refItems'] = parse_buf(body)
        res['variants'][variant] = v
    res['clientAfter'] = rpc('web3_clientVersion', [])
    res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(res, open(OUT, 'w'), indent=1)
    for k, v in res['variants'].items():
        print(k, 'ref ok', v['ref']['ok'], 'node ok', v['node']['ok'], 'equal', v['equal'], 'deltas', v['deltasSettled'])
    print(res['clientBefore'], res['clientAfter'], res['block'])


def ref_deltas(codes, st, variant):
    """Runs the probe script in pyevm with a driver whose callback returns its buffer even though deltas are open,
    by reading the transient delta slots straight from the reference world after the callback items ran."""
    wld = PE.World(codes)
    for k, v in st.items(): wld.storage[(PM, k)] = v
    for k, v in overrides().items(): wld.storage[(PM, k)] = v
    # run the callback items directly from the driver frame: set the unlock flag as unlock() would
    UNLOCKED = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
    wld.transient[(PM, UNLOCKED)] = 1
    probe = script(variant, (0, 0))
    data = S_CB + w(0x20) + w(len(probe)) + probe
    ok, ret = wld.call(PM, DRV, 0, data, False, 1)
    assert ok, 'reference callback failed'
    def s(x): return x - (1 << 256) if x >> 255 else x
    return s(wld.transient.get((PM, dslot(DRV, C0)), 0)), s(wld.transient.get((PM, dslot(DRV, C1)), 0))


if __name__ == '__main__':
    main()
