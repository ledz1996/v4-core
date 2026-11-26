"""Endpoint candidates per chain id for theme-state-replay (cycle 23). Public endpoints only, no API keys."""
import json
NR='/home/user/v4-core/research/network-risk'
NETS={n['chainId']:n for n in json.load(open(NR+'/state/networks.json'))['networks']}
CAND={
 1:['https://ethereum-rpc.publicnode.com','https://mainnet.gateway.tenderly.co','https://eth.drpc.org','https://eth.llamarpc.com','https://rpc.flashbots.net'],
 8453:['https://mainnet.base.org','https://base-rpc.publicnode.com','https://base.gateway.tenderly.co','https://base.drpc.org'],
 130:['https://mainnet.unichain.org','https://unichain-rpc.publicnode.com','https://unichain.drpc.org','https://unichain.gateway.tenderly.co'],
 42161:['https://arb1.arbitrum.io/rpc','https://arbitrum-one-rpc.publicnode.com','https://arbitrum.gateway.tenderly.co','https://arbitrum.drpc.org'],
 56:['https://bsc-dataseed1.bnbchain.org','https://bsc-rpc.publicnode.com','https://bsc.rpc.sentio.xyz','https://bsc.drpc.org','https://bsc.api.pocket.network'],
 137:['https://polygon-bor-rpc.publicnode.com','https://polygon.drpc.org','https://polygon.gateway.tenderly.co'],
 43114:['https://api.avax.network/ext/bc/C/rpc','https://avalanche-c-chain-rpc.publicnode.com','https://avalanche.drpc.org','https://avalanche.gateway.tenderly.co'],
 143:['https://rpc.monad.xyz','https://rpc1.monad.xyz','https://rpc3.monad.xyz','https://rpc-mainnet.monadinfra.com','https://monad.drpc.org'],
 4326:['https://mainnet.megaeth.com/rpc','https://megaeth.drpc.org'],
 999:['https://rpc.hyperliquid.xyz/evm','https://rpc.purroofgroup.com','https://hyperliquid.drpc.org','https://rpc.hyperlend.finance'],
}
