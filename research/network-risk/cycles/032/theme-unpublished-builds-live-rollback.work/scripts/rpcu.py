"""Small JSON-RPC helper for this unit. Read-only methods only."""
import json, ssl, urllib.request, urllib.error, time
_ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(url, method, params, timeout=90):
    req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        return {'httpError': e.code, 'body': e.read()[:300].decode('latin1')}
    except Exception as e:
        return {'netError': str(e)[:200]}
    try: return json.loads(body)
    except Exception: return {'badBody': body[:300].decode('latin1')}
def version(url, chain):
    v = {'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'web3_clientVersion': rpc(url, 'web3_clientVersion', [], 30)}
    if chain == 5042: v['arc_getVersion'] = rpc(url, 'arc_getVersion', [], 30)
    return v
