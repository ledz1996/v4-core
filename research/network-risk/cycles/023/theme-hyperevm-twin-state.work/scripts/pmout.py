# ERC-20 Transfer logs with the PoolManager as 'from' over its whole history (any contract), and the gas price and
# sender of each transaction that carried one. Also the PoolManager nonce on each endpoint at latest.
import json, sys, collections
from rpc import rpc, batch
R = sys.argv[1]; out = sys.argv[2]
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
res = {'replica': R, 'clientVersionStart': rpc(R, 'web3_clientVersion', [])}
latest = int(rpc(R, 'eth_blockNumber', []), 16); res['latest'] = latest
logs = []; b = 45998366; step = 500000
while b <= latest:
    e = min(b + step - 1, latest)
    try: r = rpc(R, 'eth_getLogs', [{'fromBlock': hex(b), 'toBlock': hex(e), 'topics': [T, '0x' + PM[2:].lower().rjust(64, '0')]}], timeout=120)
    except Exception as ex: print('err', b, str(ex)[:150]); step = max(step // 2, 10000); continue
    logs += r; b = e + 1
res['transferFromPM'] = len(logs)
hashes = sorted({l['transactionHash'] for l in logs})
txs = {}
for i in range(0, len(hashes), 20):
    for h, t in zip(hashes[i:i + 20], batch(R, [('eth_getTransactionByHash', [h]) for h in hashes[i:i + 20]])):
        txs[h] = t
gp0 = [h for h, t in txs.items() if isinstance(t, dict) and t.get('gasPrice') and int(t['gasPrice'], 16) == 0]
res['txs'] = len(txs); res['gasPriceZeroTxs'] = [[h, txs[h]['from'], txs[h]['to'], txs[h]['input'][:10]] for h in gp0]
res['tokens'] = collections.Counter(l['address'].lower() for l in logs).most_common()
res['txTargets'] = collections.Counter((t.get('to') or '').lower() for t in txs.values() if isinstance(t, dict)).most_common(30)
res['clientVersionEnd'] = rpc(R, 'web3_clientVersion', [])
json.dump(res, open(out, 'w'), indent=0)
print(res['transferFromPM'], res['txs'], len(gp0), res['tokens'][:5])
