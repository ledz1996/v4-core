#!/bin/bash
cd /home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work
python3 scan.py 4217 https://rpc.mainnet.tempo.xyz https://rpc.mainnet.tempo.xyz 1500 raw/scan_4217.json 4 2000 > raw/log_4217.txt 2>&1 &
python3 scan.py 56 https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3 https://bsc-rpc.publicnode.com 1500 raw/scan_56.json 3 40 > raw/log_56.txt 2>&1 &
python3 scan.py 43114 https://avalanche.drpc.org https://avalanche-c-chain-rpc.publicnode.com 1500 raw/scan_43114.json 2 400 > raw/log_43114.txt 2>&1 &
python3 scan.py 42161 https://arbitrum.drpc.org https://arb1.arbitrum.io/rpc 1500 raw/scan_42161.json 2 400 > raw/log_42161.txt 2>&1 &
python3 scan.py 4663 https://robinhood.drpc.org https://rpc.mainnet.chain.robinhood.com 1500 raw/scan_4663.json 2 2000 > raw/log_4663.txt 2>&1 &
python3 scan.py 10 https://optimism.drpc.org https://mainnet.optimism.io 1500 raw/scan_10.json 2 500 > raw/log_10.txt 2>&1 &
python3 scan.py 8453 https://base.drpc.org https://base-rpc.publicnode.com 1500 raw/scan_8453.json 2 20 > raw/log_8453.txt 2>&1 &
python3 scan.py 130 https://unichain.drpc.org https://mainnet.unichain.org 1500 raw/scan_130.json 2 300 > raw/log_130.txt 2>&1 &
wait
