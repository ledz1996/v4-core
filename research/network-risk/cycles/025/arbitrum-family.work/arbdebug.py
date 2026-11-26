# Read-only probe: does the ArbDebug precompile (0xff) answer on these chains, as it does only when AllowDebugPrecompiles is set?
import sys, json, urllib.request, urllib.error
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
def h(s):
    x = keccak(s.encode()); return x.hex() if isinstance(x, bytes) else '%064x' % x
def rpc(u, m, p):
    r = urllib.request.Request(u, json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(), {'content-type':'application/json','user-agent':'curl/8.5.0'})
    import time
    for i in range(8):
        try: return json.load(urllib.request.urlopen(r, timeout=40))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(5 * (i + 1))
FROM = '0x00000000000000000000000000000000c0ffee01'
for u in ['https://arb1.arbitrum.io/rpc', 'https://rpc.mainnet.chain.robinhood.com', 'https://rpc.elysium.kinetiq.xyz']:
    print('==', u)
    for s in ['becomeChainOwner()', 'legacyError()', 'customRevert(uint64)', 'panic()']:
        data = '0x' + h(s)[:8] + ('00' * 32 if 'uint64' in s else '')
        print(' ', s, json.dumps(rpc(u, 'eth_call', [{'from': FROM, 'to': '0x00000000000000000000000000000000000000ff', 'data': data}, 'latest']))[:300])
    print('  code at 0xff', rpc(u, 'eth_getCode', ['0x00000000000000000000000000000000000000ff', 'latest']).get('result'))
