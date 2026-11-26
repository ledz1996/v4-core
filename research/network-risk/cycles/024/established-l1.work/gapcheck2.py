"""Copied unchanged from cycles/021/established-l1.work/gapcheck2.py in cycle 24. Silent log gap check, cycle 19 version of cycles/018/theme-sync-leak-census.work/gapcheck.py.
Same design: PoolManager deployment block by bisection of eth_getCode (on DEPLOYURL, or DEPLOY given), ten windows of
2,000 blocks evenly from deployment to head (plus EXTRA window starts, comma separated, placed on blocks an earlier
census read), eth_getLogs of the PoolManager's Swap and ModifyLiquidity logs on every endpoint (split on range
errors, first span SPAN), then 20 sampled blocks per window (10 uniform, 10 among blocks any endpoint reported logs
for; seed '<chainId>-<window>' in Python's random) whose receipts are counted. Changes from cycle 18:
 - receipts come from eth_getBlockReceipts, or, where an endpoint lacks it, from eth_getTransactionReceipt of every
   transaction of the block; the receipt count is checked against the block's transaction count;
 - receipts are read from every endpoint, not only the first that answers, and each endpoint's getLogs count is
   compared with the receipts of every endpoint;
 - HTTP 400 answers with a range message are treated as range errors.
Read only. Usage: gapcheck2.py <chainId> <pm> <out.json> <url> [<url>...]"""
import sys, os, json, time, random, ssl, urllib.request, urllib.error
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
cid, PM, out = int(sys.argv[1]), sys.argv[2].lower(), sys.argv[3]; URLS = sys.argv[4:]
SPAN = int(os.environ.get('SPAN', '2000')); PACE = float(os.environ.get('PACE', '0'))
TOP = ['0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec']
RANGE = ('range', 'too many', 'exceed', 'too large', 'max', 'block limit', 'results', '10000', 'limit exceeded')
class RangeErr(Exception): pass
DEAD = {}; NOREC = set()
def rpc(u, m, p, tries=7):
    last = None
    if DEAD.get(u, 0) >= 3: raise RuntimeError('HTTP Error 403: Forbidden (endpoint refused this client three times; skipped)')
    for k in range(tries):
        if PACE: time.sleep(PACE)
        try:
            req = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            try: body = urllib.request.urlopen(req, timeout=120, context=CTX).read()
            except urllib.error.HTTPError as e:
                b = e.read()[:400].decode(errors='replace')
                if e.code == 400 and any(x in b.lower() for x in RANGE): raise RangeErr('HTTP 400 ' + b)
                raise RuntimeError('HTTP Error %d: %s' % (e.code, b[:150]))
            r = json.loads(body)
            if 'error' in r:
                msg = str(r['error'])
                if 'rate' in msg.lower(): raise RuntimeError('429 ' + msg)
                if any(x in msg.lower() for x in RANGE): raise RangeErr(msg)
                raise RuntimeError(msg)
            return r['result']
        except RangeErr: raise
        except Exception as e:
            if '403' in str(e): DEAD[u] = DEAD.get(u, 0) + 1
            if DEAD.get(u, 0) >= 3: raise
            if 'does not exist' in str(e) or 'not found' in str(e).lower() and m == 'eth_getBlockReceipts': raise
            last = e; time.sleep((6 if ('429' in str(e) or '403' in str(e)) else 1.5) * (k + 1))
    raise last
def logs(u, a, b, span=None, depth=0):
    span = span or SPAN
    if b - a + 1 > span:
        res = []; x = a
        while x <= b:
            y = min(b, x + span - 1); res += logs(u, x, y, span, depth); x = y + 1
        return res
    try: return rpc(u, 'eth_getLogs', [{'address': PM, 'topics': [TOP], 'fromBlock': hex(a), 'toBlock': hex(b)}])
    except RangeErr:
        if b <= a or depth > 14: raise
        m = (a + b) // 2; return logs(u, a, m, span, depth + 1) + logs(u, m + 1, b, span, depth + 1)
def count(rc): return sum(1 for r in rc for l in r['logs'] if l['address'].lower() == PM and l['topics'] and l['topics'][0] in TOP)
def receipts(u, bn):
    """Returns (method, receipts, number of transactions in the block)."""
    blk = rpc(u, 'eth_getBlockByNumber', [hex(bn), False], tries=4)
    if blk is None: raise RuntimeError('block null')
    ntx = len(blk['transactions'])
    if u not in NOREC:
        try:
            rc = rpc(u, 'eth_getBlockReceipts', [hex(bn)], tries=4)
            if rc is not None: return 'eth_getBlockReceipts', rc, ntx
        except Exception as e:
            if 'does not exist' in str(e) or 'not supported' in str(e).lower() or 'not found' in str(e).lower() or '-32601' in str(e): NOREC.add(u)
            else: raise
    rc = [rpc(u, 'eth_getTransactionReceipt', [h], tries=4) for h in blk['transactions']]
    return 'eth_getTransactionReceipt', [r for r in rc if r is not None], ntx
def first_ok(m, p, urls=None):
    for u in urls or URLS:
        try:
            r = rpc(u, m, p, tries=3)
            if r is not None: return u, r
        except Exception: pass
    raise RuntimeError('no endpoint answered ' + m)
R = {'chainId': cid, 'pm': PM, 'urls': URLS, 'span': SPAN, 'clientVersion': {}, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
if os.path.exists(out):
    old = json.load(open(out))
    if old.get('urls') == URLS and 'windows' in old: R = old
for u in URLS:
    try: R['clientVersion'][u + ' (start %s)' % time.strftime('%H:%M:%S', time.gmtime())] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u + ' (start)'] = 'error: ' + str(e)[:100]
if 'deployBlock' not in R:
    _, head = first_ok('eth_blockNumber', []); head = int(head, 16) - 50
    if os.environ.get('DEPLOY'): dep = int(os.environ['DEPLOY']); src = os.environ.get('DEPLOYSRC', 'given')
    else:
        du = [os.environ['DEPLOYURL']] if os.environ.get('DEPLOYURL') else URLS
        lo, hi = 0, head; src = None
        while lo < hi:
            m = (lo + hi) // 2
            try: src, c = first_ok('eth_getCode', [PM, hex(m)], du)
            except Exception: lo = m + 1; continue
            if c and c != '0x': hi = m
            else: lo = m + 1
        dep = lo; src = 'eth_getCode bisection on ' + str(src)
    R['deployBlock'] = dep; R['deploySource'] = src; R['head'] = head
    starts = [dep + (head - dep - 2000) * k // 9 for k in range(10)]
    if os.environ.get('STARTS'): starts = [int(x) for x in os.environ['STARTS'].split(',')]
    if os.environ.get('EXTRA'): starts += [int(x) for x in os.environ['EXTRA'].split(',')]
    R['starts'] = starts; R['windows'] = []
for k, a in enumerate(R['starts']):
    if k < len(R['windows']): continue
    b = a + 1999; W = {'k': k, 'from': a, 'to': b, 'extra': k >= 10, 'getLogs': {}, 'samples': []}
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
        s = {'block': bn, 'receipts': {}, 'txCount': {}, 'method': {}, 'getLogs': {u: sum(1 for l in L if int(l['blockNumber'], 16) == bn) for u, L in per.items()}}
        for u in URLS:
            try:
                mth, rc, ntx = receipts(u, bn); s['receipts'][u] = count(rc); s['txCount'][u] = [len(rc), ntx]; s['method'][u] = mth
            except Exception as e: s['receipts'][u] = 'error ' + str(e)[:100]
        W['samples'].append(s)
    R['windows'].append(W); print(cid, k, a, W['getLogs'], flush=True)
    json.dump(R, open(out, 'w'), indent=1)
R['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
for u in URLS:
    try: R['clientVersion'][u + ' (end %s)' % time.strftime('%H:%M:%S', time.gmtime())] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u + ' (end)'] = 'error: ' + str(e)[:100]
json.dump(R, open(out, 'w'), indent=1); print('done', cid, flush=True)
