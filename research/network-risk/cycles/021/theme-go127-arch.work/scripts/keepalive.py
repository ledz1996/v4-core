# Sequential web3_clientVersion requests on one kept-alive TLS connection to the Robinhood endpoint: is routing sticky?
import http.client, ssl, json, time, os
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
port = int(os.environ['https_proxy'].rsplit(':', 1)[1])
rows = []
for k in range(4):
    c = http.client.HTTPSConnection('127.0.0.1', port, context=CTX, timeout=60); c.set_tunnel('rpc.mainnet.chain.robinhood.com', 443); seq = []
    for i in range(10):
        c.request('POST', '/', json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}), {'content-type': 'application/json'})
        seq.append(json.loads(c.getresponse().read())['result'])
    c.close(); rows.append(seq)
json.dump({'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'connections': rows}, open('../raw/keepalive-4663.json', 'w'), indent=0)
print([[('arm' if 'arm64' in s else 'amd') for s in r] for r in rows])
