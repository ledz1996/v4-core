"""Transactions touching the PoolManager by logs: any log emitted by the PoolManager, and ERC-20 Transfer logs
with the PoolManager as sender or recipient. Read-only eth_getLogs, split on range errors.
Usage: logscan.py <pm> <lo> <hi> <span> <out.json> <threads> <url> [<url>...]"""
import sys, os, json, time, itertools, ssl, urllib.request, concurrent.futures as cf
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
PM, lo, hi, span, out, th = sys.argv[1].lower(), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], int(sys.argv[6])
URLS = sys.argv[7:]; cnt = itertools.count()
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; top = '0x' + '0' * 24 + PM[2:]
def rpc(m, p, tries=6):
    last = None
    for k in range(tries):
        u = URLS[next(cnt) % len(URLS)]
        try:
            req = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            r = json.loads(urllib.request.urlopen(req, timeout=120, context=CTX).read())
            if 'error' in r:
                msg = str(r['error'])
                if any(x in msg.lower() for x in ('range', 'limit', 'too many', 'exceed', 'large', 'max')): raise ValueError(msg)
                raise RuntimeError(msg)
            return r['result']
        except ValueError: raise
        except Exception as e:
            last = e; time.sleep(1 + k)
    raise last
def go(flt, a, b):
    try: return rpc('eth_getLogs', [dict(flt, fromBlock=hex(a), toBlock=hex(b))])
    except ValueError:
        if b <= a: raise
        m = (a + b) // 2; return go(flt, a, m) + go(flt, m + 1, b)
FL = {'pm': {'address': PM}, 'in': {'topics': [T, None, top]}, 'out': {'topics': [T, top]}}
def one(a):
    b = min(hi, a + span - 1); res = {}
    for k, flt in FL.items():
        res[k] = [(int(l['blockNumber'], 16), int(l['transactionIndex'], 16), l['transactionHash'], (l['topics'] or [None])[0]) for l in go(flt, a, b)]
    return a, b, res
txs = {}; windows = []; t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(th) as ex:
    for a, b, res in ex.map(one, range(lo, hi + 1, span)):
        windows.append([a, b, {k: len(v) for k, v in res.items()}])
        for k, v in res.items():
            for bn, ix, h, t0p in v:
                e = txs.setdefault(h, {'block': bn, 'idx': ix, 'kinds': []})
                if k not in e['kinds']: e['kinds'].append(k)
        n += 1
        if n % 200 == 0: print(n, len(txs), round(time.time() - t0), flush=True)
json.dump({'pm': PM, 'lo': lo, 'hi': hi, 'urls': URLS, 'windows': windows, 'txs': txs}, open(out, 'w'))
print('done', len(txs), flush=True)
