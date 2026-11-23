# Lists every ERC-6909 Transfer log of the PoolManager whose "from" topic is the zero address (claim mints).
# Event: Transfer(address caller, address indexed from, address indexed to, uint256 indexed id, uint256 amount)
# (src/interfaces/external/IERC6909Claims.sol:14, emitted by _mint at src/ERC6909.sol:79-83).
# Read-only: eth_getLogs, eth_blockNumber, eth_getBlockByNumber.
# usage: python3 scan_mints.py <chainId> [fromBlock] [toBlock]
import sys, json, gzip, os, threading
from lib import *
from fetch import getlogs_range
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
Z = '0x' + '0' * 64
# endpoint, chunk (blocks per request before adaptive split), workers, known first block (None: search by timestamp 2025-01-01)
SCAN = {
 1:       ('https://mainnet.gateway.tenderly.co', 40000, 3, 21688329),
 10:      ('https://optimism.gateway.tenderly.co', 200000, 3, None),
 8453:    ('https://base.gateway.tenderly.co', 1000, 4, None),
 130:     ('https://unichain.gateway.tenderly.co', 400000, 3, 0),
 7777777: ('https://rpc.zora.energy/', 2000000, 2, 25434534),
 480:     ('https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 10000, 4, None),
 57073:   ('https://ink.gateway.tenderly.co', 500000, 3, 4580556),
 1868:    ('https://soneium.gateway.tenderly.co', 2000000, 2, 2473300),
 42220:   ('https://celo.gateway.tenderly.co', 2000000, 2, None),
 196:     ('https://rpc.xlayer.tech', 100, 4, None),
 42161:   ('https://arbitrum.gateway.tenderly.co', 2000000, 3, None),
 4663:    ('https://rpc.mainnet.chain.robinhood.com', 100000, 3, 0),
 99901:   ('https://rpc.elysium.kinetiq.xyz', 100000, 3, 256083),
 137:     ('https://polygon.gateway.tenderly.co', 2000000, 3, 66980384),
 56:      ('https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 50000, 4, None),
 43114:   ('https://avalanche.gateway.tenderly.co', 2000000, 3, 56195376),
 143:     ('https://rpc2.monad.xyz', 10000, 4, 29255895),
 4326:    ('https://mainnet.megaeth.com/rpc', 2000000, 2, 7009653),
 4217:    ('https://rpc.mainnet.tempo.xyz', 100000, 3, 6455926),
 5042:    ('https://arc.gateway.tenderly.co', 2000000, 3, 1948056),
 999:     ('https://rpc.purroofgroup.com', 100000, 3, None),
}
def block_at(url, ts, head):
    lo, hi = 0, head
    def t(b):
        r = rpc(url, 'eth_getBlockByNumber', [hex(b), False])
        return int(r['timestamp'], 16) if r else 0  # endpoints without pre-migration blocks answer null; treat as old
    if t(1) >= ts: return 0
    while lo + 1 < hi:
        m = (lo + hi) // 2
        if t(m) < ts: lo = m
        else: hi = m
    return hi
def main():
    cid = int(sys.argv[1]); url, chunk, workers, first = SCAN[cid]; n = net(cid); pm = n['poolManager']
    if len(sys.argv) > 4: url = sys.argv[4]
    head = int(rpc(url, 'eth_blockNumber', []), 16)
    lo = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != '-' else (first if first is not None else block_at(url, 1735689600, head))
    hi = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != '-' else head
    tag = '%d_%d_%d' % (cid, lo, hi)
    fn = 'raw/mints_%s.jsonl.gz' % tag
    out = gzip.open(fn, 'wt'); lock = threading.Lock(); cnt = [0]
    def on(logs):
        for l in logs:
            if l.get('removed'): continue
            t = l['topics']
            if len(t) != 4 or t[0] != T6909 or t[1] != Z: continue
            d = l['data'][2:]
            row = [int(l['blockNumber'], 16), l['transactionHash'], int(l['logIndex'], 16), '0x' + d[24:64], '0x' + t[2][-40:], t[3], str(int(d[64:128], 16))]
            out.write(json.dumps(row) + '\n'); cnt[0] += 1
    st = getlogs_range(url, {'address': pm, 'topics': [T6909, Z]}, lo, hi, chunk, workers=workers, on_logs=on, label='mints %d' % cid)
    out.close()
    meta = dict(chainId=cid, url=url, poolManager=pm, fromBlock=lo, toBlock=hi, mints=cnt[0], requests=st['req'], failed=st['fail'][:50], nFailed=len(st['fail']))
    json.dump(meta, open('raw/mints_%s.meta.json' % tag, 'w'), indent=1)
    print(json.dumps(meta)[:600])
if __name__ == "__main__": main()
