import json, sys, time, urllib.request
URL = 'https://rpc.monad.xyz'
def rpc(method, params, url=URL, timeout=60):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    last = None
    for k in range(6):
        try:
            req = urllib.request.Request(url, body, {'Content-Type': 'application/json', 'User-Agent': 'rpc-client'})
            j = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            if 'error' in j:
                last = j['error']
                if 'rate' in json.dumps(j['error']).lower() or j['error'].get('code') in (-32005, 429): time.sleep(2 + 2 * k); continue
                raise RuntimeError(json.dumps(j['error'])[:300])
            return j['result']
        except RuntimeError: raise
        except Exception as e:
            last = str(e); time.sleep(2 + 2 * k)
    raise RuntimeError(str(last)[:300])
