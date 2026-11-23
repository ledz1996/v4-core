import sys, json, concurrent.futures as cf
from lib import *
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'; Z = '0x' + '0' * 64
C = {8453: ['https://base-rpc.publicnode.com','https://base.llamarpc.com','https://1rpc.io/base','https://base-mainnet.public.blastapi.io','https://base.meowrpc.com','https://developer-access-mainnet.base.org','https://base.lava.build','https://base-pokt.nodies.app','https://api.zan.top/base-mainnet','https://base.api.onfinality.io/public','https://rpc.therpc.io/base','https://base.rpc.subquery.network/public','https://gateway.tenderly.co/public/base','https://endpoints.omniatech.io/v1/base/mainnet/public','https://base.blockpi.network/v1/rpc/public','https://rpc.owlracle.info/base/70d38ce1826c4a60bb2a8e05a6c8b20f','https://base.gateway.tenderly.co'],
 480: ['https://worldchain-mainnet.gateway.tenderly.co','https://worldchain.gateway.tenderly.co','https://worldchain.drpc.org','https://480.rpc.thirdweb.com','https://worldchain-mainnet.g.alchemy.com/public','https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro','https://worldchain.rpc.subquery.network/public','https://rpc.worldchain.dev'],
 196: ['https://xlayer.drpc.org','https://rpc.xlayer.tech','https://xlayerrpc.okx.com','https://196.rpc.thirdweb.com','https://xlayer.rpc.blxrbdn.com','https://okx-xlayer.rpc.blxrbdn.com','https://rpc.ankr.com/xlayer','https://xlayer.gateway.tenderly.co','https://xlayer-rpc.publicnode.com'],
 56: ['https://bsc-rpc.publicnode.com','https://bsc.drpc.org','https://binance.llamarpc.com','https://56.rpc.thirdweb.com','https://public-bsc.nownodes.io','https://rpc-bsc.48.club','https://bsc.rpc.subquery.network/public','https://bnb.rpc.subquery.network/public','https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3'],
 143: ['https://monad.gateway.tenderly.co','https://monad-mainnet.gateway.tenderly.co','https://monad.drpc.org','https://143.rpc.thirdweb.com','https://rpc3.monad.xyz','https://rpc-mainnet.monadinfra.com','https://monad-rpc.publicnode.com'],
 7777777: ['https://zora.drpc.org','https://7777777.rpc.thirdweb.com','https://zora.gateway.tenderly.co'],
 1868: ['https://soneium.drpc.org','https://1868.rpc.thirdweb.com'],
}
def p(a):
    cid, u = a; pm = net(cid)['poolManager']; o = {'chainId': cid, 'url': u}
    try:
        head = int(rpc(u, 'eth_blockNumber', [], timeout=15, tries=1), 16); o['head'] = head
        for span in (2000000, 100000, 10000, 5000, 2000, 1000, 500, 100):
            try:
                r = rpc(u, 'eth_getLogs', [{'address': pm, 'topics': [T6909, Z], 'fromBlock': hex(head - span), 'toBlock': hex(head)}], timeout=40, tries=1)
                o['span'] = span; o['mints'] = len(r); break
            except Exception as e: o['e%d' % span] = str(e)[:100]
        try:
            r = rpc(u, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(head - 50), 'toBlock': hex(head)}], timeout=40, tries=1); o['anyLogs50'] = len(r)
        except Exception as e: o['anyErr'] = str(e)[:80]
    except Exception as e: o['err'] = str(e)[:100]
    return o
with cf.ThreadPoolExecutor(30) as ex: res = list(ex.map(p, [(c, u) for c in C for u in C[c]]))
json.dump(res, open('raw/probe_alt.json', 'w'), indent=1)
for o in res: print(o['chainId'], o['url'], o.get('head'), 'span', o.get('span'), 'mints', o.get('mints'), 'any50', o.get('anyLogs50'), o.get('err') or [v for k, v in o.items() if k[0] == 'e' and k != 'err'][:1])
