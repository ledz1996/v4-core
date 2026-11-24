import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
C = {137: ['https://polygon.drpc.org','https://polygon-bor-rpc.publicnode.com','https://polygon.gateway.tenderly.co'],
     56: ['https://bsc-dataseed1.bnbchain.org','https://bsc-rpc.publicnode.com','https://bsc.drpc.org','https://bsc-mainnet.public.blastapi.io','https://rpc-bsc.48.club'],
     4663: ['https://rpc.mainnet.chain.robinhood.com','https://robinhood.drpc.org'],
     99901: ['https://rpc.elysium.kinetiq.xyz'],
     43114: ['https://api.avax.network/ext/bc/C/rpc','https://avalanche-c-chain-rpc.publicnode.com','https://avalanche.drpc.org']}
PM = {n['chainId']: n['poolManager'] for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
for cid, urls in C.items():
    for u in urls:
        out = [cid, u]
        try:
            h = int(rpc(u, 'eth_blockNumber', [], timeout=20), 16); out.append(h)
        except Exception as e: print(cid, u, 'head fail', str(e)[:80]); continue
        for back in (1000, 100000, 1000000):
            try:
                r = rpc(u, 'eth_getStorageAt', [PM[cid], '0x0', hex(h - back)], timeout=20); out.append(('state-%d' % back, 'ok'))
            except Exception as e: out.append(('state-%d' % back, str(e)[:50]))
        for span in (1000, 10000):
            try:
                r = rpc(u, 'eth_getLogs', [{'address': PM[cid], 'fromBlock': hex(h - span), 'toBlock': hex(h)}], timeout=30); out.append(('logs%d' % span, len(r)))
            except Exception as e: out.append(('logs%d' % span, str(e)[:50]))
        try:
            b = rpc(u, 'eth_getBlockByNumber', [hex(h - 10), False], timeout=20)
            t = rpc(u, 'debug_traceTransaction', [b['transactions'][0], {'tracer': 'callTracer'}], timeout=30); out.append(('trace', 'ok'))
        except Exception as e: out.append(('trace', str(e)[:60]))
        print(out, flush=True)
