# Shared helpers for the balance reconcile sweep. Read-only JSON-RPC only.
import json, os, sys, time, requests
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NETS = json.load(open(os.path.join(HERE, '..', '..', '..', 'state', 'networks.json')))
NETS = NETS['networks'] if isinstance(NETS, dict) and 'networks' in NETS else NETS
S = requests.Session()
S.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
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
    if 'error' in j: raise Exception(json.dumps(j['error'])[:300])
    return j['result']

def batch(url, calls, **kw):
    """calls: list of (method, params). Returns list of result or {'error':..}."""
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]
    j = post(url, payload, **kw)
    if isinstance(j, dict): raise Exception('batch refused: ' + json.dumps(j)[:300])
    out = [None] * len(calls)
    for x in j:
        out[x['id']] = x['result'] if 'result' in x else {'error': x.get('error')}
    return out

def pad_addr(a): return '0x' + a[2:].lower().rjust(64, '0')
def net(cid): return [n for n in NETS if n['chainId'] == cid][0]

def sel(sig):
    from keccak import keccak256
    return '0x' + keccak256(sig.encode()).hex()[:8]
def call(url, to, sig, args='', block='latest', frm=None):
    tx = {'to': to, 'data': sel(sig) + args}
    if frm: tx['from'] = frm
    return rpc(url, 'eth_call', [tx, block])
def u256(x): return int(x).to_bytes(32, 'big').hex()
def adr(a): return a[2:].lower().rjust(64, '0')

def jl(fn):
    """json.load that also accepts the gzip-compressed copy kept in raw/."""
    import gzip
    if os.path.exists(fn): return json.load(open(fn))
    return json.load(gzip.open(fn + '.gz', 'rt'))
