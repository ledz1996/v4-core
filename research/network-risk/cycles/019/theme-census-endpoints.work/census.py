"""Copy of cycles/018/theme-sync-leak-census.work/census.py; cycle 19 change: a null trace result counts as a failed try and is retried on the next endpoint.
Sync leak census. For each transaction, takes the callTracer tree and lists the calls into the PoolManager in
execution order, with the reverted flag of the frame or an ancestor, and the balanceOf outputs of the
PoolManager's own child calls. Then replays the transient model of the source (CurrencyReserves set by sync,
reset by settle, empty at transaction start) and checks every completed settle/settleFor output against the
model. Read-only JSON-RPC (debug_traceTransaction, eth_getTransactionByHash).
Usage: census.py <pm> <out.jsonl> <threads> <txlist.json> <url> [<url> ...]"""
import sys, os, json, time, itertools, ssl, urllib.request, concurrent.futures as cf
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
PM, out, th, lst = sys.argv[1].lower(), sys.argv[2], int(sys.argv[3]), sys.argv[4]
URLS = sys.argv[5:]; cnt = itertools.count()
SEL = {'0xa5841194': 'sync', '0x11da60b4': 'settle', '0x3dd45adb': 'settleFor', '0x0b0d9c09': 'take', '0x48c89491': 'unlock',
       '0x80f0b44c': 'clear', '0x156e29f6': 'mint', '0xf5298aca': 'burn'}
def rpc(m, p, tries=8):
    last = None
    for k in range(tries):
        u = URLS[next(cnt) % len(URLS)]
        try:
            req = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            r = json.loads(urllib.request.urlopen(req, timeout=120, context=CTX).read())
            if 'error' in r: raise RuntimeError(str(r['error'])[:300])
            if r.get('result') is None: raise RuntimeError('null result from ' + u)
            return r['result']
        except Exception as e:
            last = e; time.sleep(1 + k)
    raise last
def walk(fr, acc, rev=False):
    err = fr.get('error'); r = rev or bool(err)
    to = (fr.get('to') or '').lower()
    if to == PM:
        inp = fr.get('input', '0x'); s = inp[:10]
        bal = [c.get('output') for c in (fr.get('calls') or []) if (c.get('input') or '')[:10] == '0x70a08231'
               and (c.get('input') or '')[34:74] == PM[2:]]
        acc.append({'sel': SEL.get(s, s), 'arg': ('0x' + inp[34:74]) if len(inp) >= 74 else None,
                    'value': int(fr.get('value') or '0x0', 16), 'rev': r, 'from': (fr.get('from') or '').lower(),
                    'out': fr.get('output'), 'bal': bal, 'err': err})
    for c in fr.get('calls') or []: walk(c, acc, r)
Z = '0x' + '0' * 40
def model(frames):
    """Returns (synced currency at the end, list of settle checks that disagree, number of settle checks)."""
    synced, reserves = None, None; bad = []; n = 0
    for f in frames:
        if f['rev']: continue
        if f['sel'] == 'sync':
            if f['arg'] == Z or f['arg'] is None: synced, reserves = None, None
            else:
                synced = f['arg']; reserves = int(f['bal'][0], 16) if f['bal'] and f['bal'][0] not in (None, '0x') else None
        elif f['sel'] in ('settle', 'settleFor'):
            n += 1
            got = int(f['out'], 16) if f['out'] not in (None, '0x') else None
            if synced is None: exp = f['value']
            else:
                now = int(f['bal'][0], 16) if f['bal'] and f['bal'][0] not in (None, '0x') else None
                exp = (now - reserves) if (now is not None and reserves is not None) else None
            if got is None or exp is None or got != exp:
                bad.append({'sel': f['sel'], 'synced': synced, 'exp': exp, 'got': got, 'value': f['value']})
            synced, reserves = None, None
    return synced, bad, n
def one(h):
    try:
        t = rpc('debug_traceTransaction', [h, {'tracer': 'callTracer'}]); tx = rpc('eth_getTransactionByHash', [h])
    except Exception as e:
        return {'tx': h, 'fail': str(e)[:200]}
    acc = []; walk(t, acc)
    s, bad, n = model(acc) if not t.get('error') else (None, [], 0)
    return {'tx': h, 'block': int(tx['blockNumber'], 16), 'idx': int(tx['transactionIndex'], 16), 'ok': not t.get('error'),
            'from': tx['from'].lower(), 'to': (tx.get('to') or '').lower(), 'endSynced': s, 'settleChecks': n, 'bad': bad,
            'frames': [[f['sel'], f['arg'], f['value'], f['rev'], f['from']] for f in acc]}
txs = json.load(open(lst))
done = set()
if os.path.exists(out):
    for line in open(out):
        try:
            j = json.loads(line)
            if 'fail' not in j: done.add(j['tx'])
        except Exception: pass
todo = [t for t in txs if t not in done]
f = open(out, 'a'); k = 0; t0 = time.time()
with cf.ThreadPoolExecutor(th) as ex:
    for r in ex.map(one, todo):
        f.write(json.dumps(r) + '\n'); k += 1
        if k % 1000 == 0: f.flush(); print(k, len(todo), round(time.time() - t0), flush=True)
f.close(); print('finished', k, flush=True)
