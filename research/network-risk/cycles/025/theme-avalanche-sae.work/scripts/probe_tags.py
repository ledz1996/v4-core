"""Task 1 probe for theme-avalanche-sae (cycle 25). Read-only JSON-RPC only.
For each endpoint: one batch that asks for eth_blockNumber and the header of latest, pending, safe and finalized,
then per tag eth_getBalance, eth_getStorageAt and eth_call (extsload of slot 6 and Lock state read through exttload)
at the PoolManager, then the same reads at explicit numbers: latest+1 .. pending (accepted, possibly not executed),
pending+1 and pending+50 (not accepted). Latency of each explicit-number request is recorded, because the SAE backend
waits for execution of an accepted block (restoreExecutedBlock -> WaitUntilExecuted). Brackets with web3_clientVersion.
usage: probe_tags.py <out.json> [rounds]"""
import json, sys, time, ssl, urllib.request
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
PM = '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
URLS = ['https://api.avax.network/ext/bc/C/rpc', 'https://avax.api.pocket.network']
def post(u, body, timeout=60):
    rq = urllib.request.Request(u, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    t = time.time()
    try:
        r = json.loads(urllib.request.urlopen(rq, timeout=timeout, context=CTX).read())
    except Exception as e:
        return {'exc': str(e)[:200]}, time.time() - t
    return r, time.time() - t
def one(u, m, p):
    r, dt = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p})
    return {'method': m, 'params': p, 'resp': r.get('result', r.get('error', r)), 'sec': round(dt, 3)}
# extsload(bytes32) selector 0x1e2eaeaf, slot 6 is protocolFeeController or similar fixed slot; any fixed slot will do
def extsload(slot):
    return '0x1e2eaeaf' + format(slot, '064x')
out = {'rounds': []}
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
for rd in range(rounds):
    for u in URLS:
        R = {'url': u, 't': time.time()}
        R['clientBefore'] = one(u, 'web3_clientVersion', [])['resp']
        tags = ['latest', 'pending', 'safe', 'finalized']
        batch = [{'jsonrpc': '2.0', 'id': 0, 'method': 'eth_blockNumber', 'params': []}]
        for i, tg in enumerate(tags):
            batch.append({'jsonrpc': '2.0', 'id': 1 + i, 'method': 'eth_getBlockByNumber', 'params': [tg, False]})
        r, dt = post(u, batch)
        if isinstance(r, list):
            r = sorted(r, key=lambda x: x['id'])
            R['blockNumber'] = int(r[0]['result'], 16) if 'result' in r[0] else r[0]
            R['heads'] = {}
            for i, tg in enumerate(tags):
                x = r[1 + i].get('result') or r[1 + i].get('error')
                if isinstance(x, dict) and 'number' in x:
                    x = {'number': int(x['number'], 16), 'hash': x['hash'], 'stateRoot': x['stateRoot'], 'baseFeePerGas': x.get('baseFeePerGas'), 'timestamp': int(x['timestamp'], 16), 'txs': len(x.get('transactions', []))}
                R['heads'][tg] = x
        else:
            R['batchErr'] = r
        R['perTag'] = {}
        for tg in tags:
            R['perTag'][tg] = [one(u, 'eth_getBalance', [PM, tg]), one(u, 'eth_getStorageAt', [PM, '0x6', tg]),
                               one(u, 'eth_call', [{'to': PM, 'data': extsload(6)}, tg]),
                               one(u, 'eth_getTransactionCount', ['0x0000000000000000000000000000000000000000', tg])]
        try:
            lat = R['heads']['latest']['number']; pen = R['heads']['pending']['number']
        except Exception:
            lat = pen = None
        R['explicit'] = []
        if lat is not None:
            for n in sorted(set(list(range(lat, pen + 1)) + [pen + 1, pen + 50])):
                R['explicit'].append({'n': n, 'rel': 'latest+%d' % (n - lat),
                                      'reads': [one(u, 'eth_getBalance', [PM, hex(n)]), one(u, 'eth_call', [{'to': PM, 'data': extsload(6)}, hex(n)]),
                                                one(u, 'eth_getBlockReceipts', [hex(n)]) if n <= pen + 1 else None]})
                # receipts can be long; keep only count
                rr = R['explicit'][-1]['reads'][2]
                if rr and isinstance(rr['resp'], list): rr['resp'] = {'receipts': len(rr['resp'])}
        R['clientAfter'] = one(u, 'web3_clientVersion', [])['resp']
        out['rounds'].append(R)
        print(u, R.get('blockNumber'), {k: (v.get('number') if isinstance(v, dict) else v) for k, v in R.get('heads', {}).items()}, flush=True)
    time.sleep(3)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
