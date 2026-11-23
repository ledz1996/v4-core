# Probe alternative public endpoints for archive depth and log range. Read-only.
import json, sys, concurrent.futures as cf
from lib import *
ALT = {
 1: ['https://ethereum-rpc.publicnode.com','https://eth.drpc.org','https://eth.llamarpc.com','https://1rpc.io/eth','https://eth.merkle.io','https://eth-mainnet.public.blastapi.io','https://mainnet.gateway.tenderly.co','https://rpc.flashbots.net'],
 10: ['https://mainnet.optimism.io','https://optimism.drpc.org','https://optimism-rpc.publicnode.com','https://optimism.gateway.tenderly.co','https://1rpc.io/op'],
 8453: ['https://mainnet.base.org/','https://base.drpc.org','https://base-rpc.publicnode.com','https://base.gateway.tenderly.co','https://base.llamarpc.com','https://1rpc.io/base'],
 130: ['https://mainnet.unichain.org','https://unichain.drpc.org','https://unichain-rpc.publicnode.com','https://unichain.gateway.tenderly.co'],
 7777777: ['https://rpc.zora.energy/'],
 480: ['https://worldchain-mainnet.g.alchemy.com/public','https://worldchain.drpc.org','https://worldchain-mainnet.gateway.tenderly.co'],
 57073: ['https://rpc-gel.inkonchain.com','https://rpc-qnd.inkonchain.com','https://ink.drpc.org'],
 1868: ['https://rpc.soneium.org','https://soneium.drpc.org'],
 42220: ['https://forno.celo.org','https://celo.drpc.org'],
 196: ['https://rpc.xlayer.tech','https://xlayerrpc.okx.com','https://xlayer.drpc.org'],
 42161: ['https://arb1.arbitrum.io/rpc','https://arbitrum.drpc.org','https://arbitrum-one-rpc.publicnode.com','https://arbitrum.gateway.tenderly.co','https://1rpc.io/arb'],
 4663: ['https://rpc.mainnet.chain.robinhood.com'],
 99901: ['https://rpc.elysium.kinetiq.xyz'],
 137: ['https://polygon.drpc.org','https://polygon-rpc.com','https://polygon-bor-rpc.publicnode.com','https://polygon.gateway.tenderly.co','https://1rpc.io/matic'],
 56: ['https://bsc-dataseed1.bnbchain.org','https://bsc.drpc.org','https://bsc-rpc.publicnode.com','https://binance.llamarpc.com','https://1rpc.io/bnb'],
 43114: ['https://api.avax.network/ext/bc/C/rpc','https://avalanche.drpc.org','https://avalanche-c-chain-rpc.publicnode.com','https://avalanche.gateway.tenderly.co','https://1rpc.io/avax/c'],
 143: ['https://rpc.monad.xyz','https://rpc1.monad.xyz','https://rpc3.monad.xyz','https://monad.drpc.org','https://monad-mainnet.gateway.tenderly.co'],
 4326: ['https://mainnet.megaeth.com/rpc'],
 4217: ['https://rpc.mainnet.tempo.xyz'],
 5042: ['https://rpc.mainnet.arc.io'],
 999: ['https://rpc.hyperliquid.xyz/evm','https://hyperliquid.drpc.org','https://rpc.hyperlend.finance','https://rpc.hypurrscan.io'],
}
def probe(a):
    cid, u = a; n = net(cid); pm = n['poolManager']; o = {'chainId': cid, 'url': u}
    try:
        if int(rpc(u, 'eth_chainId', [], tries=2, timeout=15), 16) != cid: o['err'] = 'wrong chain'; return o
        head = int(rpc(u, 'eth_blockNumber', [], tries=2), 16); o['head'] = head
        o['mc3'] = (len(rpc(u, 'eth_getCode', [MC3, 'latest'], tries=2)) - 2) // 2
        b = rpc(u, 'eth_getBlockByNumber', [hex(head), False], tries=2); t1 = int(b['timestamp'], 16)
        b0 = rpc(u, 'eth_getBlockByNumber', [hex(head - 5000), False], tries=2); t0 = int(b0['timestamp'], 16)
        bt = (t1 - t0) / 5000; day = int(86400 / max(bt, 0.01)); o['day'] = day
        o['state'] = 0
        for back in (day * 7, day, day // 4, day // 24, 1000, 120):
            try:
                rpc(u, 'eth_call', [{'to': pm, 'data': '0x8da5cb5b'}, hex(head - back)], tries=2); o['state'] = back; break
            except Exception as e: o['stateErr'] = str(e)[:60]
        o['logs'] = 0
        for span in (100000, 20000, 10000, 5000, 2000, 1000, 500, 100):
            try:
                r = rpc(u, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(head - span - 50), 'toBlock': hex(head - 50), 'topics': ['0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438']}], tries=2)
                o['logs'] = span; break
            except Exception as e: o['logErr'] = str(e)[:70]
        # topic-only Transfer filter (no address) over 20 blocks
        try:
            r = rpc(u, 'eth_getLogs', [{'fromBlock': hex(head - 70), 'toBlock': hex(head - 50), 'topics': [TRANSFER, None, pad_addr(pm)]}], tries=2); o['topicOnly'] = len(r)
        except Exception as e: o['topicOnlyErr'] = str(e)[:70]
        try:
            r = batch(u, [('eth_blockNumber', [])] * 30, tries=2); o['batch30'] = sum(1 for x in r if isinstance(x, str))
        except Exception as e: o['batchErr'] = str(e)[:60]
    except Exception as e:
        o['err'] = str(e)[:120]
    return o
jobs = [(c, u) for c, us in ALT.items() for u in us]
with cf.ThreadPoolExecutor(30) as ex: res = list(ex.map(probe, jobs))
json.dump(res, open('raw/endpoints_alt.json', 'w'), indent=1)
for r in res: print(json.dumps(r))
