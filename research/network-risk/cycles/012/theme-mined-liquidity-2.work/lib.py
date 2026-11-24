import sys, json, time, itertools, threading
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc as _rpc, keccak
MOD = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
TRANSFER = '0x' + keccak(b'Transfer(address,address,uint256)').hex()
T6909 = '0x' + keccak(b'Transfer(address,address,address,uint256,uint256)').hex()
NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
LOG_URLS = {143: ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://rpc.monad.xyz'],
            4326: ['https://mainnet.megaeth.com/rpc'], 4217: ['https://rpc.mainnet.tempo.xyz'], 5042: ['https://rpc.mainnet.arc.io'],
            999: ['https://rpc.hypurrscan.io', 'https://rpc.hyperliquid.xyz/evm', 'https://rpc.hyperlend.finance']}
# endpoints that honour the block tag for state reads
STATE_URLS = {143: ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com'],
              4326: ['https://mainnet.megaeth.com/rpc'], 4217: ['https://rpc.mainnet.tempo.xyz'], 5042: ['https://rpc.mainnet.arc.io'],
              999: ['https://hyperliquid.drpc.org']}
LOG_URLS.update({137: ['https://polygon-bor-rpc.publicnode.com', 'https://polygon.gateway.tenderly.co'],
    56: ['https://bsc-rpc.publicnode.com', 'https://rpc-bsc.48.club'],
    4663: ['https://rpc.mainnet.chain.robinhood.com'], 99901: ['https://rpc.elysium.kinetiq.xyz'],
    43114: ['https://avalanche-c-chain-rpc.publicnode.com']})
STATE_URLS.update({137: ['https://polygon.drpc.org', 'https://polygon.gateway.tenderly.co'],
    56: ['https://bsc.rpc.sentio.xyz', 'https://bsc.api.pocket.network', 'https://bsc-mainnet.public.blastapi.io'],
    4663: ['https://robinhood.drpc.org'], 99901: ['https://rpc.elysium.kinetiq.xyz'],
    43114: ['https://api.avax.network/ext/bc/C/rpc']})
TRACE_URLS = {999: ['https://hyperliquid.drpc.org'], 137: ['https://polygon.drpc.org'], 4663: ['https://robinhood.drpc.org'],
    43114: ['https://avalanche.drpc.org'], 56: ['https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3'], 143: STATE_URLS[143], 4326: STATE_URLS[4326], 5042: STATE_URLS[5042]}
_lock = threading.Lock(); _rr = {}

def rpc(cid, method, params, urls=None, timeout=90, tries=10):
    urls = urls or LOG_URLS[cid]
    last = None
    for k in range(tries):
        with _lock:
            i = _rr.get(id(urls), 0); _rr[id(urls)] = i + 1
        url = urls[i % len(urls)]
        try:
            return _rpc(url, method, params, timeout=timeout)
        except Exception as e:  # noqa
            last = e; m = str(e)
            if any(k in m.lower() for k in ('too large', 'exceeds max', 'not supported', 'method not found', '401', 'does not exist', 'not available')): raise
            time.sleep(min(20, 1.5 * (k + 1)))
    raise last

def s256(x): return x - (1 << 256) if x >> 255 else x
