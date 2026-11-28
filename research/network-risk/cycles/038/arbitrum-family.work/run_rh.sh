#!/bin/sh
# cycle 38 L-1329: Robinhood Chain routes each batch item to an amd64 or arm64 backend; every job is sent 10 times, one thread.
cd /home/user/v4-core/research/network-risk/cycles/038/arbitrum-family.work
python3 -I scripts/pinrun.py https://rpc.mainnet.chain.robinhood.com provevec out/rounds-rh-provevec.json --rounds 10 --threads 1 > out/rounds-rh-provevec.log 2>&1
python3 -I scripts/pinrun.py https://rpc.mainnet.chain.robinhood.com ops out/rounds-rh-ops.json --rounds 10 --threads 1 --size 1200 --per 2 > out/rounds-rh-ops.log 2>&1
