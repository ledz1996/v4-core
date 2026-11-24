"""PoolManager logs on Monad other than Swap/ModifyLiquidity: Donate, ERC-6909 Transfer, Approval, OperatorSet.
100-block windows (endpoint limit). Usage: python3 collect_pm.py <head> <windows> <out.jsonl>"""
import sys, json, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
TOP = {'0x' + keccak(s.encode()).hex(): s for s in ['Donate(bytes32,address,uint256,uint256)', 'Transfer(address,address,address,uint256,uint256)',
       'Approval(address,address,uint256,uint256)', 'OperatorSet(address,address,bool)']}
URLS = ['https://rpc3.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://rpc1.monad.xyz', 'https://rpc.monad.xyz']
def job(k):
    hi = HEAD - 100 * k; lo = hi - 99
    for a in range(8):
        try:
            return k, lo, hi, rpc(URLS[(k + a) % 4], 'eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [list(TOP)]}], timeout=60)
        except Exception:
            time.sleep(1 + a)
    return k, lo, hi, None
if __name__ == '__main__':
    HEAD = int(sys.argv[1]); N = int(sys.argv[2]); out = open(sys.argv[3], 'a')
    with cf.ThreadPoolExecutor(6) as ex:
        for k, lo, hi, r in ex.map(job, range(N)):
            out.write(json.dumps({'k': k, 'lo': lo, 'hi': hi, 'logs': None if r is None else [{'t': l['topics'], 'd': l['data'], 'b': int(l['blockNumber'], 16), 'h': l['transactionHash']} for l in r]}) + '\n'); out.flush()
            if k % 1000 == 0: print(k, lo, flush=True)
