"""Cycle 21, task 2 (L-931). Holder lists from ERC-6909 Transfer logs of the PoolManager (src/ERC6909.sol emits
Transfer(caller, from, to, id, amount) with from, to, id indexed) on networks where cycle 20 found none, then the
cycle 20 measurement (claims.py: driver by state override at the holder's address, unlock, burn(holder,id,bal) and
take(currency,holder,bal), GAS recorded around each, revert) under the mined cap. Read-only.

Windows: first the newest blocks backwards from head in chunks of CHUNK, up to NBACK windows; then NRAND windows of
CHUNK blocks at random starts in [1, head) drawn with random.Random(SEED). Every window, its endpoint, its log count and
any error are recorded. Holders are (to, id) pairs with to != 0; current balance is read with balanceOf.

usage: python3 -I claims2.py <out.json> <chainId> <cap> <chunk> <nback> <nrand> <seed> <logUrl> [callUrl]"""
import sys, json, random, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpc import call, BY  # noqa
import claims as C  # noqa  (cycle 20 driver, parse and selectors)

out, cid, cap, chunk, nback, nrand, seed, lurl = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), sys.argv[8]
curl = sys.argv[9] if len(sys.argv) > 9 else lurl
n = BY[cid]; pm = n['poolManager']
def cv(u):
    r = call(u, 'web3_clientVersion', []); return r.get('result') if isinstance(r, dict) and 'result' in r else r
res = {'chainId': cid, 'name': n['name'], 'cap': cap, 'chunk': chunk, 'seed': seed, 'logUrl': lurl, 'callUrl': curl,
       'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'clientVersionBefore': {lurl: cv(lurl), curl: cv(curl)}, 'windows': [], 'rows': []}
head = int(call(curl, 'eth_blockNumber', [])['result'], 16); res['head'] = head
found = {}
def scan(lo, hi):
    r = call(lurl, 'eth_getLogs', [{'address': pm, 'topics': [C.T_TRANSFER], 'fromBlock': hex(lo), 'toBlock': hex(hi)}], timeout=90)
    wrec = {'from': lo, 'to': hi}
    if isinstance(r, dict) and 'result' in r:
        wrec['logs'] = len(r['result'])
        for lg in r['result']:
            to = '0x' + lg['topics'][2][-40:]; tid = int(lg['topics'][3], 16)
            if int(to, 16) != 0: found.setdefault((to, tid), int(lg['blockNumber'], 16))
    else:
        wrec['error'] = str(r)[:300]
    res['windows'].append(wrec); return wrec
b = head
for _ in range(nback):
    lo = max(0, b - chunk + 1); scan(lo, b); b = lo - 1
    time.sleep(0.3)
rnd = random.Random(seed)
for _ in range(nrand):
    s = rnd.randrange(1, max(2, head - chunk)); scan(s, s + chunk - 1); time.sleep(0.3)
res['candidates'] = len(found)
code = '0x' + C.driver(int(pm, 16)).hex()
for (to, tid), blk in sorted(found.items(), key=lambda kv: -kv[1]):
    if len(res['rows']) >= 20: break
    r = call(curl, 'eth_call', [{'to': pm, 'data': '0x' + (C.S_BAL + C.w(int(to, 16)) + C.w(tid)).hex()}, 'latest'])
    bal = int(r['result'], 16) if isinstance(r, dict) and r.get('result') not in (None, '0x') else 0
    if bal == 0: continue
    amt = min(bal, (1 << 127) - 1)
    script = C.item(C.S_BURN + C.w(int(to, 16)) + C.w(tid) + C.w(amt)) + C.item(C.S_TAKE + C.w(tid) + C.w(int(to, 16)) + C.w(amt)) + b'\0\0'
    rr = call(curl, 'eth_call', [{'from': '0x00000000000000000000000000000000000ca11e', 'to': to, 'data': '0x' + script.hex(), 'gas': hex(cap)}, 'latest', {to: {'code': code}}], timeout=90)
    row = {'holder': to, 'id': hex(tid), 'balance': bal, 'seenBlock': blk}
    if isinstance(rr, dict) and isinstance(rr.get('result'), str):
        row['calls'] = C.parse(bytes.fromhex(rr['result'][2:]))
        row['allOk'] = all(c['ok'] == 1 for c in row['calls']) and len(row['calls']) == 2
        row['gasBurnTake'] = sum(c['gas'] for c in row['calls'])
    else:
        row['error'] = rr
    res['rows'].append(row)
res['clientVersionAfter'] = {lurl: cv(lurl), curl: cv(curl)}; res['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(res, open(out, 'w'), indent=1)
rows = res['rows']
print(cid, n['name'], 'windows', len(res['windows']), 'errs', sum(1 for x in res['windows'] if 'error' in x), 'logs', sum(x.get('logs', 0) for x in res['windows']),
      'cand', len(found), 'rows', len(rows), 'allOk', sum(1 for x in rows if x.get('allOk')), 'max', max([x.get('gasBurnTake', 0) for x in rows] or [0]),
      [str(x.get('error') or [c['ret'][:40] for c in x['calls'] if not c['ok']])[:120] for x in rows if not x.get('allOk')][:3])
print('first window errors', [x['error'][:150] for x in res['windows'] if 'error' in x][:2])
