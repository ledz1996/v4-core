import sys, json, time, threading, itertools
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc as _rpc, keccak
def topic(s): return '0x' + keccak(s.encode()).hex()
EV = {topic('Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)'): 'Initialize',
      topic('ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)'): 'ModifyLiquidity',
      topic('Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)'): 'Swap',
      topic('Donate(bytes32,address,uint256,uint256)'): 'Donate',
      topic('OperatorSet(address,address,bool)'): 'OperatorSet',
      topic('Approval(address,address,uint256,uint256)'): 'Approval',
      topic('Transfer(address,address,address,uint256,uint256)'): 'Transfer6909',
      topic('ProtocolFeeUpdated(bytes32,uint24)'): 'ProtocolFeeUpdated'}
NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
URLS = {143: ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://rpc.monad.xyz'],
        4326: ['https://mainnet.megaeth.com/rpc'],
        999: ['https://rpc.hyperliquid.xyz/evm', 'https://rpc.hypurrscan.io']}
TRACE = {143: ['https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com'],
         4326: ['https://mainnet.megaeth.com/rpc'], 999: ['https://hyperliquid.drpc.org', 'https://rpc.purroofgroup.com']}
STATE = {143: TRACE[143], 4326: TRACE[4326], 999: TRACE[999]}
# receipts: written by block production; on HyperEVM read from the official endpoint of the validator set
RECEIPT = {143: TRACE[143], 4326: TRACE[4326], 999: ['https://rpc.hyperliquid.xyz/evm']}
_c = itertools.count()
def rpc(urls, m, p, timeout=90, tries=8):
    last = None
    for k in range(tries):
        u = urls[next(_c) % len(urls)]
        try: return _rpc(u, m, p, timeout=timeout)
        except Exception as e:
            last = e; s = str(e).lower()
            if any(x in s for x in ('not supported', 'method not found', 'does not exist', 'execution reverted')): raise
            time.sleep(min(15, 1 + k * 1.5))
    raise last
def s256(x): return x - (1 << 256) if x >> 255 else x
