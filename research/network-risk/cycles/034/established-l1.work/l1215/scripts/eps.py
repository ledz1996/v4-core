"""Endpoint candidates per chain id for theme-replay-eleven (cycle 24). Public endpoints only, no API keys."""
import json
NR='/home/user/v4-core/research/network-risk'
NETS={n['chainId']:n for n in json.load(open(NR+'/state/networks.json'))['networks']}
CAND={
 10:['https://mainnet.optimism.io','https://optimism-rpc.publicnode.com','https://op.api.pocket.network','https://optimism.drpc.org','https://optimism.gateway.tenderly.co'],
 7777777:['https://rpc.zora.energy','https://zora.drpc.org','https://zora.api.pocket.network'],
 480:['https://worldchain-mainnet.g.alchemy.com/public','https://worldchain.drpc.org','https://480.rpc.thirdweb.com','https://worldchain.api.pocket.network'],
 57073:['https://rpc-gel.inkonchain.com','https://rpc-qnd.inkonchain.com','https://ink.drpc.org','https://ink.api.pocket.network'],
 1868:['https://rpc.soneium.org','https://soneium.drpc.org','https://soneium.api.pocket.network'],
 42220:['https://forno.celo.org','https://celo.drpc.org','https://celo-json-rpc.stakely.io','https://celo.api.pocket.network','https://rpc.ankr.com/celo'],
 196:['https://rpc.xlayer.tech','https://xlayerrpc.okx.com','https://xlayer.drpc.org'],
 4663:['https://rpc.mainnet.chain.robinhood.com'],
 99901:['https://rpc.elysium.kinetiq.xyz'],
 4217:['https://rpc.mainnet.tempo.xyz','https://tempo.drpc.org'],
 5042:['https://rpc.mainnet.arc.io','https://arc.drpc.org'],
 56:['https://bsc-dataseed1.bnbchain.org','https://bsc-rpc.publicnode.com','https://bsc.api.pocket.network','https://bsc.drpc.org','https://bsc-mainnet.public.blastapi.io'],
}
