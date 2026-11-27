"""Cycle 30 theme-monad-mined-native-coverage: read-only JSON-RPC helper with retries, endpoint rotation and a log of every call."""
import json, time, random, urllib.request, itertools, os, threading
LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'rpc-calls.log')
_lk = threading.Lock(); _id = itertools.count(1)
def rpc(url, m, p, timeout=120):
    body = json.dumps({'jsonrpc': '2.0', 'id': next(_id), 'method': m, 'params': p}).encode()
    req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'rpc-client/1.0'})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r: d = json.loads(r.read())
    with _lk:
        with open(LOG, 'a') as f: f.write(json.dumps({'t': round(t, 1), 'url': url, 'm': m, 'p': str(p)[:160], 'ok': 'result' in d, 'err': str(d.get('error'))[:200] if 'error' in d else None}) + '\n')
    if 'error' in d: raise RuntimeError(str(d['error'])[:300])
    return d['result']
def R(urls, m, p, tries=8, timeout=120):
    if isinstance(urls, str): urls = [urls]
    last = None; o = 0 if m == 'eth_getLogs' else random.randrange(len(urls))
    for k in range(tries):
        u = urls[(k + o) % len(urls)]
        try: return rpc(u, m, p, timeout), u
        except Exception as e:
            last = e
            if 'range' in str(e).lower(): raise
            time.sleep(1.5 * (k + 1))
    raise last
