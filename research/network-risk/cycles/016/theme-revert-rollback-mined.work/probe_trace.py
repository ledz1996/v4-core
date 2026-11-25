"""Read-only. For each candidate endpoint: latest block, one PoolManager log, and whether
debug_traceTransaction (callTracer) and prestateTracer answer for that transaction."""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
C = {4217: ['https://rpc.mainnet.tempo.xyz'], 5042: ['https://rpc.mainnet.arc.io', 'https://arc.drpc.org'],
     56: ['https://bsc-dataseed1.bnbchain.org', 'https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 'https://rpc-bsc.48.club'],
     43114: ['https://api.avax.network/ext/bc/C/rpc', 'https://avalanche-c-chain-rpc.publicnode.com', 'https://avalanche.drpc.org'],
     42161: ['https://arb1.arbitrum.io/rpc', 'https://arbitrum.drpc.org', 'https://arbitrum-one-rpc.publicnode.com'],
     4663: ['https://rpc.mainnet.chain.robinhood.com', 'https://robinhood.drpc.org'],
     99901: ['https://rpc.elysium.kinetiq.xyz'],
     10: ['https://mainnet.optimism.io', 'https://optimism.drpc.org', 'https://optimism-rpc.publicnode.com'],
     8453: ['https://mainnet.base.org/', 'https://base.drpc.org', 'https://base-rpc.publicnode.com', 'https://base.gateway.tenderly.co'],
     130: ['https://mainnet.unichain.org', 'https://unichain.drpc.org', 'https://unichain-rpc.publicnode.com'],
     42220: ['https://forno.celo.org', 'https://celo.drpc.org', 'https://celo-rpc.publicnode.com']}
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']} if isinstance(json.load(open('/home/user/v4-core/research/network-risk/state/networks.json')), dict) else {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))}
def go(cid):
    pm = nets[cid]['poolManager']; base = nets[cid]['rpc']; out = {'chain': cid}
    bn = int(rpc(base, 'eth_blockNumber', []), 16); out['block'] = bn
    logs = []
    for span in (200, 1000, 5000):
        try:
            logs = rpc(base, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(bn - span), 'toBlock': hex(bn)}]);
            if logs: break
        except Exception as e: out['logsErr'] = str(e)[:100]
    if not logs: return out
    h = logs[-1]['transactionHash']; out['tx'] = h; res = {}
    for u in C[cid]:
        r = {}
        for tr in ('callTracer', 'prestateTracer'):
            try: x = rpc(u, 'debug_traceTransaction', [h, {'tracer': tr}], timeout=40); r[tr] = 'ok'
            except Exception as e: r[tr] = str(e)[:90]
        res[u] = r
    out['endpoints'] = res; return out
with cf.ThreadPoolExecutor(11) as ex:
    R = list(ex.map(go, C))
json.dump(R, open('raw/probe_trace.json', 'w'), indent=1); print(json.dumps(R, indent=1))
