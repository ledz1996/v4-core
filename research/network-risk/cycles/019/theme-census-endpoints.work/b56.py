"""BNB Chain live census summary: cycle 18 analyse.py over raw/live-56.jsonl, plus a selection check: Pocket's
eth_getLogs of every PoolManager log over the followed blocks (spans of 500) compared with the selected set.
Read only. Usage: b56.py"""
import json, subprocess, ssl, urllib.request, os
os.makedirs('raw/b56', exist_ok=True)
subprocess.run(['python3', '../../018/theme-sync-leak-census.work/analyse.py', 'raw/b56/an.json', '56=raw/live-56.jsonl'], check=True)
A = json.load(open('raw/b56/an.json'))['56']
C = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt'); U = 'https://bsc.api.pocket.network'; PM = '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
def rpc(m, p):
    for k in range(6):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(U, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'}), timeout=90, context=C).read())
            if 'result' in r and r['result'] is not None: return r['result']
        except Exception: pass
    raise RuntimeError(m)
B = [json.loads(l) for l in open('raw/live-56.jsonl.blocks')]
done = [b['block'] for b in B if 'ntx' in b]; lo, hi = min(done), max(done)
rows = [json.loads(l) for l in open('raw/live-56.jsonl')]; sel = {r['tx'] for r in rows}
cv0 = rpc('web3_clientVersion', [])
logtx = set(); a = lo
while a <= hi:
    b = min(hi, a + 499); logtx |= {l['transactionHash'] for l in rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(a), 'toBlock': hex(b)}])}; a = b + 1
A['blocksText'] = f'block {lo:,} to {hi:,} ({len(done):,} blocks)'
A['pocketLogTxs'] = len(logtx); A['pocketMissing'] = len(logtx - sel); A['missing'] = sorted(logtx - sel)
A['traceFailures'] = len(A['traceFailures']); A['clientVersion'] = [cv0, rpc('web3_clientVersion', [])]
json.dump(A, open('raw/b56/analysis.json', 'w'), indent=1)
print(A['stats'], A['blocksText'], A['pocketLogTxs'], A['pocketMissing'], A['traceFailures'], len(A['settleMismatches']), len(A['endsSyncedErc20']))
