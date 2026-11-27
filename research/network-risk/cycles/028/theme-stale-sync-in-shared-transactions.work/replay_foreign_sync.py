# Read-only replay of recent PoolManager transactions with a foreign sync placed before them in the same transaction.
# The sender gets the runtime code of the public Simple7702Account (0xe6Cae83BdE06E4c305530e199D7217f42808555B) by state override,
# and calls executeBatch on itself at the parent block:
#   control: [original calls]
#   foreign: [PoolManager.sync(T), original calls]        T = a token the PoolManager holds, not the victim's currency
#   native0: [PoolManager.sync(T), PoolManager.sync(0), original calls]  (shows a sync(0) clears it)
# For 0x76 transactions the original calls are the transaction's calls list. ERC-4337 handleOps transactions are replayed
# only where eth_simulateV1 is served (logs are needed to see which user operations swapped).
# No transaction is signed or sent. Seed: none (the newest transactions of out/unlockers.json, in log order).
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
ACC = '0xe6Cae83BdE06E4c305530e199D7217f42808555B'
SW = '0x' + keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
UOE = '0x' + keccak256(b'UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)').hex()
TOK = {480: '0x4200000000000000000000000000000000000006', 4217: '0x20c0000000000000000000000000000000000000', 8453: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'}
EP = {'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789', '0x0000000071727de22e5e9d8baf0edac6f37da032', '0x4337084d9e255ff0702461cf8895ce9e3b5ff108', '0x433709009b8330fda32311df1c2afa402ed8d009'}
URL = {480: net(480)['rpc'], 4217: net(4217)['rpc'], 8453: 'https://mainnet.base.org/'}
SIM = {480: False, 4217: True, 8453: True}
def enc_batch(calls):
    head = u256(32) + u256(len(calls)); offs = []; bodies = []; off = 32 * len(calls)
    for t, v, d in calls:
        b = bytes.fromhex(d[2:] if d.startswith('0x') else d); body = adr(t) + u256(v) + u256(96) + u256(len(b)) + b.hex().ljust(((len(b) + 31) // 32) * 64, '0')
        offs.append(off); bodies.append(body); off += len(body) // 2
    return '0x' + sel('executeBatch((address,uint256,bytes)[])') + head + ''.join(u256(o) for o in offs) + ''.join(bodies)
def run_one(cid, frm, calls, block, code, gas, pm):
    u = URL[cid]; data = enc_batch(calls)
    if SIM[cid]:
        j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'stateOverrides': {frm: {'code': code}}, 'calls': [{'from': frm, 'to': frm, 'data': data, 'gas': hex(gas)}]}], 'validation': False}, hex(block)]}, timeout=90, tries=3)
        if 'error' in j: return {'ok': False, 'rpcError': str(j['error'])[:200]}
        c = j['result'][0]['calls'][0]; logs = c.get('logs', [])
        return {'ok': c['status'] == '0x1', 'ret': (c.get('returnData') or '')[:300], 'err': str(c.get('error'))[:200] if c.get('error') else None,
                'swaps': sum(1 for l in logs if l['address'].lower() == pm.lower() and l['topics'][0] == SW),
                'uoSuccess': [l['data'][2 + 64 * 1: 2 + 64 * 2][-1] for l in logs if l['topics'][0] == UOE]}
    j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'from': frm, 'to': frm, 'data': data, 'gas': hex(gas)}, hex(block), {frm: {'code': code}}]}, timeout=90, tries=3)
    if 'error' in j:
        e = j['error']; d = e.get('data'); d = d if isinstance(d, str) else json.dumps(d)
        return {'ok': False, 'msg': str(e.get('message'))[:150], 'data': (d or '')[:400]}
    return {'ok': True}
def main(cid, maxn):
    U = {r['chainId']: r for r in json.load(open('out/unlockers.json'))}[cid]; n = net(cid); pm = n['poolManager']; u = URL[cid]
    out = dict(chainId=cid, clientBefore=rpc(u, 'web3_clientVersion', []), url=u, token=TOK[cid], results=[])
    code = rpc(u, 'eth_getCode', [ACC, 'latest']); out['accCodeLen'] = len(code) // 2 - 1
    picks = []; seenTo = {}
    for row in U['rows']:
        k = (row['to'], tuple(row['unlockers']))
        if seenTo.get(k, 0) >= 3: continue
        if row['to'] in EP and not SIM[cid]: continue
        seenTo[k] = seenTo.get(k, 0) + 1; picks.append(row)
        if len(picks) >= maxn: break
    def sim(row):
        t = rpc(u, 'eth_getTransactionByHash', [row['h']]); b = int(t['blockNumber'], 16) - 1
        if t.get('type') == '0x76': calls = [((c.get('to') or ''), int(c.get('value', '0x0'), 16), c.get('input') or c.get('data') or '0x') for c in t.get('calls', [])]
        else: calls = [(t['to'], int(t.get('value', '0x0'), 16), t['input'])]
        if any(not c[0] for c in calls): return dict(tx=row['h'], skipped='create call')
        gas = min(int(t['gas'], 16) * 2 + 400000, 30000000)
        syncT = (pm, 0, '0x' + sel('sync(address)') + adr(TOK[cid])); sync0 = (pm, 0, '0x' + sel('sync(address)') + adr('0x' + '00' * 20))
        r = dict(tx=row['h'], type=t.get('type'), to=row['to'], unlockers=row['unlockers'], value=sum(c[1] for c in calls), block=b + 1, ncalls=len(calls))
        try:
            r['control'] = run_one(cid, t['from'], calls, b, code, gas, pm)
            if r['control'].get('ok'):
                r['foreign'] = run_one(cid, t['from'], [syncT] + calls, b, code, gas, pm)
                if not r['foreign'].get('ok') or r['foreign'].get('swaps') != r['control'].get('swaps') or r['foreign'].get('uoSuccess') != r['control'].get('uoSuccess'):
                    r['native0'] = run_one(cid, t['from'], [syncT, sync0] + calls, b, code, gas, pm)
        except Exception as e: r['exc'] = str(e)[:200]
        return r
    with cf.ThreadPoolExecutor(3) as ex: out['results'] = list(ex.map(sim, picks))
    out['clientAfter'] = rpc(u, 'web3_clientVersion', [])
    return out
if __name__ == '__main__':
    cids = [int(x) for x in sys.argv[1:]] or [480, 4217, 8453]
    res = [main(c, 40) for c in cids]
    old = {}
    try: old = {r['chainId']: r for r in json.load(open('out/replay_foreign_sync.json'))}
    except Exception: pass
    for r in res: old[r['chainId']] = r
    json.dump(list(old.values()), open('out/replay_foreign_sync.json', 'w'), indent=1)
    for r in res:
        print(r['chainId'], r['clientBefore'], 'acc code', r['accCodeLen'])
        for x in r['results']:
            c = x.get('control') or {}; f = x.get('foreign') or {}
            v = 'control failed ' + str(c)[:120] if not c.get('ok') else ('SAME' if f.get('ok') and f.get('swaps') == c.get('swaps') and f.get('uoSuccess') == c.get('uoSuccess') else 'DIFF ' + str(f)[:200] + ' | native0 ' + str(x.get('native0'))[:150])
            print('  %s type %s to %s val %s swaps %s uo %s : %s' % (x['tx'][:12], x.get('type'), x.get('to', '')[:12], x.get('value'), c.get('swaps'), c.get('uoSuccess'), v), x.get('exc', ''), x.get('skipped', ''))
