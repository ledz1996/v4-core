#!/bin/sh
# Task 1 and Task 4 batches. Each line: chain, trace endpoint, PoolManager, window, log step, block cap, threads, output, receipts endpoint.
cd /home/user/v4-core/research/network-risk/cycles/039/theme-transient-across-transactions-and-workers.work
S=scripts/syncpairs.py
python3 $S 4326 https://mainnet.megaeth.com/rpc 0xacb7e78fa05d562e0a5d3089ec896d57d057d38e 32200000 33045000 5000 3000 6 out/sp-4326.json > out/sp-4326.log 2>&1 &
python3 $S 143 https://rpc-mainnet.monadinfra.com 0x188d586ddcf52439676ca21a244753fa19f9ea8e 125800000 126058000 100 2000 4 out/sp-143.json https://rpc.monad.xyz > out/sp-143.log 2>&1 &
python3 $S 999 https://rpc.hyperlend.finance/archive 0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f 51000000 52444700 5000 2000 4 out/sp-999.json https://rpc.hyperliquid.xyz/evm > out/sp-999.log 2>&1 &
LOGS_URL=https://polygon-bor-rpc.publicnode.com python3 $S 137 https://polygon.drpc.org 0x67366782805870060151383f4bbff9dab53e5cd6 97900000 98090900 1000 1500 3 out/sp-137.json https://polygon-bor-rpc.publicnode.com > out/sp-137.log 2>&1 &
wait
