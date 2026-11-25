"""ERC-6909 claim redemption (burn + take) by real claim holders at the real PoolManager, under a gas limit equal
to the network's mined per-transaction cap. Read-only. A measuring driver is placed by state override at the
holder's own address (only its code is replaced; the PoolManager's code and storage stay as on chain). The
driver calls unlock; in the callback it runs burn(holder, id, balance) and take(currency, holder, balance),
records GAS before and after each call, and reverts with the record, so nothing is settled or persists.
usage: python3 -I claims.py <caps.json> <out.json> [chainId ...]"""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpc import call, NET
from evm import keccak, assemble

def sel(sig): return keccak(sig.encode())[:4]
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
S_UNLOCK = sel('unlock(bytes)'); S_CB = sel('unlockCallback(bytes)')
S_BURN = sel('burn(address,uint256,uint256)'); S_TAKE = sel('take(address,address,uint256)')
S_BAL = sel('balanceOf(address,uint256)')
T_TRANSFER = '0x' + keccak(b'Transfer(address,address,address,uint256,uint256)').hex()

def driver(pm):
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(S_CB, 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(S_UNLOCK, 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pm), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x2000), ('PUSH', 68),
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 240), 'SHR',
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP3', ('PUSH', 2), 'ADD', ('PUSH', 0), 'CALLDATACOPY',
         'GAS', 'DUP4', ('PUSH', 32), 'ADD', 'MSTORE',
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pm), 'GAS', 'CALL',
         'GAS', 'DUP5', ('PUSH', 64), 'ADD', 'MSTORE',
         'DUP4', 'MSTORE',
         'RETURNDATASIZE', 'DUP4', ('PUSH', 96), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP5', ('PUSH', 128), 'ADD', 'RETURNDATACOPY',
         'SWAP2', ('PUSH', 128), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP2',
         ('PUSH', 2), 'ADD', 'ADD',
         ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP',
         ('PUSH', 0x2000), 'SWAP1', 'SUB', ('PUSH', 0x2000), 'REVERT']
    return assemble(p)

def item(b): return len(b).to_bytes(2, 'big') + b

def parse(buf):
    out = []; i = 0
    while i + 128 <= len(buf):
        ok = int.from_bytes(buf[i:i+32], 'big'); g0 = int.from_bytes(buf[i+32:i+64], 'big'); g1 = int.from_bytes(buf[i+64:i+96], 'big')
        rds = int.from_bytes(buf[i+96:i+128], 'big'); rd = buf[i+128:i+128+rds]
        out.append({'ok': ok, 'gas': g0 - g1, 'ret': rd.hex()[:200]}); i += 128 + rds
    return out

def holders(url, pm, head, span, chunk):
    found = {}
    b = head
    while b > head - span and len(found) < 60:
        lo = max(0, b - chunk + 1)
        r = call(url, 'eth_getLogs', [{'address': pm, 'topics': [T_TRANSFER], 'fromBlock': hex(lo), 'toBlock': hex(b)}])
        if not isinstance(r, dict) or 'result' not in r:
            if chunk > 50: chunk //= 4; continue
            break
        for lg in r['result']:
            to = '0x' + lg['topics'][2][-40:]; cid = int(lg['topics'][3], 16)
            if int(to, 16) != 0: found[(to, cid)] = 1
        b = lo - 1
    return list(found)

def run(n, cap):
    url = n['rpc']; pm = n['poolManager']; cid = n['chainId']
    out = {'chainId': cid, 'name': n['name'], 'gasLimit': cap, 'rows': []}
    head = int(call(url, 'eth_blockNumber', [])['result'], 16)
    import os
    hs = holders(url, pm, head, int(os.environ.get('SPAN', 400000)), int(os.environ.get('CHUNK', 20000)))
    out['candidates'] = len(hs)
    for to, tid in hs:
        if len(out['rows']) >= 8: break
        r = call(url, 'eth_call', [{'to': pm, 'data': '0x' + (S_BAL + w(int(to, 16)) + w(tid)).hex()}, 'latest'])
        bal = int(r['result'], 16) if isinstance(r, dict) and r.get('result') not in (None, '0x') else 0
        if bal == 0: continue
        amt = min(bal, (1 << 127) - 1)
        script = item(S_BURN + w(int(to, 16)) + w(tid) + w(amt)) + item(S_TAKE + w(tid) + w(int(to, 16)) + w(amt)) + b'\0\0'
        code = '0x' + driver(int(pm, 16)).hex()
        res = call(url, 'eth_call', [{'from': '0x00000000000000000000000000000000000ca11e', 'to': to, 'data': '0x' + script.hex(), 'gas': hex(cap)},
                                     'latest', {to: {'code': code}}])
        row = {'holder': to, 'id': hex(tid), 'balance': bal}
        if isinstance(res, dict) and isinstance(res.get('result'), str):
            row['calls'] = parse(bytes.fromhex(res['result'][2:]))
            row['allOk'] = all(c['ok'] == 1 for c in row['calls']) and len(row['calls']) == 2
            row['gasBurnTake'] = sum(c['gas'] for c in row['calls'])
        else:
            row['error'] = res
        out['rows'].append(row)
    return out

if __name__ == '__main__':
    caps = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}
    ids = [int(a) for a in sys.argv[3:]] or [n['chainId'] for n in NET]
    nets = [n for n in NET if n['chainId'] in ids]
    with cf.ThreadPoolExecutor(7) as ex:
        res = list(ex.map(lambda n: run(n, caps[n['chainId']]), nets))
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
    for r in res:
        rows = r['rows']
        print(r['chainId'], r['name'], 'cand', r.get('candidates'), 'rows', len(rows), 'allOk', sum(1 for x in rows if x.get('allOk')),
              'max', max([x.get('gasBurnTake', 0) for x in rows] or [0]), [str(x.get('error') or [c['ret'][:40] for c in x['calls'] if not c['ok']])[:100] for x in rows if not x.get('allOk')][:2])
