"""HyperEVM producer check. The official endpoint https://rpc.hyperliquid.xyz/evm answers eth_getStorageAt with the
latest state whatever block is named (shown in raw/999/official-not-archive.json), so the per-block check cannot use it.
The window holds every PoolManager transaction with a log from deployment to the window head. This takes, for every
PoolManager word that any traced transaction changed, the last traced post value over the whole history, lists the
PoolManager logs after the window head, and compares the words of pools untouched since then with the official
endpoint's latest state, and the native balance likewise. Read-only."""
import json, gzip, os, time, urllib.request, ssl, sys
from rpcu import call
from eps import NETS
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
cid = 999; PM = NETS[cid]['poolManager']; D = '../raw/999'
w = json.load(open(D + '/window.json'))
order = sorted(w['txs'], key=lambda t: (t[1], t[2]))
final = {}; last = {}; bal = None; missing = 0
for h, b, i in order:
    p = '%s/tx/%s.json.gz' % (D, h)
    if not os.path.exists(p): missing += 1; continue
    r = json.load(gzip.open(p))
    dpre = next((v for k, v in r['diff']['pre'].items() if k.lower() == PM.lower()), {})
    dpost = next((v for k, v in r['diff']['post'].items() if k.lower() == PM.lower()), {})
    for s in set(dpre.get('storage') or {}) | set(dpost.get('storage') or {}):
        final[int(s, 16)] = int((dpost.get('storage') or {}).get(s, '0x0'), 16); last[int(s, 16)] = (b, h)
    if 'balance' in dpost: bal = int(dpost['balance'], 16)
U = 'https://rpc.hyperliquid.xyz/evm'
v0 = call(U, 'web3_clientVersion', [], 20)
head = int(call(U, 'eth_blockNumber', [], 20)[0], 16)
newlogs = []
lo = w['head'] + 1
while lo <= head:
    hi = min(head, lo + 999)
    r, e = call(U, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi)}], 60)
    if e: time.sleep(2); continue
    newlogs += r; lo = hi + 1
def batch(reqs):
    body = json.dumps([{'jsonrpc': '2.0', 'id': k, 'method': m, 'params': p} for k, (m, p) in enumerate(reqs)]).encode()
    for t in range(8):
        try:
            rq = urllib.request.Request(U, body, {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            x = json.loads(urllib.request.urlopen(rq, timeout=60, context=CTX).read())
            if isinstance(x, list): return [y.get('result') for y in sorted(x, key=lambda y: y['id'])]
        except Exception as e: pass
        time.sleep(2 + 2 * t)
    return None
slots = sorted(final); mism = []; n = 0
for j in range(0, len(slots), 20):
    g = batch([('eth_getStorageAt', [PM, hex(s), hex(head)]) for s in slots[j:j + 20]])
    if g is None: continue
    for s, x in zip(slots[j:j + 20], g):
        n += 1
        if int(x, 16) != final[s]: mism.append({'slot': hex(s), 'lastTraced': hex(final[s]), 'official': x, 'lastTx': last[s]})
gb = call(U, 'eth_getBalance', [PM, hex(head)], 20)[0]
res = {'officialClient': v0, 'officialHead': head, 'windowHead': w['head'], 'logsAfterWindowHead': len(newlogs),
       'txsAfterWindowHead': sorted({l['transactionHash'] for l in newlogs}), 'slotsCompared': n, 'mismatches': mism,
       'tracedFinalBalance': bal, 'officialBalance': int(gb, 16), 'missingTraces': missing,
       'clientAfter': call(U, 'web3_clientVersion', [], 20)}
json.dump(res, open(D + '/latest-official.json', 'w'), indent=1)
print({k: (v if k != 'mismatches' else len(v)) for k, v in res.items() if k != 'txsAfterWindowHead'})
