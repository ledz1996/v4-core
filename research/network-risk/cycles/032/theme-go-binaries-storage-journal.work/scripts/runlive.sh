#!/bin/sh
# cycle 32: the cycle 31 Nitro live probe (copied unchanged as live.py) on one public endpoint per chain
S=/home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work
cd $S
python3 -I scripts/live.py out/live-56.json https://bsc-dataseed1.bnbchain.org 0x28e2ea090877bf75740558f6bfb36a5ffee9e9df > out/live-56.log 2>&1
python3 -I scripts/live.py out/live-137.json https://polygon-bor-rpc.publicnode.com 0x67366782805870060151383f4bbff9dab53e5cd6 > out/live-137.log 2>&1
python3 -I scripts/live.py out/live-43114.json https://api.avax.network/ext/bc/C/rpc 0x06380c0e0912312b5150364b9dc4542ba0dbbc85 > out/live-43114.log 2>&1
python3 -I scripts/live.py out/live-42161.json https://arb1.arbitrum.io/rpc 0x360e68faccca8ca495c1b759fd9eee466db9fb32 > out/live-42161.log 2>&1
python3 -I scripts/live.py out/live-4663.json https://rpc.mainnet.chain.robinhood.com 0x8366a39cc670b4001a1121b8f6a443a643e40951 > out/live-4663.log 2>&1
