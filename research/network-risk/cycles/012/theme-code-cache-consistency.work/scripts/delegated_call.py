# Read-only check per network: owner() on the PoolManager directly, and owner()
# on an EOA whose code is overridden with the EIP-7702 designator 0xef0100||PM
# and whose slot 0 is overridden. The delegated call must run the PoolManager's
# code (its jumps judged against the PoolManager's bitmap) in the EOA's storage.
import json, sys, urllib.request
nets = json.load(open(sys.argv[1]))
nets = nets if isinstance(nets, list) else nets.get('networks', nets)
EOA = '0x00000000000000000000000000000000c0dec0de'
MARK = '0x000000000000000000000000' + '1234567890abcdef1234567890abcdef12345678'
def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, body, {"content-type": "application/json", "user-agent": "review-client"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except Exception as e:
        return {"error": str(e)}
out = []
for n in nets:
    pm = n['poolManager']; url = n['rpc']
    direct = rpc(url, 'eth_call', [{"to": pm, "data": "0x8da5cb5b"}, "latest"])
    ov = {EOA: {"code": "0xef0100" + pm[2:].lower(), "stateDiff": {"0x" + "00"*32: MARK}}}
    deleg = rpc(url, 'eth_call', [{"to": EOA, "data": "0x8da5cb5b"}, "latest", ov])
    ext = rpc(url, 'eth_call', [{"to": EOA, "data": "0x1e2eaeaf" + "00"*32}, "latest", ov])
    r = {"chainId": n['chainId'], "direct": direct.get('result', direct.get('error')),
         "expectedOwner": n.get('owner'),
         "delegatedOwner": deleg.get('result', deleg.get('error')),
         "delegatedExtsload0": ext.get('result', ext.get('error'))}
    r["delegatedOk"] = (str(r["delegatedOwner"]).lower() == MARK.lower() and str(r["delegatedExtsload0"]).lower() == MARK.lower())
    out.append(r); print(json.dumps(r), flush=True)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
