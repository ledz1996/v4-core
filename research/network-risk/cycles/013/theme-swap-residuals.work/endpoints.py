"""Endpoints per chain id: which serve eth_getLogs and which serve historical state (extsload at old blocks).
Lists come from earlier cycles' tools (tools/opdiff/swaps.py, replay.py, cycles/012/theme-mined-liquidity-2.work/lib.py)."""
import json
NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
LOG = {8453: ['https://base.gateway.tenderly.co', 'https://base-rpc.publicnode.com'], 56: ['https://bsc.rpc.sentio.xyz'],
       999: ['https://rpc.hyperlend.finance', 'https://rpc.hypurrscan.io', 'https://rpc.hyperliquid.xyz/evm'],
       143: ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://rpc.monad.xyz'],
       137: ['https://polygon-bor-rpc.publicnode.com', 'https://polygon.gateway.tenderly.co'],
       43114: ['https://avalanche-c-chain-rpc.publicnode.com'], 1: ['https://ethereum-rpc.publicnode.com', 'https://mainnet.gateway.tenderly.co'],
       42161: ['https://arb1.arbitrum.io/rpc', 'https://arbitrum-one-rpc.publicnode.com']}
STATE = {1: ['https://mainnet.gateway.tenderly.co'], 8453: ['https://base.gateway.tenderly.co'], 56: ['https://bsc.rpc.sentio.xyz', 'https://bsc.api.pocket.network'],
         143: ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com'], 999: ['https://hyperliquid.drpc.org'],
         137: ['https://polygon.drpc.org', 'https://polygon.gateway.tenderly.co'], 4663: ['https://robinhood.drpc.org', 'https://rpc.mainnet.chain.robinhood.com'],
         43114: ['https://api.avax.network/ext/bc/C/rpc'], 42161: ['https://arb1.arbitrum.io/rpc', 'https://arbitrum.gateway.tenderly.co'],
         10: ['https://mainnet.optimism.io', 'https://optimism.gateway.tenderly.co']}
def log_urls(cid): return LOG.get(cid, [NETS[cid]['rpc']])
def state_urls(cid): return STATE.get(cid, [NETS[cid]['rpc']])
