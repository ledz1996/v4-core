"""Read-only scan: failed or halted deposits (type 0x7e, status 0) followed in the same block by a
PoolManager transaction. Usage: depscan.py <chainId> <rpc> <poolManager> <fromBlock> <toBlock> <outfile>
Method: eth_getLogs for the PoolManager over the window gives candidate blocks and the tx index of
every PoolManager log. For each candidate block the transactions at index 1.. are read until the first
one that is not type 0x7e (index 0 is the L1 attributes deposit). Every deposit found gets its receipt.
A pair is a deposit with status 0x0 whose block has a PoolManager log at a higher tx index.
Every request and the client version before and after are logged."""
import json, sys, time, os, ssl, urllib.request, urllib.error

CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
chain, url, pm, lo, hi, out = int(sys.argv[1]), sys.argv[2], sys.argv[3].lower(), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
log = open(out + '.log', 'a', buffering=1)
stats = {'requests': 0, 'errors': 0}


def post(payload, timeout=120):
    for k in range(6):
        stats['requests'] += 1
        time.sleep(float(os.environ.get('PAUSE', '0')))
        req = urllib.request.Request(url, json.dumps(payload).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=timeout, context=CTX).read())
            return r
        except urllib.error.HTTPError as e:
            stats['errors'] += 1
            log.write('%s HTTP %d %s\n' % (time.strftime('%FT%TZ', time.gmtime()), e.code, e.read()[:200]))
            if e.code in (403, 400):
                raise RuntimeError('HTTP %d' % e.code)
            time.sleep(2 + 3 * k)
        except Exception as e:
            stats['errors'] += 1
            log.write('%s EXC %s\n' % (time.strftime('%FT%TZ', time.gmtime()), str(e)[:200]))
            time.sleep(2 + 3 * k)
    raise RuntimeError('gave up')


def call(method, params):
    r = post({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    if 'error' in r:
        raise RuntimeError(json.dumps(r['error']))
    return r['result']


def batch(reqs, size=int(os.environ.get('BATCH', '25'))):
    res = []
    for i in range(0, len(reqs), size):
        chunk = [{'jsonrpc': '2.0', 'id': j, 'method': m, 'params': p} for j, (m, p) in enumerate(reqs[i:i + size])]
        for attempt in range(5):
            r = post(chunk)
            if isinstance(r, dict):
                r = [r]
            byid = {x.get('id'): x for x in r}
            bad = [j for j in range(len(chunk)) if j not in byid or 'error' in byid[j]]
            if not bad:
                break
            log.write('batch errors %s\n' % json.dumps([byid.get(j, {}).get('error') for j in bad[:3]]))
            time.sleep(2 + 2 * attempt)
        res += [byid[j].get('result') if j in byid else None for j in range(len(chunk))]
    return res


cv0 = call('web3_clientVersion', [])
log.write('%s start %s %s window %d-%d\n' % (time.strftime('%FT%TZ', time.gmtime()), url, cv0, lo, hi))
# 1. PoolManager logs
pmlogs = {}
step = int(os.environ.get('STEP', '2000'))
b = lo
while b <= hi:
    e = min(hi, b + step - 1)
    try:
        logs = call('eth_getLogs', [{'address': pm, 'fromBlock': hex(b), 'toBlock': hex(e)}])
    except RuntimeError as ex:
        if step > 50:
            step //= 2
            log.write('shrink step to %d after %s\n' % (step, str(ex)[:150]))
            continue
        raise
    for L in logs:
        bn = int(L['blockNumber'], 16)
        pmlogs.setdefault(bn, set()).add((int(L['transactionIndex'], 16), L['transactionHash']))
    b = e + 1
cands = sorted(pmlogs)
log.write('candidate blocks %d, pm txs %d\n' % (len(cands), sum(len(v) for v in pmlogs.values())))
# 2. deposits at index 1.. of candidate blocks
deposits = {}  # bn -> list of (idx, hash)
pending = [(bn, 1) for bn in cands]
if os.environ.get('BLOCKMODE'):
    blks = batch([('eth_getBlockByNumber', [hex(bn), True]) for bn in cands], size=int(os.environ.get('BSIZE', '10')))
    for bn, blk in zip(cands, blks):
        for i, tx in enumerate((blk or {}).get('transactions', [])[1:], start=1):
            if tx.get('type') != '0x7e':
                break
            deposits.setdefault(bn, []).append((i, tx['hash'], tx.get('from'), tx.get('to'), tx.get('mint'), tx.get('gas')))
    pending = []
while pending:
    res = batch([('eth_getTransactionByBlockNumberAndIndex', [hex(bn), hex(i)]) for bn, i in pending])
    nxt = []
    for (bn, i), tx in zip(pending, res):
        if tx and tx.get('type') == '0x7e':
            deposits.setdefault(bn, []).append((i, tx['hash'], tx.get('from'), tx.get('to'), tx.get('mint'), tx.get('gas')))
            nxt.append((bn, i + 1))
    pending = nxt
ndep = sum(len(v) for v in deposits.values())
log.write('user deposits in candidate blocks %d\n' % ndep)
# 3. receipts of deposits
flat = [(bn, d) for bn, v in deposits.items() for d in v]
recs = batch([('eth_getTransactionReceipt', [d[1]]) for bn, d in flat])
failed = []
for (bn, d), r in zip(flat, recs):
    if r is None:
        continue
    if r.get('status') == '0x0':
        later = sorted(x for x in pmlogs[bn] if x[0] > d[0])
        failed.append({'block': bn, 'depositIndex': d[0], 'depositHash': d[1], 'from': d[2], 'to': d[3], 'mint': d[4],
                       'gas': d[5], 'gasUsed': r.get('gasUsed'), 'logs': len(r.get('logs', [])),
                       'laterPoolManagerTxs': [{'index': x[0], 'hash': x[1]} for x in later]})
# 4. receipts of the later PoolManager txs in those blocks
pmh = [t['hash'] for f in failed for t in f['laterPoolManagerTxs']]
pmr = dict(zip(pmh, batch([('eth_getTransactionReceipt', [h]) for h in pmh]))) if pmh else {}
for f in failed:
    for t in f['laterPoolManagerTxs']:
        r = pmr.get(t['hash']) or {}
        t['status'] = r.get('status')
        t['to'] = r.get('to')
        t['pmLogTopics0'] = sorted({L['topics'][0] for L in r.get('logs', []) if L['address'].lower() == pm})
cv1 = call('web3_clientVersion', [])
log.write('%s end %s requests %d errors %d\n' % (time.strftime('%FT%TZ', time.gmtime()), cv1, stats['requests'], stats['errors']))
json.dump({'chainId': chain, 'rpc': url, 'poolManager': pm, 'window': [lo, hi], 'clientVersionStart': cv0,
           'clientVersionEnd': cv1, 'candidateBlocks': len(cands), 'poolManagerTxs': sum(len(v) for v in pmlogs.values()),
           'userDepositsInCandidateBlocks': ndep, 'failedDeposits': failed,
           'pairs': sum(1 for f in failed if f['laterPoolManagerTxs'])}, open(out, 'w'), indent=1)
print(chain, 'cands', len(cands), 'deposits', ndep, 'failed', len(failed), 'pairs', sum(1 for f in failed if f['laterPoolManagerTxs']))
