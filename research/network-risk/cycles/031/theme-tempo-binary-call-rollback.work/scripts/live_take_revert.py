"""Cycle 31 Task 5 (live part): read-only eth_call on Tempo at the deployed PoolManager with its real code and
state. A driver placed by state override unlocks the PoolManager. In the callback a helper takes pathUSD
(the TIP-20 precompile token 0x20c0...0000, which the PoolManager holds) to itself and then reverts, so the
precompile's balance writes and the PoolManager's transient delta must both be undone by the frame rollback.
The driver then reads the deltas, the token balances, syncs and settles. Variants:
  revert   - helper takes A and reverts; settle pays 0; unlock must close (success).
  kept     - helper takes A and returns; its debt stays; unlock must revert with CurrencyNotSettled.
  nested   - helper takes A, calls a second helper that takes B and reverts, then the first reverts.
  roundtrip- driver takes A to itself, a helper takes B and reverts, the driver syncs, sends A back with
             TIP-20 transfer and settles; settle must return A and the unlock must close.
The reference is tools/opdiff/pyevm.py over the PoolManager code from eth_getCode, the PoolManager storage the
node reports (prestateTracer), and a minimal token contract at the token address whose balances are seeded with
the node's balanceOf answers at the same block (pyevm.py cannot run the TIP-20 precompile). Return bytes of node
and reference are compared. Every batch is bracketed with web3_clientVersion.
usage: python3 -I live_take_revert.py <out.json> [url]   (TIME_OVERRIDE=<unix time> runs the calls through eth_simulateV1 at that block time)
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
TOKEN = 0x20c0000000000000000000000000000000000000
A_AMT, B_AMT = 1_000_000, 500_000
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
M = MASK


def w(x): return (x & M).to_bytes(32, 'big')
def sel(s): return keccak(s.encode())[:4]
def kw(*xs): return int.from_bytes(keccak(b''.join(w(x) for x in xs)), 'big')


KEY = '(address,address,uint24,int24,address)'
S_INIT, S_MOD, S_SWAP = sel(f'initialize({KEY},uint160)'), sel(f'modifyLiquidity({KEY},(int24,int24,int256,bytes32),bytes)'), sel(f'swap({KEY},(bool,int256,uint160),bytes)')
S_MINT, S_BURN, S_UNLOCK, S_CB = sel('mint(address,uint256,uint256)'), sel('burn(address,uint256,uint256)'), sel('unlock(bytes)'), sel('unlockCallback(bytes)')
S_EXT, S_TT = sel('extsload(bytes32[])'), sel('exttload(bytes32[])')
S_TAKE, S_SYNC, S_SETTLE = sel('take(address,address,uint256)'), sel('sync(address)'), sel('settle()')
S_BAL, S_TRANSFER = sel('balanceOf(address)'), sel('transfer(address,uint256)')
FEE, TS = 3000, 60
KW = w(0) + w(TOKEN) + w(FEE) + w(TS) + w(0)
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
         ('PUSHN', 20, PM), 'DUP2', ('PUSH', 1), 'EQ', ('REF', 'k1'), 'JUMPI', 'DUP2', ('PUSH', 2), 'EQ', ('REF', 'k2'), 'JUMPI',
         'DUP2', ('PUSH', 3), 'EQ', ('REF', 'k3'), 'JUMPI', ('REF', 'go'), 'JUMP',
         ('LABEL', 'k3'), 'POP', ('PUSHN', 20, TOKEN), ('REF', 'go'), 'JUMP',
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


def c_take(to, amt): return S_TAKE + w(TOKEN) + w(to) + w(amt)
def c_bal(a): return S_BAL + w(a)


def script(variant):
    tts = [dslot(DRV, TOKEN), dslot(H1, TOKEN), dslot(H2, TOKEN), NZDC]
    reads = [item(0, c_tt(tts)), item(3, c_bal(PM)), item(3, c_bal(H1)), item(3, c_bal(H2)), item(3, c_bal(DRV))]
    its = []
    if variant == 'roundtrip':
        its += [item(0, c_take(DRV, A_AMT)), item(1, c_take(H1, B_AMT)), item(0, S_SYNC + w(TOKEN))] + reads
        its += [item(3, S_TRANSFER + w(PM) + w(A_AMT)), item(0, S_SETTLE)] + reads
    else:
        its += [item(1, c_take(H1, A_AMT))] + reads
        its += [item(0, S_SYNC + w(TOKEN)), item(0, S_SETTLE)] + reads
    return b''.join(its) + b'\0\0\0'


def token_model():
    """balanceOf(a) returns sload(a); transfer(to, v) moves v from caller to to, reverts when short, returns true."""
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', 'DUP1', ('PUSHN', 4, int.from_bytes(S_BAL, 'big')), 'EQ', ('REF', 'bal'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(S_TRANSFER, 'big')), 'EQ', ('REF', 'tr'), 'JUMPI', ('PUSH', 0), ('PUSH', 0), 'REVERT',
         ('LABEL', 'bal'), ('PUSH', 4), 'CALLDATALOAD', 'SLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
         ('LABEL', 'tr'), ('PUSH', 36), 'CALLDATALOAD', 'CALLER', 'SLOAD',  # bal, v
         'DUP2', 'DUP2', 'LT', ('REF', 'short'), 'JUMPI',
         'SUB', 'CALLER', 'SSTORE',
         ('PUSH', 36), 'CALLDATALOAD', ('PUSH', 4), 'CALLDATALOAD', 'SLOAD', 'ADD', ('PUSH', 4), 'CALLDATALOAD', 'SSTORE',
         ('PUSH', 1), ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
         ('LABEL', 'short'), ('PUSH', 0), ('PUSH', 0), 'REVERT']
    return assemble(p)


def codes_for(variant, pmcode):
    nested_inner = c_take(H2, B_AMT)
    h1 = helper(revert=(variant != 'kept'), inner=nested_inner if variant == 'nested' else None)
    h2 = helper(revert=True)
    return {DRV: driver(), H1: h1, H2: h2, PM: pmcode}


BIG = 10 ** 30
def overrides():
    return {}


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


def ref_run(codes, storage, data, tokbal):
    codes = dict(codes); codes[TOKEN] = token_model()
    wld = PE.World(codes)
    for a, v in tokbal.items(): wld.storage[(TOKEN, a)] = v
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
    tokbal = {}
    for a in (PM, H1, H2, DRV):
        r = rpc('eth_call', [{'to': '0x%040x' % TOKEN, 'data': '0x' + c_bal(a).hex()}, bn])
        tokbal[a] = int(r['result'], 16)
    res['tokenBalances'] = {'0x%040x' % a: v for a, v in tokbal.items()}
    for variant in ('revert', 'kept', 'nested', 'roundtrip'):
        codes = codes_for(variant, pmcode)
        full = script(variant)
        tx = {'from': '0x%040x' % EOA, 'to': '0x%040x' % DRV, 'data': '0x' + full.hex(), 'gas': hex(40_000_000)}
        tr = rpc('debug_traceCall', [tx, bn, {'tracer': 'prestateTracer', 'stateOverrides': state_override(codes)}])
        pre = tr.get('result', {})
        st = {int(k, 16): int(v, 16) for k, v in pre.get('0x%040x' % PM, {}).get('storage', {}).items()}
        rok, rret = ref_run(codes, st, full, tokbal)
        if TOVER:
            # eth_call's block override changes TIMESTAMP but not the hardfork rules on this endpoint
            # (results/t14_override_probe.txt); eth_simulateV1 applies the rules of the simulated time
            stx = dict(tx); stx['gas'] = hex(25_000_000)
            sim = rpc('eth_simulateV1', [{'blockStateCalls': [{'blockOverrides': {'time': hex(int(TOVER))},
                                                               'stateOverrides': state_override(codes), 'calls': [stx]}]}, bn])
            if 'error' in sim: node = {'error': sim['error']}
            else:
                blk0 = sim['result'][0]; c0 = blk0['calls'][0]
                res.setdefault('simulatedTimestamps', []).append(blk0['timestamp'])
                if c0['status'] == '0x1': node = {'result': c0['returnData']}
                else: node = {'error': {'data': (c0.get('error') or {}).get('data') or c0.get('returnData'), 'detail': c0.get('error')}}
        else:
            node = rpc('eth_call', [tx, bn, state_override(codes)])
        if 'error' in node:
            nok, nret = False, bytes.fromhex((node['error'].get('data') or '0x')[2:])
        else:
            nok, nret = True, bytes.fromhex(node['result'][2:])
        v = {'prestateSlots': len(st), 'traceError': tr.get('error'), 'ref': {'ok': rok, 'ret': rret.hex()},
             'node': {'ok': nok, 'ret': nret.hex(), 'error': node.get('error')}, 'equal': (rok, rret) == (nok, nret)}
        if rok: v['refItems'] = parse_buf(rret[64:])
        if nok: v['nodeItems'] = parse_buf(nret[64:])
        res['variants'][variant] = v
    res['clientAfter'] = rpc('web3_clientVersion', [])
    res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(res, open(OUT, 'w'), indent=1)
    for k, v in res['variants'].items():
        print(k, 'ref ok', v['ref']['ok'], 'node ok', v['node']['ok'], 'equal', v['equal'], v['node']['ret'][:80])
    print(res['clientBefore'], res['clientAfter'], res['block'])


if __name__ == '__main__':
    main()
