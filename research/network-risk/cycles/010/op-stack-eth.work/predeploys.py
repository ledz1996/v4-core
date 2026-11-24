"""Read the EIP-1967 implementation slot of predeploys 0x4200..0022 to 0x4200..0030 on the seven chains (eth_getStorageAt)."""
import json, urllib.request, ssl
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
R = {10: 'https://mainnet.optimism.io', 8453: 'https://mainnet.base.org/', 130: 'https://mainnet.unichain.org', 7777777: 'https://rpc.zora.energy/',
     480: 'https://worldchain-mainnet.g.alchemy.com/public', 57073: 'https://rpc-gel.inkonchain.com', 1868: 'https://rpc.soneium.org'}
SLOT = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
def rpc(u, m, p):
    q = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(q, timeout=30, context=ctx)).get('result')
for cid, u in R.items():
    bn = rpc(u, 'eth_blockNumber', [])
    nz = {}
    for k in range(0x22, 0x31):
        a = '0x42000000000000000000000000000000000000%02x' % k
        v = rpc(u, 'eth_getStorageAt', [a, SLOT, bn])
        if v and int(v, 16): nz[hex(k)] = '0x' + v[-40:]
    print(cid, int(bn, 16), nz)
