import json, urllib.request, time

NET = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
BY = {n['chainId']: n for n in NET}

def call(url, method, params, timeout=60, retries=2):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers={"content-type": "application/json", "user-agent": "rpc-client/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            last = {"transport_error": str(e)[:300]}
            time.sleep(1.5)
    return last
