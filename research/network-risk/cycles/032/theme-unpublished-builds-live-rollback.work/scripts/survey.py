import sys, json
sys.path.insert(0, sys.argv[2]); from rpcu import rpc, version
C = {5042: ['https://rpc.mainnet.arc.io', 'https://arc.drpc.org', 'https://arc-rpc.publicnode.com', 'https://rpc.drpc.mainnet.arc.io', 'https://rpc.blockdaemon.mainnet.arc.io', 'https://rpc.quicknode.mainnet.arc.io'],
     99901: ['https://rpc.elysium.kinetiq.xyz', 'https://rpc-elysium-mainnet.t.conduit.xyz', 'https://elysium.drpc.org'],
     999: ['https://rpc.hyperliquid.xyz/evm', 'https://rpc.hyperlend.finance/archive', 'https://hyperliquid.drpc.org', 'https://rpc.hypurrscan.io', 'https://hyperliquid-json-rpc.stakely.io'],
     4326: ['https://mainnet.megaeth.com/rpc', 'https://rpc-megaeth-mainnet.globalstake.io', 'https://megaeth.drpc.org'],
     56: ['https://bsc-dataseed1.bnbchain.org', 'https://bsc-dataseed2.bnbchain.org', 'https://bsc-dataseed.bnbchain.org', 'https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://rpc-bsc.48.club']}
out = {}
for c, urls in C.items():
    for u in urls:
        v = version(u, c); v['chainId'] = rpc(u, 'eth_chainId', [], 30); v['block'] = rpc(u, 'eth_blockNumber', [], 30)
        out[u] = {'chain': c, **v}
        print(c, u, json.dumps(v['web3_clientVersion'])[:150], json.dumps(v.get('arc_getVersion', ''))[:250], v['chainId'].get('result'))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
