"""Task 3: live read-only probe of the CallFrom rollback on Arc. Nothing is sent: eth_call / eth_simulateV1 with state overrides.
An EOA E gets the EIP-7702 designator 0xef0100||CB by override and CB gets harness code W. The transaction is from E to E.
W as driver (caller != PoolManager): warms the target, CALLs it with an explicit gas X and the payload, records gas before/after,
success and return data, then reads PoolManager.isOperator(E, BEEF) and exttload of the synced currency, lock and delta count.
mode 0: target PoolManager, payload unlock(data)  (ordinary call frame: the reference)
mode 1: target Multicall3From, payload aggregate3([{PM, allowFailure=true, unlock(data)}])  (child under CallFrom)
mode 2: target D (code STOP) to calibrate the driver's own gas use.
W as unlock callback (caller == PoolManager): PM.setOperator(BEEF,true) [PM storage write], PM.sync(USDC face) [PM transient
write], then if data[1]==1 REVERT, else RETURN abi bytes of length N=data[0].
usage: python3 -I live.py <out.json> <url> [<url> ...]"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc
from evm import assemble, keccak
PM = 0x8366a39CC670B4001A1121B8F6A443A643e40951
MC = 0x522fAf9A91c41c443c66765030741e4AaCe147D0
USDC = 0x3600000000000000000000000000000000000000
E = 0x00000000000000000000000000000000e0a1c038
CB = 0x00000000000000000000000000000000cb0a1038
D = 0x00000000000000000000000000000000d0a1c038
BEEF = 0x000000000000000000000000000000000000beef
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
CNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
def sel(s): return int.from_bytes(keccak(s.encode())[:4], 'big')
def w(x): return x.to_bytes(32, 'big')
def mstore(off, v): return [('PUSH', v), ('PUSH', off), 'MSTORE']
def code():
    p = ['CALLER', ('PUSH', PM), 'EQ', ('REF', 'cb'), 'JUMPI']
    # target = [PM, MC, D][mode]
    p += [('PUSH', 0), 'CALLDATALOAD', 'DUP1', ('REF', 'm1'), 'JUMPI', 'POP', ('PUSH', PM), ('REF', 'tg'), 'JUMP',
          ('LABEL', 'm1'), ('PUSH', 1), 'EQ', ('REF', 'mc'), 'JUMPI', ('PUSH', D), ('REF', 'tg'), 'JUMP',
          ('LABEL', 'mc'), ('PUSH', MC), ('LABEL', 'tg')]                     # stack: target
    # warm target and PM
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), 'DUP5', 'GAS', 'STATICCALL', 'POP']
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', PM), 'GAS', 'STATICCALL', 'POP']
    p += [('PUSH', 0x40), 'CALLDATASIZE', 'SUB', ('PUSH', 0x40), ('PUSH', 0x1000), 'CALLDATACOPY']
    # CALL(X, target, 0, 0x1000, len, 0, 0)
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0x40), 'CALLDATASIZE', 'SUB', ('PUSH', 0x1000), ('PUSH', 0), 'DUP6',
          ('PUSH', 0x20), 'CALLDATALOAD', 'GAS', ('PUSH', 0), 'MSTORE', 'CALL', 'GAS', ('PUSH', 0x40), 'MSTORE',
          ('PUSH', 0x20), 'MSTORE', 'POP', 'RETURNDATASIZE', ('PUSH', 0x60), 'MSTORE',
          'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0x100), 'RETURNDATACOPY']
    def rd(selector, args, out):
        q = mstore(0x3000, selector << 224)
        for i, a in enumerate(args): q += a(0x3004 + 32 * i)
        q += [('PUSH', 0x20), ('PUSH', out), ('PUSH', 4 + 32 * len(args)), ('PUSH', 0x3000), ('PUSH', PM), 'GAS', 'STATICCALL', 'POP']
        return q
    p += rd(sel('isOperator(address,address)'), [lambda o: ['ADDRESS', ('PUSH', o), 'MSTORE'], lambda o: mstore(o, BEEF)], 0x80)
    for slot, out in ((CUR, 0xa0), (LOCK, 0xc0), (CNT, 0xe0)):
        p += rd(sel('exttload(bytes32)'), [lambda o, s=slot: mstore(o, s)], out)
    p += [('PUSH', 0x60), 'MLOAD', ('PUSH', 0x100), 'ADD', ('PUSH', 0), 'RETURN']
    # callback
    p += [('LABEL', 'cb')]
    p += mstore(0x3000, sel('setOperator(address,bool)') << 224) + mstore(0x3004, BEEF) + mstore(0x3024, 1)
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0x44), ('PUSH', 0x3000), ('PUSH', 0), ('PUSH', PM), 'GAS', 'CALL', 'POP']
    p += mstore(0x3000, sel('sync(address)') << 224) + mstore(0x3004, USDC)
    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0x24), ('PUSH', 0x3000), ('PUSH', 0), ('PUSH', PM), 'GAS', 'CALL', 'POP']
    p += [('PUSH', 0x64), 'CALLDATALOAD', ('REF', 'rv'), 'JUMPI']
    p += mstore(0, 0x20) + [('PUSH', 0x44), 'CALLDATALOAD', ('PUSH', 0x20), 'MSTORE',
                           ('PUSH', 0x44), 'CALLDATALOAD', ('PUSH', 0x40), 'ADD', ('PUSH', 0), 'RETURN']
    p += [('LABEL', 'rv'), ('PUSH', 0), ('PUSH', 0), 'REVERT']
    return assemble(p)
W = code()
def unlock_cd(n, mode):
    data = w(n) + w(mode)
    return w(sel('unlock(bytes)'))[-4:] + w(0x20) + w(len(data)) + data
def agg3(inner):
    pad = inner + b'\0' * ((-len(inner)) % 32)
    elem = w(PM) + w(1) + w(0x60) + w(len(inner)) + pad
    return w(sel('aggregate3((address,bool,bytes)[])'))[-4:] + w(0x20) + w(1) + w(0x20) + elem
def payload(mode, n, rv):
    if mode == 0: return unlock_cd(n, rv)
    if mode == 1: return agg3(unlock_cd(n, rv))
    return b''
def h(x, n=20): return '0x' + x.to_bytes(n, 'big').hex()
OVR = {h(E): {'code': '0xef0100' + CB.to_bytes(20, 'big').hex()}, h(CB): {'code': '0x' + W.hex()}, h(D): {'code': '0x00'}}
def tx(mode, X, n, rv):
    return {'from': h(E), 'to': h(E), 'gas': hex(25_000_000), 'data': '0x' + (w(mode) + w(X) + payload(mode, n, rv)).hex()}
def parse(res):
    b = bytes.fromhex(res[2:]); ws = [int.from_bytes(b[i:i + 32], 'big') for i in range(0, 0x100, 32)]
    r = {'g0': ws[0], 'ok': ws[1], 'g1': ws[2], 'rds': ws[3], 'isOperator': ws[4], 'tCurrency': hex(ws[5]), 'tLock': ws[6], 'tCount': ws[7]}
    rd = b[0x100:]
    r['ret_head'] = rd[:256].hex()
    return r, rd
def entry_success(rd):  # aggregate3 return: Result[]
    try:
        off = int.from_bytes(rd[0:32], 'big'); n = int.from_bytes(rd[off:off + 32], 'big')
        e0 = off + 32 + int.from_bytes(rd[off + 32:off + 64], 'big')
        return int.from_bytes(rd[e0:e0 + 32], 'big')
    except Exception: return None
def call(url, mode, X, n, rv):
    r = rpc(url, 'eth_call', [tx(mode, X, n, rv), 'latest', OVR], 120)
    if 'result' not in r: return {'err': json.dumps(r)[:300]}
    p, rd = parse(r['result'])
    if mode == 1: p['entrySuccess'] = entry_success(rd) if p['ok'] else None
    if mode == 0: p['unlockRetLen'] = len(rd)
    return p
def ver(u):
    r = rpc(u, 'arc_getVersion', [], 30); c = rpc(u, 'web3_clientVersion', [], 30)
    return {'arc_getVersion': r.get('result', r), 'web3_clientVersion': c.get('result', c)}
def good(p, mode):
    if 'err' in p: return None
    return bool(p['ok']) if mode == 0 else bool(p['ok'] and p['entrySuccess'])
def search(url, mode, n, lo=1000, hi=6_000_000, log=None):
    """smallest X at which the call (mode 0) or the aggregate3 entry (mode 1) succeeds; records the two edge results."""
    assert good(call(url, mode, hi, n, 0), mode)
    while hi - lo > 1:
        m = (lo + hi) // 2
        g = good(call(url, mode, m, n, 0), mode)
        if g is None: raise RuntimeError('rpc error')
        if g: hi = m
        else: lo = m
    return hi, call(url, mode, hi, n, 0), call(url, mode, hi - 1, n, 0)
NS = [0, 4096, 16384, 65536]
def run(url):
    out = {'url': url, 'before': ver(url), 'blk': rpc(url, 'eth_blockNumber', [], 30).get('result')}
    out['calib'] = call(url, 2, 1_000_000, 0, 0)
    out['cases'] = {}
    for n in NS:
        c = {}
        c['a_direct_ample'] = call(url, 0, 5_000_000, n, 0)
        c['a_callfrom_ample'] = call(url, 1, 5_000_000, n, 0)
        c['b_direct_revert'] = call(url, 0, 5_000_000, n, 1)
        c['b_callfrom_revert'] = call(url, 1, 5_000_000, n, 1)
        c['direct_min'] = search(url, 0, n)
        c['callfrom_min'] = search(url, 1, n)
        T = c['callfrom_min'][0]
        sw = []
        for d in sorted(set([1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657])):
            p = call(url, 1, T - d, n, 0)
            sw.append({'X': T - d, 'used': (p['g0'] - p['g1']) if 'g0' in p else None, 'ok': p.get('ok'), 'entrySuccess': p.get('entrySuccess'),
                       'isOperator': p.get('isOperator'), 'tCurrency': p.get('tCurrency'), 'tLock': p.get('tLock'), 'tCount': p.get('tCount'), 'rds': p.get('rds'), 'err': p.get('err')})
        c['sweep_below_callfrom_min'] = sw
        out['cases'][n] = c
        print(url, n, 'direct_min', c['direct_min'][0], 'callfrom_min', c['callfrom_min'][0], flush=True)
    out['after'] = ver(url)
    return out
if __name__ == '__main__' and sys.argv[1] == 'smoke':
    u = sys.argv[2]; print(ver(u)); print(call(u,2,1000000,0,0)); print(call(u,0,5000000,64,0)); print(call(u,1,5000000,64,0)); print(call(u,1,5000000,64,1)); print(call(u,0,5000000,64,1))
elif __name__ == '__main__':
    res = {'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'W': W.hex(), 'overrides': OVR, 'endpoints': []}
    for u in sys.argv[2:]:
        try: res['endpoints'].append(run(u))
        except Exception as e: res['endpoints'].append({'url': u, 'error': str(e)})
        json.dump(res, open(sys.argv[1], 'w'), indent=1, default=str)
