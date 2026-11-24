"""Collect mined logs on Monad in 100-block windows: v4 PoolManager Swap and ModifyLiquidity,
and Uniswap v3 style Swap, Mint and Burn of every emitter. Read-only eth_getLogs.
Usage: python3 collect.py <head> <windows> <out.jsonl>"""
import sys, json, time, threading, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
V4SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
V4MOD = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
V3SWAP = '0x' + keccak(b'Swap(address,address,int256,int256,uint160,uint128,int24)').hex()
V3MINT = '0x' + keccak(b'Mint(address,address,int24,int24,uint128,uint256,uint256)').hex()
V3BURN = '0x' + keccak(b'Burn(address,int24,int24,uint128,uint256,uint256)').hex()
URLS = ['https://rpc.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc3.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
lock = threading.Lock()
def job(k):
    hi = HEAD - 100 * k; lo = hi - 99
    for a in range(8):
        url = URLS[(k + a) % len(URLS)]
        try:
            r = rpc(url, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [[V4SWAP, V4MOD, V3SWAP, V3MINT, V3BURN]]}], timeout=60)
            return k, lo, hi, r
        except Exception as e:
            time.sleep(1 + a)
    return k, lo, hi, None
if __name__ == '__main__':
    HEAD = int(sys.argv[1]); N = int(sys.argv[2]); out = open(sys.argv[3], 'a')
    with cf.ThreadPoolExecutor(8) as ex:
        for k, lo, hi, r in ex.map(job, range(N)):
            slim = None if r is None else [{'a': l['address'], 't': l['topics'], 'd': l['data'], 'b': int(l['blockNumber'], 16), 'i': int(l['logIndex'], 16), 'h': l['transactionHash']} for l in r]
            out.write(json.dumps({'k': k, 'lo': lo, 'hi': hi, 'logs': slim}) + '\n'); out.flush()
            if k % 200 == 0: print(k, lo, len(slim or []), flush=True)
