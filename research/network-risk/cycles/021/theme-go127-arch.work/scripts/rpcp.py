# Batched JSON-RPC helper for the pinned reruns: one HTTP request carries [web3_clientVersion, call, web3_clientVersion].
import json, urllib.request, urllib.error, ssl
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpcb(url, calls, timeout=120):
    body = [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=timeout, context=CTX).read())
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}', 'body': e.read()[:200].decode('latin1')}
    except Exception as e:
        return {'error': repr(e)[:200]}
    if isinstance(r, dict): return {'error': r}
    r = sorted(r, key=lambda x: x['id'])
    return [x.get('result', {'error': x.get('error')}) for x in r]
def arch(s):
    if not isinstance(s, str): return None
    for a in ('linux-arm64', 'linux-amd64'):
        if '/' + a + '/' in s: return a
    return None
