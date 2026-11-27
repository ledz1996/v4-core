# Shared helpers for the shared-transaction theme. Read-only JSON-RPC and explorer reads only.
import json, os, sys, time, requests
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from keccak import keccak256
NETS = json.load(open(os.path.join(HERE, '..', '..', '..', 'state', 'networks.json')))['networks']
DL = os.path.join(HERE, 'dl')
S = requests.Session()
S.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
MC3 = '0xcA11bde05977b3631167028862bE2a173976CA11'
def post(url, payload, timeout=40, tries=4):
    last = None
    for i in range(tries):
        try:
            r = S.post(url, data=json.dumps(payload), timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                last = 'http %d %s' % (r.status_code, r.text[:120]); time.sleep(1.5 * (i + 1)); continue
            return r.json()
        except Exception as e:
            last = repr(e)[:200]; time.sleep(1.0 * (i + 1))
    raise Exception('post failed: ' + str(last))
def rpc(url, method, params, **kw):
    j = post(url, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}, **kw)
    if 'error' in j: raise Exception(json.dumps(j['error'])[:400])
    return j['result']
def batch(url, calls, **kw):
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]
    j = post(url, payload, **kw)
    if isinstance(j, dict): raise Exception('batch refused: ' + json.dumps(j)[:300])
    out = [None] * len(calls)
    for x in j:
        out[x['id']] = x['result'] if 'result' in x else {'error': x.get('error')}
    return out
def net(cid): return [n for n in NETS if n['chainId'] == cid][0]
def sel(sig): return keccak256(sig.encode()).hex()[:8]
def u256(x): return int(x).to_bytes(32, 'big').hex()
def adr(a): return a[2:].lower().rjust(64, '0')
def fetch_src(cid, addr):
    """Verified source from Sourcify into the scratch download directory. Returns (dir, name, nfiles) or None."""
    u = 'https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,compilation' % (cid, addr)
    r = requests.get(u, timeout=60, headers={'user-agent': 'curl/8'})
    if r.status_code != 200: return None
    j = r.json(); d = os.path.join(DL, '%d_%s' % (cid, addr.lower())); os.makedirs(d, exist_ok=True)
    for path, s in (j.get('sources') or {}).items():
        fn = os.path.join(d, path.replace('/', '__').replace('..', '_'))
        open(fn, 'w').write(s.get('content', ''))
    return d, (j.get('compilation') or {}).get('name'), len(j.get('sources') or {})
