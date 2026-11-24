"""T4 and T3 probe on the deployed PoolManager of each network, read only (eth_call with a code
override for one driver address; nothing is deployed, nothing is sent).

The driver calls unlock six times, each with a callback mode, and after each one reads the lock flag,
the nonzero delta counter, the driver's own delta slot for currency id 1, the synced currency slot and
the driver's ERC-6909 balance of id 1. Then it calls take outside any unlock.
 mode 1: mint(D,1,1), read lock and counter inside, REVERT        -> unlock must fail, all slots 0 after
 mode 2: mint(D,1,1), endless loop (out of gas, call gets 300k gas) -> same
 mode 3: mint(D,1,1), INVALID                                       -> same
 mode 4: mint(D,1,1), burn(D,1,1), return                           -> unlock succeeds, all 0 after
 mode 5: mint(D,1,1), return                                        -> unlock fails with CurrencyNotSettled
 mode 6: BALANCE(PM); settle{value 5}; BALANCE(PM); take(0,D,5); BALANCE(PM); counter; revert with them
Source lines: src/PoolManager.sol:104-114, 291-336, 349-378; src/libraries/Lock.sol:8-27;
src/libraries/NonzeroDeltaCount.sol:9-34; src/libraries/CurrencyDelta.sol:10-41; src/libraries/CurrencyReserves.sol:11-38.
Usage: python3 rollback.py <out.json> [chainId ...]
"""
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, keccak, rpc, MASK

D = 0x00000000000000000000000000000000d21fe0b4
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
COUNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
CURR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
def w(x): return (x & MASK).to_bytes(32, 'big')
DELTA = int.from_bytes(keccak(w(D) + w(1)), 'big')
def sel(sig): return keccak(sig.encode())[:4]

def put(data, at):
    """ops that write data bytes to memory at offset at (padded to words)"""
    ops = []
    data = data + b'\0' * (-len(data) % 32)
    for i in range(0, len(data), 32):
        ops += [('PUSHN', 32, int.from_bytes(data[i:i + 32], 'big')), ('PUSH', at + i), 'MSTORE']
    return ops

def call(pm, data, at, out, outsz, value=0, gas=None, static=False):
    ops = put(data, at)
    if static:
        ops += [('PUSH', outsz), ('PUSH', out), ('PUSH', len(data)), ('PUSH', at), ('PUSHN', 20, pm)]
        ops += [('PUSH', gas) if gas else 'GAS', 'STATICCALL']
    else:
        ops += [('PUSH', outsz), ('PUSH', out), ('PUSH', len(data)), ('PUSH', at), ('PUSH', value), ('PUSHN', 20, pm)]
        ops += [('PUSH', gas) if gas else 'GAS', 'CALL']
    return ops  # leaves ok

def driver(pm):
    S_MINT = sel('mint(address,uint256,uint256)'); S_BURN = sel('burn(address,uint256,uint256)')
    S_TT = sel('exttload(bytes32)'); S_SET = sel('settle()'); S_TAKE = sel('take(address,address,uint256)')
    S_UNL = sel('unlock(bytes)'); S_CB = sel('unlockCallback(bytes)'); S_BAL = sel('balanceOf(address,uint256)')
    mint = S_MINT + w(D) + w(1) + w(1); burn = S_BURN + w(D) + w(1) + w(1)
    p = ['CALLDATASIZE', ('REF', 'go'), 'JUMPI', 'STOP', ('LABEL', 'go'),
         ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI']
    # ---- outer
    rec = 0x2000
    for mode in (1, 2, 3, 4, 5, 6, 7):
        p += call(pm, S_UNL + w(0x20) + w(32) + w(mode), 0x1000, rec + 64, 192, gas=300000 if mode == 2 else None)
        p += [('PUSH', rec), 'MSTORE', 'RETURNDATASIZE', ('PUSH', rec + 32), 'MSTORE']
        rec += 256
        for slot in (LOCK, COUNT, DELTA, CURR):
            p += call(pm, S_TT + w(slot), 0x1000, rec, 32, static=True) + ['POP']; rec += 32
        p += call(pm, S_BAL + w(D) + w(1), 0x1000, rec, 32, static=True) + ['POP']; rec += 32
    p += call(pm, S_TAKE + w(0) + w(D) + w(0), 0x1000, rec + 64, 32)
    p += [('PUSH', rec), 'MSTORE', 'RETURNDATASIZE', ('PUSH', rec + 32), 'MSTORE']; rec += 96
    p += [('PUSH', rec - 0x2000), ('PUSH', 0x2000), 'RETURN']
    # ---- callback
    p += [('LABEL', 'cb'), ('PUSH', 68), 'CALLDATALOAD']  # mode on stack
    for mode in (1, 2, 3, 4, 5, 7):
        p += ['DUP1', ('PUSH', mode), 'EQ', ('REF', f'm{mode}'), 'JUMPI']
    p += [('REF', 'm6'), 'JUMP']
    def mint_ops(): return call(pm, mint, 0x100, 0, 0) + ['POP']
    p += [('LABEL', 'm1')] + mint_ops()
    p += call(pm, S_TT + w(LOCK), 0x100, 0x400, 32, static=True) + ['POP']
    p += call(pm, S_TT + w(COUNT), 0x100, 0x420, 32, static=True) + ['POP']
    p += call(pm, S_TT + w(DELTA), 0x100, 0x440, 32, static=True) + ['POP']
    p += [('PUSH', 96), ('PUSH', 0x400), 'REVERT']
    p += [('LABEL', 'm2')] + mint_ops() + [('LABEL', 'spin'), ('REF', 'spin'), 'JUMP']
    p += [('LABEL', 'm3')] + mint_ops() + ['INVALID']
    p += [('LABEL', 'm4')] + mint_ops() + call(pm, burn, 0x100, 0, 0) + ['POP', ('REF', 'ret'), 'JUMP']
    p += [('LABEL', 'm5')] + mint_ops() + [('REF', 'ret'), 'JUMP']
    p += [('LABEL', 'ret'), ('PUSH', 0x20), ('PUSH', 0), 'MSTORE', ('PUSH', 0), ('PUSH', 0x20), 'MSTORE', ('PUSH', 64), ('PUSH', 0), 'RETURN']
    S_SYNC = sel('sync(address)')
    p += [('LABEL', 'm7')] + call(pm, S_UNL + w(0x20) + w(32) + w(4), 0x100, 0x420, 32) + [('PUSH', 0x400), 'MSTORE']
    p += call(pm, S_SYNC + w(4), 0x100, 0, 0) + [('PUSH', 0x440), 'MSTORE']
    p += call(pm, S_SET, 0x100, 0x480, 32, value=1) + [('PUSH', 0x460), 'MSTORE']
    p += call(pm, S_TT + w(CURR), 0x100, 0x4a0, 32, static=True) + ['POP']
    p += [('PUSH', 192), ('PUSH', 0x400), 'REVERT']
    p += [('LABEL', 'm6'), ('PUSHN', 20, pm), ('RAW', b'\x31'), ('PUSH', 0x400), 'MSTORE']
    p += call(pm, S_SET, 0x100, 0, 0, value=5) + [('PUSH', 0x4a0), 'MSTORE']
    p += [('PUSHN', 20, pm), ('RAW', b'\x31'), ('PUSH', 0x420), 'MSTORE']
    p += call(pm, S_TT + w(COUNT), 0x100, 0x460, 32, static=True) + ['POP']
    p += call(pm, S_TAKE + w(0) + w(D) + w(5), 0x100, 0, 0) + [('PUSH', 0x4c0), 'MSTORE']
    p += [('PUSHN', 20, pm), ('RAW', b'\x31'), ('PUSH', 0x440), 'MSTORE']
    p += call(pm, S_TT + w(COUNT), 0x100, 0x480, 32, static=True) + ['POP']
    p += [('PUSH', 224), ('PUSH', 0x400), 'REVERT']
    return assemble(p)

MODES = {1: 'mint then REVERT', 2: 'mint then out of gas', 3: 'mint then INVALID', 4: 'mint, burn, return', 5: 'mint, return', 6: 'native settle 5 and take 5, then REVERT', 7: 'nested unlock; sync(0x04); settle with value 1; read synced currency; REVERT'}

def run(net):
    cid, name, url, pm = net
    code = driver(int(pm, 16))
    res = {'chainId': cid, 'name': name, 'pm': pm}
    try:
        res['block'] = rpc(url, 'eth_blockNumber', [])
        tx = {'from': '0x' + w(D)[12:].hex(), 'to': '0x' + w(D)[12:].hex(), 'data': '0x01', 'gas': hex(int(os.environ.get('GASLIM', 8_000_000)))}
        out = bytes.fromhex(rpc(url, 'eth_call', [tx, res['block'], {'0x' + w(D)[12:].hex(): {'code': '0x' + code.hex(), 'balance': hex(10**18)}}], timeout=90)[2:])
    except Exception as e:
        res['error'] = str(e)[:300]; return res
    words = [int.from_bytes(out[i:i + 32], 'big') for i in range(0, len(out), 32)]
    k = 0; rows = []
    for mode in range(1, 8):
        ok, rds = words[k], words[k + 1]; ret = out[(k + 2) * 32:(k + 8) * 32]
        lock, cnt, delta, curr, bal = words[k + 8:k + 13]; k += 13
        rows.append({'mode': mode, 'what': MODES[mode], 'unlockOk': ok, 'returnSize': rds, 'return': ret[:min(rds, 192)].hex(),
                     'after': {'lock': lock, 'count': cnt, 'delta': hex(delta), 'syncedCurrency': hex(curr), 'claimBalance': bal}})
    res['modes'] = rows
    res['takeOutsideUnlock'] = {'ok': words[k], 'returnSize': words[k + 1], 'return': out[(k + 2) * 32:(k + 3) * 32].hex()}
    return res

def check(r):
    """expected under Ethereum semantics"""
    if 'modes' not in r: return ['no result']
    bad = []
    for m in r['modes']:
        a = m['after']
        if a['lock'] or a['count'] or int(a['delta'], 16) or a['claimBalance'] or int(a['syncedCurrency'], 16): bad.append(f"mode {m['mode']} left state {a}")
        want_ok = 1 if m['mode'] == 4 else 0
        if m['unlockOk'] != want_ok: bad.append(f"mode {m['mode']} unlockOk {m['unlockOk']}")
    m1 = r['modes'][0]['return']
    if m1[:128] != '%064x' % 1 + '%064x' % 1: bad.append('mode 1 inside reading ' + m1[:192])
    if not r['modes'][4]['return'].startswith('5212cba1'): bad.append('mode 5 selector ' + r['modes'][4]['return'][:8])
    m6 = bytes.fromhex(r['modes'][5]['return'])
    if len(m6) >= 128:
        b0, b1, b2 = (int.from_bytes(m6[i:i + 32], 'big') for i in (0, 32, 64))
        r['native'] = {'balBefore': b0, 'afterSettle': b1, 'afterTake': b2}
        if b1 - b0 != 5 or b2 != b0: bad.append(f'mode 6 balances {b0} {b1} {b2}')
    else: bad.append('mode 6 short return ' + r['modes'][5]['return'])
    m7 = bytes.fromhex(r['modes'][6]['return'])
    if len(m7) >= 192:
        f = [m7[i:i + 32] for i in range(0, 192, 32)]
        r['nested'] = {'innerUnlockOk': int.from_bytes(f[0], 'big'), 'innerUnlockSel': f[1][:4].hex(), 'syncOk': int.from_bytes(f[2], 'big'),
                       'settleValueOk': int.from_bytes(f[3], 'big'), 'settleSel': f[4][:4].hex(), 'synced': hex(int.from_bytes(f[5], 'big'))}
        n = r['nested']
        if n['innerUnlockOk'] or n['innerUnlockSel'] != '5090d6c6' or n['syncOk'] != 1 or n['settleValueOk'] or n['settleSel'] != 'b0ec849e' or n['synced'] != '0x4': bad.append('mode 7 ' + str(n))
    else: bad.append('mode 7 short return ' + r['modes'][6]['return'])
    if r['takeOutsideUnlock']['ok'] or not r['takeOutsideUnlock']['return'].startswith('54e3ca0d'): bad.append('take outside unlock ' + str(r['takeOutsideUnlock']))
    return bad

if __name__ == '__main__':
    nets = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'state', 'networks.json')))['networks']
    want = set(int(x) for x in sys.argv[2:])
    nets = [(n['chainId'], n['name'], n['rpc'], n['poolManager']) for n in nets if not want or n['chainId'] in want]
    with cf.ThreadPoolExecutor(8) as ex: results = list(ex.map(run, nets))
    for r in results:
        r['mismatches'] = check(r)
        print(r['chainId'], r['name'], r.get('block'), 'OK' if not r['mismatches'] else r['mismatches'], r.get('native', ''), r.get('error', ''))
    json.dump(results, open(sys.argv[1], 'w'), indent=1)
