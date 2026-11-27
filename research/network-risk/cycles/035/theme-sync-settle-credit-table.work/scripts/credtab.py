"""Cycle 35, theme-sync-settle-credit-table, Task 3. Read-only measurement harness.
A driver placed by state override at DRV (fresh address, funded by override) calls unlock on the
DEPLOYED PoolManager of each network (real address, real state). Inside unlockCallback it runs a
script of steps and finally reverts with the record, so nothing persists and nothing settles.
Steps: CALL(target, value, calldata) records ok, return size and return data; BAL(addr) records
the native balance; CREATE(value, initcode) records the created address. The only initcode used is
PUSH20 <PoolManager> SELFDESTRUCT, i.e. a forced native inflow paid by the driver itself.
Cases per network: native forced inflow between sync(0) and settle; native take/settle round trip;
for each protocol token (native face, precompile token, fee token, linked token) a take/sync/repay/
settle round trip with balanceOf(PM) read at each point, and for native faces sync(face), forced native
inflow, settle, plus sync(face) then settle with value. No randomness is used (no sampling seed).
Each network batch is bracketed by web3_clientVersion. usage: python3 -I credtab.py <out.json> [chainId ...]"""
import sys, os, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.work/scripts')
from evm import assemble, keccak
from rpcu import rpc, version

DRV = '0x00000000000000000000000000000000d21fe035'
def sel(s): return keccak(s.encode())[:4]
def w(x): return (x % 2**256).to_bytes(32, 'big')
S_UNLOCK, S_CB = sel('unlock(bytes)'), sel('unlockCallback(bytes)')

def driver(pm):
    pmi = int(pm, 16)
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pmi), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x4000), ('PUSH', 68),
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 248), 'SHR',
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP2', ('PUSH', 1), 'ADD', 'CALLDATALOAD', ('PUSH', 240), 'SHR',
         'DUP3', ('PUSH', 3), 'ADD', 'CALLDATALOAD', ('PUSH', 96), 'SHR',
         'DUP4', ('PUSH', 23), 'ADD', 'CALLDATALOAD',
         'DUP3', 'DUP6', ('PUSH', 55), 'ADD', ('PUSH', 0), 'CALLDATACOPY',
         'DUP4', ('PUSH', 2), 'EQ', ('REF', 'bal'), 'JUMPI',
         'DUP4', ('PUSH', 3), 'EQ', ('REF', 'cre'), 'JUMPI',
         ('PUSH', 0), ('PUSH', 0), 'DUP5', ('PUSH', 0), 'DUP5', 'DUP7', 'GAS', 'CALL',
         'DUP7', 'MSTORE',
         'RETURNDATASIZE', 'DUP7', ('PUSH', 32), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP8', ('PUSH', 64), 'ADD', 'RETURNDATACOPY',
         'RETURNDATASIZE', ('PUSH', 64), 'ADD', ('REF', 'next'), 'JUMP',
         ('LABEL', 'bal'), 'DUP2', ('RAW', bytes([0x31])), 'DUP7', 'MSTORE', ('PUSH', 0), 'DUP7', ('PUSH', 32), 'ADD', 'MSTORE',
         ('PUSH', 64), ('REF', 'next'), 'JUMP',
         ('LABEL', 'cre'), 'DUP3', ('PUSH', 0), 'DUP3', ('RAW', bytes([0xf0])), 'DUP7', 'MSTORE', ('PUSH', 0), 'DUP7', ('PUSH', 32), 'ADD', 'MSTORE',
         ('PUSH', 64), ('REF', 'next'), 'JUMP',
         ('LABEL', 'next'), 'DUP7', 'ADD', 'SWAP6', 'POP', 'POP', 'POP', 'SWAP1', 'POP', ('PUSH', 55), 'ADD', 'ADD', ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP', ('PUSH', 0x4000), 'SWAP1', 'SUB', ('PUSH', 0x4000), 'REVERT']
    return assemble(p)

def item(kind, target, value, data=b''):
    return bytes([kind]) + len(data).to_bytes(2, 'big') + bytes.fromhex(target[2:].rjust(40, '0')) + w(value) + data
def CALL(t, data, value=0, label=''): return (label, item(1, t, value, data))
def BAL(a, label=''): return (label, item(2, a, 0))
def CREATE(v, code, label=''): return (label, item(3, '0x' + '00' * 20, v, code))
def a32(a): return w(int(a, 16))
def dslot(t, c): return keccak(a32(t) + a32(c))
def balOf(tok, who): return sel('balanceOf(address)') + a32(who)

def parse(buf):
    out = []; i = 0
    while i + 64 <= len(buf):
        ok = int.from_bytes(buf[i:i + 32], 'big'); n = int.from_bytes(buf[i + 32:i + 64], 'big')
        out.append((ok, buf[i + 64:i + 64 + n].hex())); i += 64 + n
    return out

ZERO = '0x' + '00' * 20
def case_native_forced(pm, v):
    return [BAL(pm, 'PM native before'), CALL(pm, sel('sync(address)') + a32(ZERO), label='sync(0)'),
            CREATE(v, bytes([0x73]) + bytes.fromhex(pm[2:]) + bytes([0xff]), 'forced native inflow (selfdestruct)'),
            BAL(pm, 'PM native after inflow'), CALL(pm, sel('settle()'), label='settle() value 0'),
            CALL(pm, sel('exttload(bytes32)') + dslot(DRV, ZERO), label='delta(driver,native)')]
def case_native_roundtrip(pm, x):
    return [BAL(pm, 'PM native before'), CALL(pm, sel('take(address,address,uint256)') + a32(ZERO) + a32(DRV) + w(x), label='take native x'),
            BAL(pm, 'PM native after take'), CALL(pm, sel('sync(address)') + a32(ZERO), label='sync(0)'),
            CALL(pm, sel('settle()'), value=x, label='settle() value x'), BAL(pm, 'PM native after settle'),
            CALL(pm, sel('exttload(bytes32)') + dslot(DRV, ZERO), label='delta(driver,native)')]
def case_token_roundtrip(pm, t, x):
    return [CALL(t, balOf(t, pm), label='balanceOf(PM) before'), BAL(pm, 'PM native before'),
            CALL(pm, sel('take(address,address,uint256)') + a32(t) + a32(DRV) + w(x), label='take(T,driver,x)'),
            CALL(t, balOf(t, pm), label='balanceOf(PM) after take'), BAL(pm, 'PM native after take'), CALL(t, balOf(t, DRV), label='balanceOf(driver) after take'),
            CALL(pm, sel('sync(address)') + a32(t), label='sync(T)'),
            CALL(t, sel('transfer(address,uint256)') + a32(pm) + w(x), label='driver T.transfer(PM,x)'),
            CALL(t, balOf(t, pm), label='balanceOf(PM) after repay'),
            CALL(pm, sel('settle()'), label='settle()'),
            CALL(pm, sel('exttload(bytes32)') + dslot(DRV, t), label='delta(driver,T)')]
def case_face_forced(pm, f, v):
    return [CALL(f, balOf(f, pm), label='face balanceOf(PM) before'), BAL(pm, 'PM native before'),
            CALL(pm, sel('sync(address)') + a32(f), label='sync(face)'),
            CREATE(v, bytes([0x73]) + bytes.fromhex(pm[2:]) + bytes([0xff]), 'forced native inflow (selfdestruct)'),
            CALL(f, balOf(f, pm), label='face balanceOf(PM) after inflow'),
            CALL(pm, sel('settle()'), label='settle() value 0'),
            CALL(pm, sel('exttload(bytes32)') + dslot(DRV, f), label='delta(driver,face)'),
            CALL(pm, sel('exttload(bytes32)') + dslot(DRV, ZERO), label='delta(driver,native)'),
            CALL(pm, sel('sync(address)') + a32(f), label='sync(face) again'),
            CALL(pm, sel('settle()'), value=1, label='settle() value 1 with face synced')]

def run(url, chain, pm, name, steps, block):
    drv = driver(pm)
    data = b''.join(s for _, s in steps)
    ov = {DRV: {'code': '0x' + drv.hex(), 'balance': hex(10**21)}}
    tx = {'from': '0x00000000000000000000000000000000000a11ce', 'to': DRV, 'data': '0x' + data.hex(), 'gas': hex(15_000_000)}
    r = rpc(url, 'eth_call', [tx, block, ov], 120)
    rec = {'case': name, 'labels': [l for l, _ in steps], 'block': block, 'raw': r}
    if 'result' in r:
        try:
            rec['steps'] = [{'label': l, 'ok': ok, 'ret': d} for l, (ok, d) in zip([l for l, _ in steps], parse(bytes.fromhex(r['result'][2:])))]
        except Exception as e: rec['parseErr'] = str(e)
    return rec

def main():
    out_path = sys.argv[1]; spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.json')))
    only = set(map(int, sys.argv[2:]))
    nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
    results = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for n in nets:
        cid = n['chainId']
        if only and cid not in only: continue
        s = spec.get(str(cid), {}); url = s.get('rpc', n['rpc']); pm = n['poolManager'].lower()
        res = {'chain': cid, 'name': n['name'], 'url': url, 'pm': pm, 'before': version(url, cid), 'cases': []}
        b = rpc(url, 'eth_getBlockByNumber', ['latest', False], 60)
        block = (b.get('result') or {}).get('number', 'latest'); res['blockNumber'] = block
        if not s.get('noNative'):
            res['cases'].append(run(url, cid, pm, 'native forced inflow between sync(0) and settle', case_native_forced(pm, 10**6), block))
            res['cases'].append(run(url, cid, pm, 'native take then sync(0) and settle with value', case_native_roundtrip(pm, s.get('nativeX', 1000)), block))
        for t, label in s.get('tokens', []):
            q = rpc(url, 'eth_call', [{'to': t, 'data': '0x' + (balOf(t, pm)).hex()}, block], 60)
            try: bal = int(q['result'], 16)
            except Exception: bal = None
            if not bal:
                res['cases'].append({'case': f'token round trip {label} {t}', 'skipped': 'PoolManager balance read as ' + str(q)[:200]}); continue
            x = max(1, bal // 1000)
            rec = run(url, cid, pm, f'token round trip {label} {t}', case_token_roundtrip(pm, t.lower(), x), block); rec['x'] = x; rec['pmBalance'] = bal
            res['cases'].append(rec)
        for f, label in s.get('faces', []):
            res['cases'].append(run(url, cid, pm, f'face forced inflow {label} {f}', case_face_forced(pm, f.lower(), 10**6 if cid != 5042 else 10**13), block))
        res['after'] = version(url, cid)
        results[str(cid)] = res
        json.dump(results, open(out_path, 'w'), indent=1)
        print(cid, n['name'], 'done', [ (c['case'][:40], 'ok' if 'steps' in c else str(c.get('raw', c.get('skipped')))[:120]) for c in res['cases']], flush=True)

if __name__ == '__main__':
    main()
