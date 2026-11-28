#!/bin/sh
# cycle 38: L-1335 and L-1329 pinned runs; each request is a batch [web3_clientVersion, eth_call x K, web3_clientVersion]
cd /home/user/v4-core/research/network-risk/cycles/038/arbitrum-family.work
S=scripts/pinrun.py
(for s in provevec ops pmdiff pmdiff2; do python3 -I $S https://arb1.arbitrum.io/rpc $s out/pin-arb1-$s.json --threads 2 > out/pin-arb1-$s.log 2>&1; done) &
(for s in provevec ops pmdiff pmdiff2; do python3 -I $S https://rpc.elysium.kinetiq.xyz $s out/pin-ely-$s.json --threads 2 > out/pin-ely-$s.log 2>&1; done) &
(for s in provevec ops; do python3 -I $S https://rpc.mainnet.chain.robinhood.com $s out/rounds-rh-$s.json --rounds 10 --threads 2 > out/rounds-rh-$s.log 2>&1; done) &
wait
