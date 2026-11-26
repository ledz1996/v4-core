"""Task 4b (cycle 24, theme-failed-tx-replay): for up to N mined failed transactions that entered the PoolManager, eth_call the same
call (from, to, input, value, gas) at the parent block on a second endpoint and compare with the mined result (callTracer root error
and output). usage: ethcall.py <cid> <url> <N> <seed>. Read-only. The parent state is the state before the block, so transactions
earlier in the same block are missing from it; 'exactParent' marks transactions at index 0, whose parent state is exact.
Writes results/ethcall-<cid>.json (summary) and results/ethcall-<cid>.jsonl (every record in full)."""
import json, os, sys, gzip, glob, random, time, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
cid = int(sys.argv[1]); url = sys.argv[2]; N = int(sys.argv[3]); seed = int(sys.argv[4])
HERE = os.path.dirname(os.path.abspath(__file__)); D = HERE + '/../raw/%d' % cid
recs = []
for fn in sorted(glob.glob(D + '/tx/*.json.gz')):
    r = json.load(gzip.open(fn))
    if r.get('kind') == 'failed': recs.append(r)
rng = random.Random(seed); recs = recs if len(recs) <= N else rng.sample(recs, N)
v0, e0 = call(url, 'web3_clientVersion', [], 30)
out = open(HERE + '/../results/ethcall-%d.jsonl' % cid, 'w'); cnt = collections.Counter()
for r in recs:
    tx, e = call(url, 'eth_getTransactionByHash', [r['hash']], 60)
    if not tx: cnt['tx-not-found'] += 1; out.write(json.dumps({'hash': r['hash'], 'err': e}) + '\n'); continue
    c = {'from': tx['from'], 'to': tx['to'], 'data': tx['input'], 'value': tx['value'], 'gas': tx['gas']}
    for k in range(4):
        res, err = call(url, 'eth_call', [c, hex(r['block'] - 1)], 90)
        if not (err and ('429' in err or 'EXC' in err)): break
        time.sleep(3 + 3 * k)
    mined_out = r['call'].get('output') or '0x'; mined_err = r['call'].get('error')
    if err is None: got = 'success'; data = res
    else:
        data = None
        try:
            j = json.loads(err.split(' ', 1)[1]) if err.startswith('RPCERR') else None
            data = j.get('data') if isinstance(j, dict) else None
            if isinstance(data, dict): data = data.get('data')
        except Exception: pass
        low = err.lower()
        got = 'revert' if ('revert' in low or data) else ('endpoint-error')
        if 'out of gas' in low or 'gas required exceeds' in low: got = 'oog'
    if got == 'revert': cls = 'same-revert-data' if (data or '0x') == mined_out or (data is None and mined_out in ('0x', '')) else 'reverts-other-data'
    else: cls = got
    cnt[cls] += 1
    if tx.get('transactionIndex') == '0x0': cnt['exactParent:' + cls] += 1
    out.write(json.dumps({'hash': r['hash'], 'block': r['block'], 'index': int(tx['transactionIndex'], 16), 'minedError': mined_err, 'minedOutput': mined_out[:300],
                          'callResult': got, 'callData': (data or res or '')[:300] if isinstance(data or res, str) else data, 'callErr': (err or '')[:300], 'class': cls}) + '\n')
v1, e1 = call(url, 'web3_clientVersion', [], 30)
summ = {'chainId': cid, 'url': url, 'clientBefore': v0, 'clientAfter': v1, 'traceEndpoints': sorted(set(r.get('url') for r in recs)), 'n': len(recs), 'seed': seed, 'classes': dict(cnt)}
json.dump(summ, open(HERE + '/../results/ethcall-%d.json' % cid, 'w'), indent=1); print(json.dumps(summ))
