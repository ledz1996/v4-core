#!/bin/bash
cd /home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work
timeout 3000 python3 aa.py 8453 https://base-rpc.publicnode.com https://base.drpc.org 12000 20 raw/aa2_8453.json > raw/aa2_8453.txt 2>&1 &
timeout 3000 python3 aa.py 1 https://ethereum-rpc.publicnode.com https://eth.drpc.org 6000 50 raw/aa2_1.json > raw/aa2_1.txt 2>&1 &
timeout 3000 python3 aa.py 137 https://polygon-bor-rpc.publicnode.com https://polygon.drpc.org 6000 100 raw/aa2_137.json > raw/aa2_137.txt 2>&1 &
timeout 3000 python3 aa.py 42161 https://arb1.arbitrum.io/rpc https://arbitrum.drpc.org 6000 400 raw/aa2_42161.json > raw/aa2_42161.txt 2>&1 &
timeout 3000 python3 aa.py 10 https://mainnet.optimism.io https://optimism.drpc.org 6000 500 raw/aa2_10.json > raw/aa2_10.txt 2>&1 &
wait
