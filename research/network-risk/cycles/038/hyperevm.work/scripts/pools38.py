"""List Initialize logs of the HyperEVM PoolManager on the archive replica, keep hookless pools, read their slot0 and liquidity
through extsload on the official endpoint. Output out/pools38.json. Read-only."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
I = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
ARCH = 'https://rpc.hyperlend.finance/archive'
OFF = 'https://rpc.hyperliquid.xyz/evm'
head = int(rpc(ARCH, 'eth_blockNumber', []), 16)
logs = []; b = head
while b > 38_000_000:
    logs += rpc(ARCH, 'eth_getLogs', [{'address': PM, 'topics': [I], 'fromBlock': hex(max(b - 99999, 0)), 'toBlock': hex(b)}], timeout=90)
    b -= 100000
pools = []
for x in logs:
    d = bytes.fromhex(x['data'][2:])
    fee = int.from_bytes(d[0:32], 'big'); ts = int.from_bytes(d[32:64], 'big', signed=True); hook = '0x' + d[76:96].hex()
    pools.append({'id': x['topics'][1], 'c0': '0x' + x['topics'][2][26:], 'c1': '0x' + x['topics'][3][26:], 'fee': fee, 'ts': ts, 'hooks': hook, 'block': int(x['blockNumber'], 16)})
hl = [p for p in pools if int(p['hooks'], 16) == 0]
for p in hl:
    base = int.from_bytes(keccak(bytes.fromhex(p['id'][2:]) + (6).to_bytes(32, 'big')), 'big')
    s0 = int(rpc(OFF, 'eth_getStorageAt', [PM, hex(base), 'latest']), 16)
    liq = int(rpc(OFF, 'eth_getStorageAt', [PM, hex(base + 3), 'latest']), 16)
    p['sqrtPriceX96'] = s0 & ((1 << 160) - 1); t = (s0 >> 160) & 0xffffff; p['tick'] = t - (1 << 24) if t >> 23 else t
    p['lpFee'] = (s0 >> 208) & 0xffffff; p['liquidity'] = liq
json.dump({'head': head, 'allPools': len(pools), 'hookless': hl}, open(sys.argv[1], 'w'), indent=1)
print('head', head, 'pools', len(pools), 'hookless', len(hl), 'with liquidity', sum(1 for p in hl if p['liquidity']))
