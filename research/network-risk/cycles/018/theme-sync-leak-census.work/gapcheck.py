"""Silent log gap check. For one network: find the PoolManager deployment block by binary search of eth_getCode,
place ten windows of 2,000 blocks evenly from deployment to head, ask every endpoint for the PoolManager's Swap and
ModifyLiquidity logs of each window (eth_getLogs, split on range errors), then sample 20 blocks per window (10 uniform,
10 among blocks any endpoint reported logs for; seed '<chainId>-<window>' in Python's random) and count the same
logs in eth_getBlockReceipts. Every endpoint's getLogs count on the sampled blocks is compared with the receipts.
When they disagree, the endpoint's own receipts for that block are also read. Read only.
Usage: gapcheck.py <chainId> <pm> <out.json> <url> [<url>...]"""
import sys, os, json, time, random, ssl, urllib.request
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
cid, PM, out = int(sys.argv[1]), sys.argv[2].lower(), sys.argv[3]; URLS = sys.argv[4:]
TOP = ['0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec']
class RangeErr(Exception): pass
DEAD = {}
def rpc(u, m, p, tries=6):
    last = None
    if DEAD.get(u, 0) >= 3: raise RuntimeError('HTTP Error 403: Forbidden (endpoint refused this client three times; skipped)')
    for k in range(tries):
        try:
            req = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            body = urllib.request.urlopen(req, timeout=120, context=CTX).read()
            r = json.loads(body)
            if 'error' in r:
                msg = str(r['error'])
                if any(x in msg.lower() for x in ('range', 'too many', 'exceed', 'too large', 'max', 'block limit', 'results', '10000', 'limit exceeded')): raise RangeErr(msg)
                raise RuntimeError(msg)
            return r['result']
        except RangeErr: raise
        except Exception as e:
            if '403' in str(e): DEAD[u] = DEAD.get(u, 0) + 1
            if DEAD.get(u, 0) >= 3: raise
            last = e; time.sleep((6 if ('429' in str(e) or '403' in str(e)) else 1.5) * (k + 1))
    raise last
def logs(u, a, b, depth=0):
    try: return rpc(u, 'eth_getLogs', [{'address': PM, 'topics': [TOP], 'fromBlock': hex(a), 'toBlock': hex(b)}])
    except RangeErr:
        if b <= a or depth > 12: raise
        m = (a + b) // 2; return logs(u, a, m, depth + 1) + logs(u, m + 1, b, depth + 1)
def first_ok(m, p):
    for u in URLS:
        try:
            r = rpc(u, m, p, tries=3)
            if r is not None: return u, r
        except Exception: pass
    raise RuntimeError('no endpoint answered ' + m)
R = {'chainId': cid, 'pm': PM, 'urls': URLS, 'clientVersion': {}, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
for u in URLS:
    try: R['clientVersion'][u] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u] = 'error: ' + str(e)[:100]
_, head = first_ok('eth_blockNumber', []); head = int(head, 16) - 50
lo, hi = 0, head; src = None
if os.environ.get('DEPLOY'): lo = hi = int(os.environ['DEPLOY']); src = 'first PoolManager log, bisected by eth_getLogs (deploybisect.py)'
while lo < hi:  # first block with code
    m = (lo + hi) // 2
    try: src, c = first_ok('eth_getCode', [PM, hex(m)])
    except Exception: lo = m + 1; continue
    if c and c != '0x': hi = m
    else: lo = m + 1
dep = lo; R['deployBlock'] = dep; R['deploySource'] = src; R['head'] = head
starts = [dep + (head - dep - 2000) * k // 9 for k in range(10)]
R['windows'] = []
for k, a in enumerate(starts):
    b = a + 1999; W = {'k': k, 'from': a, 'to': b, 'getLogs': {}, 'samples': []}
    per = {}
    for u in URLS:
        try:
            L = logs(u, a, b); per[u] = L; W['getLogs'][u] = len(L)
        except Exception as e:
            W['getLogs'][u] = 'error: ' + str(e)[:150]
    rnd = random.Random(f'{cid}-{k}')
    seen = sorted({int(l['blockNumber'], 16) for L in per.values() for l in L})
    samp = sorted(set(rnd.sample(range(a, b + 1), 10)) | set(rnd.sample(seen, min(10, len(seen)))))
    for bn in samp:
        try: ru, rc = first_ok('eth_getBlockReceipts', [hex(bn)])
        except Exception as e:
            W['samples'].append({'block': bn, 'receipts': 'error ' + str(e)[:80]}); continue
        n = sum(1 for r in rc for l in r['logs'] if l['address'].lower() == PM and l['topics'] and l['topics'][0] in TOP)
        s = {'block': bn, 'receiptsFrom': ru, 'receipts': n, 'getLogs': {u: sum(1 for l in L if int(l['blockNumber'], 16) == bn) for u, L in per.items()}}
        for u, c in s['getLogs'].items():
            if c != n:
                try:
                    rc2 = rpc(u, 'eth_getBlockReceipts', [hex(bn)], tries=3)
                    s.setdefault('ownReceipts', {})[u] = sum(1 for r in rc2 for l in r['logs'] if l['address'].lower() == PM and l['topics'] and l['topics'][0] in TOP)
                except Exception as e: s.setdefault('ownReceipts', {})[u] = 'error ' + str(e)[:80]
        W['samples'].append(s)
    R['windows'].append(W); print(cid, k, a, W['getLogs'], flush=True)
    json.dump(R, open(out, 'w'), indent=1)
R['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
for u in URLS:
    try: R['clientVersion'][u + ' (end)'] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u + ' (end)'] = 'error: ' + str(e)[:100]
json.dump(R, open(out, 'w'), indent=1); print('done', cid, flush=True)
