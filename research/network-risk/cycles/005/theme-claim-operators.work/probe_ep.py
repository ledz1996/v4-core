# Probe which endpoint serves address+topic filtered eth_getLogs over a wide block range.
import sys, json
from lib import *
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
C = {8453:['https://base.gateway.tenderly.co','https://base.drpc.org','https://mainnet.base.org','https://base-rpc.publicnode.com','https://8453.rpc.thirdweb.com','https://base.llamarpc.com','https://1rpc.io/base'],
 56:['https://bsc.gateway.tenderly.co','https://bsc.drpc.org','https://bsc-rpc.publicnode.com','https://56.rpc.thirdweb.com','https://rpc-bsc.48.club','https://bsc-mainnet.public.blastapi.io','https://binance.llamarpc.com','https://1rpc.io/bnb','https://bsc-dataseed1.bnbchain.org'],
 196:['https://xlayer.drpc.org','https://rpc.xlayer.tech','https://xlayerrpc.okx.com','https://196.rpc.thirdweb.com','https://xlayer.gateway.tenderly.co','https://1rpc.io/xlayer'],
 480:['https://worldchain.gateway.tenderly.co','https://worldchain.drpc.org','https://worldchain-mainnet.g.alchemy.com/public','https://480.rpc.thirdweb.com','https://worldchain-mainnet.gateway.tenderly.co']}
for cid, urls in C.items():
    pm = net(cid)['poolManager']
    for u in urls:
        try:
            head = int(rpc(u, 'eth_blockNumber', [], tries=1, timeout=15), 16)
        except Exception as e:
            print(cid, u, 'head ERR', str(e)[:100]); continue
        for span in (1000000, 100000, 10000, 1000):
            try:
                r = rpc(u, 'eth_getLogs', [{'address': pm, 'topics': [[OP, AP]], 'fromBlock': hex(head - span), 'toBlock': hex(head)}], tries=1, timeout=40)
                print(cid, u, 'span', span, 'OK', len(r)); break
            except Exception as e:
                print(cid, u, 'span', span, 'ERR', str(e)[:140])
