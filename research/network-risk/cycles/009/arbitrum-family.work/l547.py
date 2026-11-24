"""Lead L-547 on Robinhood Chain: find mined transactions in which a call into PoolManager.unlock
reverted and a later unlock in the same transaction succeeded. Reads PoolManager logs, then
debug_traceTransaction (callTracer) on robinhood.drpc.org. Usage: python3 -I l547.py <out.json> <maxTx>"""
import sys, json, urllib.request, concurrent.futures as cf
PM = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
RPC = 'https://rpc.mainnet.chain.robinhood.com'; TR = 'https://robinhood.drpc.org'
def rpc(url, m, p):
    req = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    r = json.load(urllib.request.urlopen(req, timeout=90))
    if 'error' in r: raise Exception(str(r['error'])[:200])
    return r['result']
head = int(rpc(RPC, 'eth_blockNumber', []), 16)
txs = []; seen = set(); to = head
while len(txs) < int(sys.argv[2]) and to > head - 2_000_000:
    logs = rpc(RPC, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(to - 2000), 'toBlock': hex(to)}])
    for l in reversed(logs):
        if l['transactionHash'] not in seen: seen.add(l['transactionHash']); txs.append(l['transactionHash'])
    to -= 2001
txs = txs[:int(sys.argv[2])]
def walk(c, acc):
    if c.get('to', '').lower() == PM and c.get('input', '')[:10] == '0x48c89491':
        acc.append(('error' in c, c.get('error', '')))
    for k in c.get('calls', []) or []: walk(k, acc)
def one(h):
    import time
    for k in range(6):
        try:
            t = rpc(TR, 'debug_traceTransaction', [h, {'tracer': 'callTracer'}]); break
        except Exception as e:
            err = str(e)[:100]; time.sleep(3 * (k + 1))
    else:
        return h, None, err
    acc = []; walk(t, acc); return h, acc, t.get('error', '')
res = []; hits = []
with cf.ThreadPoolExecutor(2) as ex:
    for h, acc, err in ex.map(one, txs):
        res.append({'tx': h, 'unlocks': acc, 'txError': err})
        if acc and any(a[0] for a in acc):
            first = next(i for i, a in enumerate(acc) if a[0])
            if any(not a[0] for a in acc[first + 1:]): hits.append(h)
traced = sum(1 for r in res if r['unlocks'] is not None)
print('head', head, 'txs', len(txs), 'traced', traced, 'with reverted unlock', sum(1 for r in res if r['unlocks'] and any(a[0] for a in r['unlocks'])), 'reverted-then-successful', len(hits), hits[:5])
json.dump({'head': head, 'traced': traced, 'hits': hits, 'rows': res}, open(sys.argv[1], 'w'), indent=1)
