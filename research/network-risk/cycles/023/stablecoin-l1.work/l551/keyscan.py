"""L-551: scan the Tempo AccountKeychain precompile (0xAAAAAAAA00..00) over the whole chain for KeyAuthorized and
AdminKeyAuthorized logs whose indexed account is address zero, and count all such logs. Read-only eth_getLogs."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '021', 'theme-arc-running-code.work'))
from rpc import batch, call
U = 'https://rpc.mainnet.tempo.xyz'; KC = '0xAAAAAAAA00000000000000000000000000000000'
T = {'KeyAuthorized': '0x7c46af0758d3eca5e8195833bff1e5153f6249fc0f2968a878fd28544315a03c', 'AdminKeyAuthorized': '0x493bc0240c1da6c792754dc5247d39ed76c71c99a43e16777538687f8d05e88e'}
Z = '0x' + '0' * 64
head = int(call(U, 'eth_blockNumber', []), 16); STEP = 100000
out = {'head': head, 'client': call(U, 'web3_clientVersion', []), 'zeroAccount': {}, 'all': {}}
for name, t in T.items():
    zero = []; allc = 0
    ranges = [(a, min(a + STEP - 1, head)) for a in range(0, head + 1, STEP)]
    for i in range(0, len(ranges), 10):
        ch = ranges[i:i + 10]
        r = batch(U, [('eth_getLogs', [{'fromBlock': hex(a), 'toBlock': hex(b), 'address': KC, 'topics': [t]}]) for a, b in ch])
        for lg in r:
            allc += len(lg); zero += [l for l in lg if len(l['topics']) > 1 and l['topics'][1] == Z]
    out['zeroAccount'][name] = zero; out['all'][name] = allc
    print(name, 'all', allc, 'zero account', len(zero), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keyscan.json'), 'w'), indent=1)
