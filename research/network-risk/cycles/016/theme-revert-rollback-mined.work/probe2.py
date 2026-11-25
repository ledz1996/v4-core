import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
C = {56: ['https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 'https://rpc-bsc.48.club'],
     43114: ['https://avalanche-c-chain-rpc.publicnode.com', 'https://avalanche.drpc.org', 'https://api.avax.network/ext/bc/C/rpc'],
     8453: ['https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://base.gateway.tenderly.co', 'https://mainnet.base.org/'],
     42220: ['https://celo-rpc.publicnode.com', 'https://celo.drpc.org', 'https://forno.celo.org'],
     5042: ['https://rpc.mainnet.arc.io'], 99901: ['https://rpc.elysium.kinetiq.xyz']}
out = {}
for cid, us in C.items():
    pm = nets[cid]['poolManager']; h = None
    for u in us:
        try:
            bn = int(rpc(u, 'eth_blockNumber', []), 16)
            lg = rpc(u, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(bn - 40), 'toBlock': hex(bn)}])
            if lg: h = lg[-1]['transactionHash']; print(cid, 'logs via', u, len(lg)); break
        except Exception as e: print(cid, u, 'logs', str(e)[:80])
    r = {}
    for u in us:
        for tr in ('callTracer', 'prestateTracer'):
            try: rpc(u, 'debug_traceTransaction', [h, {'tracer': tr}], timeout=40); r[u + ' ' + tr] = 'ok'
            except Exception as e: r[u + ' ' + tr] = str(e)[:80]
        for m, p in (('debug_traceCall', [{'to': pm, 'data': '0x'}, 'latest', {'tracer': 'callTracer'}]), ('eth_simulateV1', [{'blockStateCalls': [{'calls': [{'to': pm, 'data': '0x'}]}]}, 'latest'])):
            try: rpc(u, m, p, timeout=30); r[u + ' ' + m] = 'ok'
            except Exception as e: r[u + ' ' + m] = str(e)[:80]
    out[cid] = {'tx': h, 'r': r}
json.dump(out, open('raw/probe2.json', 'w'), indent=1); print(json.dumps(out, indent=1))
