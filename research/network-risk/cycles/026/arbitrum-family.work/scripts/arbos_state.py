import sys, json, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
def sel(s): return '0x' + keccak(s.encode()).hex()[:8] if isinstance(keccak(s.encode()), bytes) else '0x%064x' % keccak(s.encode())
def rpc(u, m, p):
    r = urllib.request.Request(u, json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(), {'content-type':'application/json','user-agent':'curl/8.5.0'})
    return json.load(urllib.request.urlopen(r, timeout=40)).get('result')
CALLS = [('0x000000000000000000000000000000000000006b', s) for s in ['getScheduledUpgrade()', 'getNativeTokenManagementFrom()', 'getTransactionFilteringFrom()', 'getAllChainOwners()', 'getNetworkFeeAccount()', 'isCalldataPriceIncreaseEnabled()']] + [('0x0000000000000000000000000000000000000064', 'arbOSVersion()')]
for u in ['https://arb1.arbitrum.io/rpc', 'https://rpc.mainnet.chain.robinhood.com', 'https://rpc.elysium.kinetiq.xyz']:
    b = rpc(u, 'eth_getBlockByNumber', ['latest', False])
    print('==', u, 'block', int(b['number'], 16), 'ts', int(b['timestamp'], 16))
    for to, s in CALLS:
        h = keccak(s.encode()); h = h.hex() if isinstance(h, bytes) else '%064x' % h
        try: print(s, rpc(u, 'eth_call', [{'to': to, 'data': '0x' + h[:8]}, b['number']]))
        except Exception as e: print(s, 'ERR', e)
